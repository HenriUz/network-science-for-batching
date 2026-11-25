"""Leitura das instâncias e soluções do Desafio Mercado Livre (SBPO 2025).

Formato da instância (igual ao checker.py oficial):
    linha 1: |O| |I| |A|
    |O| linhas: k item_1 qtd_1 ... item_k qtd_k      (pedidos)
    |A| linhas: k item_1 qtd_1 ... item_k qtd_k      (corredores)
    última linha: LB UB
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import scipy.sparse as sp


@dataclass
class Instancia:
    nome: str
    n_pedidos: int
    n_itens: int
    n_corredores: int
    pedidos: list[dict[int, int]]
    corredores: list[dict[int, int]]
    lb: int
    ub: int
    # Matrizes esparsas (CSR): demanda pedido x item, oferta corredor x item
    D: sp.csr_matrix = field(repr=False, default=None)
    S: sp.csr_matrix = field(repr=False, default=None)

    @property
    def unidades_pedido(self) -> np.ndarray:
        return np.asarray(self.D.sum(axis=1)).ravel()


def _matriz(linhas: list[dict[int, int]], n_linhas: int, n_itens: int) -> sp.csr_matrix:
    rows, cols, vals = [], [], []
    for r, mapa in enumerate(linhas):
        for item, qtd in mapa.items():
            rows.append(r)
            cols.append(item)
            vals.append(qtd)
    return sp.csr_matrix((vals, (rows, cols)), shape=(n_linhas, n_itens), dtype=np.int64)


def ler_instancia(caminho: str | Path) -> Instancia:
    caminho = Path(caminho)
    with open(caminho) as f:
        linhas = [l for l in f.read().splitlines() if l.strip()]
    o, i, a = map(int, linhas[0].split())

    def parse(l: str) -> dict[int, int]:
        t = list(map(int, l.split()))
        k = t[0]
        return {t[2 * j + 1]: t[2 * j + 2] for j in range(k)}

    pedidos = [parse(linhas[1 + j]) for j in range(o)]
    corredores = [parse(linhas[1 + o + j]) for j in range(a)]
    lb, ub = map(int, linhas[1 + o + a].split())
    inst = Instancia(
        nome=f"{caminho.parent.name}/{caminho.stem}",
        n_pedidos=o, n_itens=i, n_corredores=a,
        pedidos=pedidos, corredores=corredores, lb=lb, ub=ub,
    )
    inst.D = _matriz(pedidos, o, i)
    inst.S = _matriz(corredores, a, i)
    return inst


def ler_solucao(caminho: str | Path) -> tuple[list[int], list[int]]:
    with open(caminho) as f:
        t = [l.strip() for l in f if l.strip()]
    n_o = int(t[0])
    ped = [int(x) for x in t[1:1 + n_o]]
    n_a = int(t[1 + n_o])
    cor = [int(x) for x in t[2 + n_o:2 + n_o + n_a]]
    return sorted(set(ped)), sorted(set(cor))


def avaliar(inst: Instancia, pedidos: list[int], corredores: list[int]) -> tuple[bool, float, int]:
    """Viabilidade e objetivo, com a mesma lógica do checker.py oficial."""
    if not corredores:
        return False, 0.0, 0
    demanda = np.asarray(inst.D[pedidos].sum(axis=0)).ravel() if pedidos else np.zeros(inst.n_itens)
    oferta = np.asarray(inst.S[corredores].sum(axis=0)).ravel()
    unidades = int(demanda.sum())
    viavel = (inst.lb <= unidades <= inst.ub) and bool(np.all(demanda <= oferta))
    return viavel, unidades / len(corredores), unidades
