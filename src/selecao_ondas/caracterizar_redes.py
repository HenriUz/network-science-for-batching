"""Métricas de rede (Tabela 11 do texto) para todas as instâncias oficiais.

Uso: python caracterizar_redes.py <pasta_datasets> <saida.csv> [k]
"""
import csv
import sys
import time
from pathlib import Path

from grafos import (afinidade_corredores, afinidade_itens, grafo_pedido_corredor, metricas,
                    para_igraph, projecao_corredores)
from instancia import ler_instancia


def main(pasta: Path, saida: Path, k: int = 10) -> None:
    linhas = []
    for ds in ["a", "b", "x"]:
        for arq in sorted((pasta / ds).glob("instance_*.txt")):
            t0 = time.time()
            inst = ler_instancia(arq)
            W = grafo_pedido_corredor(inst)
            graus_a = (W > 0).sum(axis=0).A1
            base = {"dataset": ds.upper(), "instancia": arq.stem.replace("instance_", ""),
                    "arestas_GOA": W.nnz, "grau_corredor_max_frac": graus_a.max() / inst.n_pedidos}
            for nome, M in [("O_itens", afinidade_itens(inst, k)),
                            ("O_corredores", afinidade_corredores(inst, k, W)),
                            ("A", projecao_corredores(W))]:
                for chave, valor in metricas(para_igraph(M)).items():
                    base[f"{nome}_{chave}"] = valor
            base["tempo_s"] = round(time.time() - t0, 2)
            linhas.append(base)
            print(ds, arq.stem, base["tempo_s"], flush=True)
    with open(saida, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0]))
        w.writeheader()
        w.writerows(linhas)


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]), int(sys.argv[3]) if len(sys.argv) > 3 else 10)
