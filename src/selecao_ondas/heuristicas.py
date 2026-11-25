"""Heurísticas construtivas para o modelo monoobjetivo (razão unidades/corredores).

    B0  Crescimento por oferta      (sem rede: abre corredores em ordem de oferta total)
    H1  Descascamento de corredores (Charikar adaptado ao grafo pedido--corredor G_OA)
    H2  Comunidades de pedidos      (Leiden em G_O com afinidade por corredores + reparo)
    H3  Crescimento guiado por G_A  (abre o corredor mais conectado ao conjunto atual)
    H4  Comunidades de corredores   (Leiden em G_A + descascamento dentro de cada comunidade)

Todas usam o mesmo seletor de pedidos e o mesmo decodificador de corredores,
para que as diferenças venham apenas da informação de rede usada.
"""
from __future__ import annotations

import time
from dataclasses import dataclass

import numpy as np
import scipy.sparse as sp

from grafos import (
    afinidade_corredores,
    detectar_comunidades,
    grafo_pedido_corredor,
    para_igraph,
    projecao_corredores,
)
from instancia import Instancia, avaliar


@dataclass
class Solucao:
    pedidos: list[int]
    corredores: list[int]
    unidades: int
    razao: float
    metodo: str = ""
    tempo: float = 0.0


class Nucleo:
    """Seletor de pedidos e decodificador compartilhados por todas as heurísticas."""

    def __init__(self, inst: Instancia):
        self.inst = inst
        self.D = inst.D.tocsr()
        self.S = inst.S.tocsr()
        self.u = inst.unidades_pedido.astype(np.int64)
        self.Db = (self.D > 0).astype(np.int32).tocsr()
        self.ip, self.ix, self.qx = self.D.indptr, self.D.indices, self.D.data
        self.lb, self.ub = inst.lb, inst.ub
        # pedidos com u_o > UB nunca entram (pré-processamento)
        self.validos = self.u <= self.ub

    # ------------------------------------------------------------ seleção
    def selecionar(self, corredores, ordem: np.ndarray | None = None,
                   pedidos_permitidos: np.ndarray | None = None) -> tuple[list[int], int]:
        """Dado um conjunto de corredores, escolhe gulosamente os pedidos totalmente
        atendíveis pela oferta deles, em ordem decrescente de unidades, até UB."""
        if len(corredores) == 0:
            return [], 0
        oferta = np.asarray(self.S[corredores].sum(axis=0)).ravel()
        falta = self.Db @ (oferta == 0).astype(np.int32)
        mask = (falta == 0) & self.validos
        if pedidos_permitidos is not None:
            mask &= pedidos_permitidos
        cand = np.flatnonzero(mask)
        if ordem is None:
            cand = cand[np.argsort(-self.u[cand], kind="stable")]
        else:
            cand = cand[np.argsort(-ordem[cand], kind="stable")]
        rest = oferta.astype(np.int64)
        escolhidos, U = [], 0
        ip, ix, qx, u, ub = self.ip, self.ix, self.qx, self.u, self.ub
        for o in cand:
            if U + u[o] > ub:
                continue
            a, b = ip[o], ip[o + 1]
            idx, q = ix[a:b], qx[a:b]
            if np.all(rest[idx] >= q):
                rest[idx] -= q
                escolhidos.append(int(o))
                U += int(u[o])
                if U == ub:
                    break
        return escolhidos, U

    # ------------------------------------------------------------ decodificador
    def decodificar(self, pedidos, permitidos=None) -> list[int] | None:
        """Algoritmo 1: cobertura gulosa da demanda + remoção de corredores redundantes."""
        if not pedidos:
            return None
        R = np.asarray(self.D[pedidos].sum(axis=0)).ravel().astype(np.int64)
        S = self.S if permitidos is None else self.S[permitidos]
        ids = np.arange(self.inst.n_corredores) if permitidos is None else np.asarray(permitidos)
        S = S.tocsr()
        aberto = np.zeros(S.shape[0], dtype=bool)
        escolhidos = []
        while R.any():
            dados = np.minimum(S.data, R[S.indices])
            ganho = np.add.reduceat(dados, S.indptr[:-1]) if len(dados) else np.zeros(S.shape[0])
            ganho[np.diff(S.indptr) == 0] = 0
            ganho[aberto] = -1
            j = int(np.argmax(ganho))
            if ganho[j] <= 0:
                return None
            aberto[j] = True
            escolhidos.append(j)
            linha = S.getrow(j)
            R[linha.indices] = np.maximum(0, R[linha.indices] - linha.data)
        # remoção de redundantes (menor contribuição primeiro)
        demanda = np.asarray(self.D[pedidos].sum(axis=0)).ravel()
        oferta = np.asarray(S[escolhidos].sum(axis=0)).ravel()
        contrib = [np.minimum(S.getrow(j).data, demanda[S.getrow(j).indices]).sum() for j in escolhidos]
        for j in [escolhidos[t] for t in np.argsort(contrib)]:
            linha = S.getrow(j)
            if np.all(oferta[linha.indices] - linha.data >= demanda[linha.indices]):
                oferta[linha.indices] -= linha.data
                escolhidos.remove(j)
        return [int(ids[j]) for j in escolhidos]

    # ------------------------------------------------------------ avaliação
    def fechar(self, corredores, metodo: str, t0: float, rodadas: int = 2) -> Solucao | None:
        """Seleciona pedidos nos corredores dados e enxuga os corredores (iterado)."""
        melhor = None
        cor = list(corredores)
        for _ in range(rodadas):
            ped, U = self.selecionar(cor)
            if U < self.lb or not ped:
                break
            novo = self.decodificar(ped, permitidos=cor)
            if novo is None:
                break
            s = Solucao(ped, novo, U, U / len(novo), metodo)
            if melhor is None or s.razao > melhor.razao:
                melhor = s
            if set(novo) == set(cor):
                break
            cor = novo
        if melhor:
            melhor.tempo = time.time() - t0
        return melhor


def _melhor(a: Solucao | None, b: Solucao | None) -> Solucao | None:
    if a is None:
        return b
    if b is None:
        return a
    return b if b.razao > a.razao else a


# ================================================================ B0
def crescimento_por_oferta(n: Nucleo, kmax: int | None = None, paciencia: int = 15) -> Solucao | None:
    t0 = time.time()
    kmax = kmax or n.inst.n_corredores
    oferta_total = np.asarray(n.S.sum(axis=1)).ravel()
    ordem = list(np.argsort(-oferta_total))
    return _crescer(n, ordem[:1], lambda atual, cand: oferta_total[cand], ordem, "B0", t0, kmax, paciencia)


# ================================================================ H3
def crescimento_guiado(n: Nucleo, G_A: sp.csr_matrix, sementes: int = 5, kmax: int | None = None,
                       paciencia: int = 15, metrica: str = "forca_local") -> Solucao | None:
    """Cresce ondas priorizando a conectividade local ou uma centralidade de corredor.

    ``forca_local`` reproduz H3: soma dos pesos das arestas para corredores
    selecionados. ``grau_local`` conta essas conexoes sem usar seus pesos.
    As demais opcoes usam uma centralidade global para ordenar candidatos.
    """
    t0 = time.time()
    kmax = kmax or n.inst.n_corredores
    metricas_estaticas = {"grau", "forca", "pagerank", "k_core"}
    if metrica != "forca_local" and metrica != "grau_local" and metrica not in metricas_estaticas:
        raise ValueError(f"métrica desconhecida: {metrica}")
    # sementes: corredores com melhor razão sozinhos
    razoes = np.zeros(n.inst.n_corredores)
    for a in range(n.inst.n_corredores):
        _, U = n.selecionar([a])
        razoes[a] = U
    melhor = None
    G = G_A.tocsr()
    conexoes = G if metrica == "forca_local" else G.copy()
    if metrica == "grau_local":
        conexoes.data[:] = 1.0
    centralidade = None
    if metrica in metricas_estaticas:
        g = para_igraph(G)
        if metrica == "grau":
            centralidade = np.asarray(g.degree(), dtype=float)
        elif metrica == "forca":
            centralidade = np.asarray(g.strength(weights="weight"), dtype=float)
        elif metrica == "pagerank":
            centralidade = np.asarray(g.pagerank(weights="weight", directed=False), dtype=float)
        else:
            centralidade = np.asarray(g.coreness(), dtype=float)

    for s in np.argsort(-razoes)[:sementes]:
        conexao = np.zeros(n.inst.n_corredores)

        def escore(atual, cand, conexao=conexao, centralidade=centralidade):
            return centralidade[cand] if centralidade is not None else conexao[cand]

        def atualizar(a, conexao=conexao):
            linha = conexoes.getrow(a)
            conexao[linha.indices] += linha.data

        sol = _crescer(n, [int(s)], escore, list(range(n.inst.n_corredores)),
                       f"H3-{metrica.upper()}", t0, kmax, paciencia,
                       ao_abrir=atualizar)
        melhor = _melhor(melhor, sol)
    if melhor:
        melhor.tempo = time.time() - t0
    return melhor


def _crescer(n: Nucleo, iniciais, escore, universo, metodo, t0, kmax, paciencia, ao_abrir=None,
             frac: float = 0.05, limiar: int = 60):
    """Abre corredores um a um até `limiar`; acima disso, abre a fração `frac` por passo
    (simétrico ao descascamento). Cada corredor aberto atualiza o escore via `ao_abrir`."""
    atual = []
    fechado = np.ones(n.inst.n_corredores, dtype=bool)
    universo = np.asarray(universo)
    melhor, sem_melhora = None, 0
    proximos = list(iniciais)
    while len(atual) < kmax:
        passo = 1 if len(atual) < limiar else max(1, int(frac * len(atual)))
        for _ in range(passo):
            if proximos:
                a = proximos.pop(0)
            else:
                cand = universo[fechado[universo]]
                if len(cand) == 0:
                    break
                a = int(cand[np.argmax(escore(atual, cand))])
            atual.append(a)
            fechado[a] = False
            if ao_abrir:
                ao_abrir(a)
        if not fechado[universo].any() and len(atual) >= len(universo):
            ped, U = n.selecionar(atual)
            if U >= n.lb:
                melhor = _melhor(melhor, n.fechar(atual, metodo, t0, rodadas=1))
            break
        ped, U = n.selecionar(atual)
        if U >= n.lb:
            sol = n.fechar(atual, metodo, t0, rodadas=1)
            if sol and (melhor is None or sol.razao > melhor.razao):
                melhor, sem_melhora = sol, 0
            else:
                sem_melhora += 1
            if U == n.ub and sem_melhora >= paciencia:
                break
    return melhor


# ================================================================ H1
def descascamento(n: Nucleo, inicio=None, metodo: str = "H1", frac: float = 0.05,
                  limiar: int = 60, pedidos_permitidos: np.ndarray | None = None) -> Solucao | None:
    """Algoritmo 3: remove o corredor de menor contribuição e guarda a melhor razão.
    Para acelerar, remove a fração `frac` de menor contribuição enquanto |A'| > limiar.
    Com `pedidos_permitidos`, a seleção durante o descascamento fica restrita a esses
    pedidos (S_0); a onda final é completada com qualquer pedido atendível."""
    t0 = time.time()
    atual = np.asarray(inicio if inicio is not None else np.flatnonzero(np.diff(n.S.indptr) > 0))
    melhor = None
    while len(atual) > 0:
        ped, U = n.selecionar(list(atual), pedidos_permitidos=pedidos_permitidos)
        if U < n.lb:
            break
        sol = n.fechar(list(atual), metodo, t0, rodadas=1)
        melhor = _melhor(melhor, sol)
        demanda = np.asarray(n.D[ped].sum(axis=0)).ravel()
        Ssub = n.S[atual].tocsr()
        dados = np.minimum(Ssub.data, demanda[Ssub.indices])
        contrib = np.add.reduceat(dados, Ssub.indptr[:-1]) if len(dados) else np.zeros(len(atual))
        contrib[np.diff(Ssub.indptr) == 0] = 0
        r = max(1, int(frac * len(atual))) if len(atual) > limiar else 1
        atual = np.delete(atual, np.argsort(contrib, kind="stable")[:r])
    if melhor:
        melhor.tempo = time.time() - t0
    return melhor


# ================================================================ H4
def comunidades_corredores(n: Nucleo, G_A: sp.csr_matrix, resolucoes=(0.5, 1.0, 2.0, 4.0),
                           semente: int = 0, algoritmo: str = "leiden") -> Solucao | None:
    t0 = time.time()
    g = para_igraph(G_A)
    melhor = None
    vistos = set()
    resolucoes_uso = resolucoes if algoritmo.lower() == "leiden" else (1.0,)
    for gamma in resolucoes_uso:
        part = detectar_comunidades(g, algoritmo=algoritmo, resolucao=gamma, semente=semente)
        for com in part:
            chave = frozenset(com)
            if chave in vistos:
                continue
            vistos.add(chave)
            melhor = _melhor(
                melhor,
                descascamento(n, inicio=sorted(com), metodo=f"H4-{algoritmo.upper()}"),
            )
    if melhor:
        melhor.tempo = time.time() - t0
    return melhor


# ================================================================ H2
def comunidades_pedidos(n: Nucleo, G_O: sp.csr_matrix, resolucoes=(0.5, 1.0, 2.0, 5.0),
                        semente: int = 0, algoritmo: str = "leiden") -> Solucao | None:
    t0 = time.time()
    g = para_igraph(G_O)
    G = G_O.tocsr()
    melhor = None
    resolucoes_uso = resolucoes if algoritmo.lower() == "leiden" else (1.0,)
    for gamma in resolucoes_uso:
        part = detectar_comunidades(g, algoritmo=algoritmo, resolucao=gamma, semente=semente)
        for com in part:
            membros = np.array([o for o in com if n.validos[o]])
            if len(membros) == 0 or n.u[membros].sum() < n.lb:
                continue
            permitidos = np.zeros(n.inst.n_pedidos, dtype=bool)
            permitidos[membros] = True
            # corredores adjacentes à comunidade em G_OA
            oferta_util = (n.Db[membros].sum(axis=0).A1 > 0).astype(np.int32)
            adj = np.flatnonzero((n.S > 0).astype(np.int32) @ oferta_util > 0)
            sol = descascamento(
                n,
                inicio=adj,
                metodo=f"H2-{algoritmo.upper()}",
                pedidos_permitidos=permitidos,
            )
            melhor = _melhor(melhor, sol)
    if melhor:
        melhor.tempo = time.time() - t0
    return melhor


def _reparar(n: Nucleo, G: sp.csr_matrix, membros: np.ndarray):
    """Função Reparar do Algoritmo 2 (ordens estáticas, para eficiência)."""
    sel = np.zeros(G.shape[0], dtype=bool)
    sel[membros] = True
    forca_int = np.asarray(G[membros][:, membros].sum(axis=1)).ravel()
    U = int(n.u[membros].sum())
    if U > n.ub:
        ordem = membros[np.argsort(forca_int)]
        for o in ordem:
            if U <= n.ub:
                break
            sel[o] = False
            U -= int(n.u[o])
    if U < n.lb:
        conexao = np.asarray(G[:, np.flatnonzero(sel)].sum(axis=1)).ravel()
        fronteira = np.flatnonzero((conexao > 0) & ~sel & n.validos)
        for o in fronteira[np.argsort(-conexao[fronteira])]:
            if U >= n.lb:
                break
            if U + n.u[o] <= n.ub:
                sel[o] = True
                U += int(n.u[o])
    if U < n.lb or U > n.ub:
        return None
    return np.flatnonzero(sel)


# ================================================================ execução
def executar_todas(inst: Instancia, k: int = 10) -> list[Solucao]:
    n = Nucleo(inst)
    W = grafo_pedido_corredor(inst)
    t = time.time()
    G_A = projecao_corredores(W)
    t_GA = time.time() - t
    t = time.time()
    G_O = afinidade_corredores(inst, k, W)
    t_GO = time.time() - t
    saida = []
    for nome, f, extra in [
        ("B0", lambda: crescimento_por_oferta(n), 0.0),
        ("H1", lambda: descascamento(n), 0.0),
        ("H2", lambda: comunidades_pedidos(n, G_O), t_GO),
        ("H2-LOUVAIN", lambda: comunidades_pedidos(n, G_O, algoritmo="louvain"), t_GO),
        ("H3", lambda: crescimento_guiado(n, G_A), t_GA),
        ("H4", lambda: comunidades_corredores(n, G_A), t_GA),
        ("H4-LOUVAIN", lambda: comunidades_corredores(n, G_A, algoritmo="louvain"), t_GA),
    ]:
        s = f()
        if s is not None:
            ok, obj, _ = avaliar(inst, s.pedidos, s.corredores)
            assert ok and abs(obj - s.razao) < 1e-9, f"{nome}: solução inválida"
            s.metodo, s.tempo = nome, s.tempo + extra
        saida.append(s if s is not None else Solucao([], [], 0, 0.0, nome, 0.0))
    return saida
