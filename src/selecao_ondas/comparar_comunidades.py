"""Compara particoes Leiden e Louvain em G_O e G_A."""
from __future__ import annotations

import csv
import sys
import time
from pathlib import Path

import numpy as np

from grafos import (
    afinidade_corredores,
    detectar_comunidades,
    grafo_pedido_corredor,
    para_igraph,
    projecao_corredores,
)
from instancia import ler_instancia


def nmi(membros_a: list[int], membros_b: list[int]) -> float:
    """Informacao mutua normalizada (metrica ajustada ao desempate de rotulos)."""
    a, b = np.asarray(membros_a), np.asarray(membros_b)
    n = len(a)
    if n == 0:
        return 0.0

    cont = {}
    ca = np.bincount(a)
    cb = np.bincount(b)
    for ia, ib in zip(a, b):
        cont[(int(ia), int(ib))] = cont.get((int(ia), int(ib)), 0) + 1

    def ent(vals):
        p = vals[vals > 0] / n
        return float(-np.sum(p * np.log(p)))

    mi = sum((v / n) * np.log((v / n) / (ca[ia] * cb[ib] / (n * n)))
             for (ia, ib), v in cont.items())
    ha, hb = ent(ca), ent(cb)
    return float(2 * mi / (ha + hb)) if ha + hb else 1.0


def comparar_grafo(g, nome_grafo: str, nome_instancia: str) -> list[dict]:
    linhas = []
    for resolucao in (0.5, 1.0, 2.0, 4.0):
        t0 = time.time()
        leiden = detectar_comunidades(g, "leiden", resolucao=resolucao, semente=0)
        leiden_t = time.time() - t0
        t0 = time.time()
        louvain = detectar_comunidades(g, "louvain", semente=0)
        louvain_t = time.time() - t0

        linhas.extend([
            {
                "instancia": nome_instancia,
                "grafo": nome_grafo,
                "algoritmo": "Leiden",
                "resolucao": resolucao,
                "comunidades": len(leiden),
                "comunidade_tam_med": float(np.median(leiden.sizes())),
                "modularidade": g.modularity(leiden.membership, weights="weight"),
                "tempo_s": round(leiden_t, 4),
            },
            {
                "instancia": nome_instancia,
                "grafo": nome_grafo,
                "algoritmo": "Louvain",
                "resolucao": 1.0,
                "comunidades": len(louvain),
                "comunidade_tam_med": float(np.median(louvain.sizes())),
                "modularidade": g.modularity(louvain.membership, weights="weight"),
                "tempo_s": round(louvain_t, 4),
                "NMI_vs_Leiden": nmi(leiden.membership, louvain.membership),
            },
        ])
    return linhas


def main(instancia_path: str, saida: str, k: int = 10) -> None:
    inst = ler_instancia(instancia_path)
    W = grafo_pedido_corredor(inst)
    GO = afinidade_corredores(inst, k, W)
    GA = projecao_corredores(W)
    linhas = []
    linhas += comparar_grafo(para_igraph(GO), "G_O", inst.nome)
    linhas += comparar_grafo(para_igraph(GA), "G_A", inst.nome)

    caminho = Path(saida)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    campos = list(dict.fromkeys(chave for linha in linhas for chave in linha))
    with caminho.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows(linhas)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python comparar_comunidades.py instancia.txt saida.csv [k]")
        raise SystemExit(1)
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 10)
