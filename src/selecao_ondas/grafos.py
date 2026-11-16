"""Gerador de grafos de demanda e métricas de redes (Etapa 1 do TCC).

Grafos (notação da Seção 4.3 do texto):
    G_OI  pedido--item       (bipartido; matriz D, peso u_oi)
    G_IA  item--corredor     (bipartido; matriz S^T, peso u_ai)
    G_OA  pedido--corredor   (bipartido; peso w_oa = sum_i min(u_oi, u_ai))
    G_O   pedido--pedido     (projeção esparsificada por k vizinhos)
    G_A   corredor--corredor (projeção de G_OA sobre os corredores)

Uso como script:
    python grafos.py <instancia.txt> [--afinidade itens|corredores|combinada] [--k 10] [--salvar pasta]
"""
from __future__ import annotations

import argparse
from pathlib import Path

import igraph as ig
import leidenalg as la
import numpy as np
import scipy.sparse as sp

from instancia import Instancia, ler_instancia


# ---------------------------------------------------------------- bipartidos
def grafo_pedido_corredor(inst: Instancia) -> sp.csr_matrix:
    """G_OA: w_oa = sum_i min(u_oi, u_ai), calculado item a item (esparso)."""
    D = inst.D.tocsc()
    S = inst.S.tocsc()
    rows, cols, vals = [], [], []
    for i in range(inst.n_itens):
        p0, p1 = D.indptr[i], D.indptr[i + 1]
        c0, c1 = S.indptr[i], S.indptr[i + 1]
        if p0 == p1 or c0 == c1:
            continue
        ped, qd = D.indices[p0:p1], D.data[p0:p1]
        cor, qs = S.indices[c0:c1], S.data[c0:c1]
        m = np.minimum.outer(qd, qs)
        rows.append(np.repeat(ped, len(cor)))
        cols.append(np.tile(cor, len(ped)))
        vals.append(m.ravel())
    if not rows:
        return sp.csr_matrix((inst.n_pedidos, inst.n_corredores))
    W = sp.csr_matrix(
        (np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))),
        shape=(inst.n_pedidos, inst.n_corredores), dtype=np.float64,
    )
    W.sum_duplicates()
    return W


# ---------------------------------------------------------------- projeções
def _knn_simetrico(M: sp.csr_matrix, k: int) -> sp.csr_matrix:
    """Mantém, por linha, as k maiores entradas e simetriza pelo máximo."""
    M = M.tocsr()
    M.setdiag(0)
    M.eliminate_zeros()
    rows, cols, vals = [], [], []
    for r in range(M.shape[0]):
        a, b = M.indptr[r], M.indptr[r + 1]
        if a == b:
            continue
        idx, val = M.indices[a:b], M.data[a:b]
        if len(val) > k:
            sel = np.argpartition(-val, k - 1)[:k]
            idx, val = idx[sel], val[sel]
        rows.append(np.full(len(idx), r))
        cols.append(idx)
        vals.append(val)
    if not rows:
        return sp.csr_matrix(M.shape)
    K = sp.csr_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))), shape=M.shape)
    return K.maximum(K.T).tocsr()


def _produto_knn(X: sp.csr_matrix, Y: sp.csr_matrix, k: int, bloco_nnz: float = 2e7) -> sp.csr_matrix:
    """kNN de X @ Y calculado em blocos de linhas para limitar a memória."""
    n = X.shape[0]
    # nnz esperado por linha do produto: soma dos graus (em Y) das colunas de cada linha de X
    grau_col = np.diff(Y.tocsr().indptr).astype(np.float64)
    nnz_linha = np.asarray(X.astype(bool).astype(np.float64) @ grau_col).ravel()
    partes, inicio = [], 0
    while inicio < n:
        acum = np.cumsum(nnz_linha[inicio:])
        fim = inicio + max(1, int(np.searchsorted(acum, bloco_nnz)))
        fim = min(n, fim)
        P = (X[inicio:fim] @ Y).tocoo()
        fora_diag = P.row + inicio != P.col
        P = sp.csr_matrix((P.data[fora_diag], (P.row[fora_diag], P.col[fora_diag])), shape=P.shape)
        partes.append(_topk_linhas(P, k))
        inicio = fim
    K = sp.vstack(partes).tocsr()
    return K.maximum(K.T).tocsr()


def _topk_linhas(P: sp.csr_matrix, k: int) -> sp.csr_matrix:
    rows, cols, vals = [], [], []
    for r in range(P.shape[0]):
        a, b = P.indptr[r], P.indptr[r + 1]
        if a == b:
            continue
        idx, val = P.indices[a:b], P.data[a:b]
        if len(val) > k:
            sel = np.argpartition(-val, k - 1)[:k]
            idx, val = idx[sel], val[sel]
        rows.append(np.full(len(idx), r))
        cols.append(idx)
        vals.append(val)
    if not rows:
        return sp.csr_matrix(P.shape)
    return sp.csr_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))), shape=P.shape)


def afinidade_itens(inst: Instancia, k: int) -> sp.csr_matrix:
    """Jaccard ponderado (Eq. 4): sum min(u_oi,u_o'i) / sum max(u_oi,u_o'i).

    Usa min + max = u_oi + u_o'i  =>  sum max = u_o + u_o' - sum min.
    O numerador sum_i min(u_oi, u_o'i) é calculado item a item.
    """
    D = inst.D.tocsc()
    rows, cols, vals = [], [], []
    for i in range(inst.n_itens):
        a, b = D.indptr[i], D.indptr[i + 1]
        if b - a < 2:
            continue
        ped, q = D.indices[a:b], D.data[a:b]
        m = np.minimum.outer(q, q).astype(np.float64)
        rr, cc = np.meshgrid(ped, ped, indexing="ij")
        mask = rr != cc
        rows.append(rr[mask]); cols.append(cc[mask]); vals.append(m[mask])
    n = inst.n_pedidos
    if not rows:
        return sp.csr_matrix((n, n))
    MIN = sp.csr_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))), shape=(n, n))
    MIN.sum_duplicates()
    u = inst.unidades_pedido.astype(np.float64)
    C = MIN.tocoo()
    jac = C.data / (u[C.row] + u[C.col] - C.data)
    J = sp.csr_matrix((jac, (C.row, C.col)), shape=(n, n))
    return _knn_simetrico(J, k)


def afinidade_corredores(inst: Instancia, k: int, W_oa: sp.csr_matrix | None = None) -> sp.csr_matrix:
    """Adamic--Adar sobre corredores comuns (Eq. 5): sum_a 1/ln(1+k_a)."""
    if W_oa is None:
        W_oa = grafo_pedido_corredor(inst)
    B = W_oa.copy()
    B.data[:] = 1.0
    grau_a = np.asarray(B.sum(axis=0)).ravel()
    peso_a = np.where(grau_a > 0, 1.0 / np.log1p(np.maximum(grau_a, 1)), 0.0)
    Y = (sp.diags(peso_a) @ B.T).tocsr()
    return _produto_knn(B.tocsr(), Y, k)


def afinidade_combinada(J: sp.csr_matrix, A: sp.csr_matrix, alpha: float, k: int) -> sp.csr_matrix:
    def norm(M):
        M = M.tocsr().copy()
        if M.nnz:
            M.data = M.data / M.data.max()
        return M
    C = alpha * norm(J) + (1 - alpha) * norm(A)
    return _knn_simetrico(C, k)


def projecao_corredores(W_oa: sp.csr_matrix) -> sp.csr_matrix:
    """G_A: peso(a,b) = unidades de pedidos que ambos os corredores podem atender,
    sum_o min(w_oa, w_ob). Aproximação via produto B^T diag(u) B com B binária."""
    B = W_oa.copy()
    B.data[:] = 1.0
    u = np.asarray(W_oa.max(axis=1).todense()).ravel()
    G = (B.T @ sp.diags(u) @ B).tocsr()
    G.setdiag(0)
    G.eliminate_zeros()
    return G


# ---------------------------------------------------------------- métricas
def para_igraph(M: sp.csr_matrix) -> ig.Graph:
    C = sp.triu(M, k=1).tocoo()
    g = ig.Graph(n=M.shape[0], edges=list(zip(C.row.tolist(), C.col.tolist())), directed=False)
    g.es["weight"] = C.data.tolist()
    return g


def metricas(g: ig.Graph, semente: int = 0, resolucao: float = 1.0) -> dict:
    n, m = g.vcount(), g.ecount()
    comp = g.connected_components()
    isolados = sum(1 for d in g.degree() if d == 0)
    forca = np.array(g.strength(weights="weight")) if m else np.zeros(n)
    part = la.find_partition(
        g, la.RBConfigurationVertexPartition, weights="weight" if m else None,
        resolution_parameter=resolucao, seed=semente,
    )
    tamanhos = np.array(part.sizes())
    nao_triviais = tamanhos[tamanhos > 1]
    return {
        "vertices": n,
        "arestas": m,
        "densidade": 2 * m / (n * (n - 1)) if n > 1 else 0.0,
        "grau_medio": 2 * m / n if n else 0.0,
        "isolados_frac": isolados / n if n else 0.0,
        "componentes": len(comp),
        "maior_comp_frac": max(comp.sizes()) / n if n else 0.0,
        "forca_media": float(forca.mean()) if n else 0.0,
        "forca_cv": float(forca.std() / forca.mean()) if forca.mean() > 0 else 0.0,
        "agrupamento": g.transitivity_avglocal_undirected(mode="zero") if m else 0.0,
        "modularidade": g.modularity(part.membership, weights="weight") if m else 0.0,
        "comunidades": int(len(nao_triviais)),
        "comunidade_tam_med": float(np.median(nao_triviais)) if len(nao_triviais) else 0.0,
    }


# ---------------------------------------------------------------- script
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("instancia")
    ap.add_argument("--afinidade", default="itens", choices=["itens", "corredores", "combinada"])
    ap.add_argument("--k", type=int, default=10)
    ap.add_argument("--alpha", type=float, default=0.5)
    ap.add_argument("--salvar", default=None, help="pasta para salvar os grafos (.npz)")
    a = ap.parse_args()

    inst = ler_instancia(a.instancia)
    W_oa = grafo_pedido_corredor(inst)
    if a.afinidade == "itens":
        G_O = afinidade_itens(inst, a.k)
    elif a.afinidade == "corredores":
        G_O = afinidade_corredores(inst, a.k, W_oa)
    else:
        G_O = afinidade_combinada(afinidade_itens(inst, a.k), afinidade_corredores(inst, a.k, W_oa), a.alpha, a.k)
    G_A = projecao_corredores(W_oa)

    print("G_O:", metricas(para_igraph(G_O)))
    print("G_A:", metricas(para_igraph(G_A)))

    if a.salvar:
        p = Path(a.salvar)
        p.mkdir(parents=True, exist_ok=True)
        base = Path(a.instancia).stem
        sp.save_npz(p / f"{base}_G_OI.npz", inst.D)
        sp.save_npz(p / f"{base}_G_IA.npz", inst.S.T.tocsr())
        sp.save_npz(p / f"{base}_G_OA.npz", W_oa)
        sp.save_npz(p / f"{base}_G_O_{a.afinidade}_k{a.k}.npz", G_O)
        sp.save_npz(p / f"{base}_G_A.npz", G_A)
        print("grafos salvos em", p)


if __name__ == "__main__":
    main()
