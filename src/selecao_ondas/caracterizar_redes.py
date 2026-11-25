"""Métricas de rede (Tabela 11 do texto) para todas as instâncias oficiais.

Uso: python caracterizar_redes.py <pasta_datasets> <saida.csv> [k]
"""
import csv
import sys
import time
from pathlib import Path

from grafos import (afinidade_corredores, afinidade_itens, grafo_pedido_corredor, metricas,
                    metricas_centralidade, para_igraph, projecao_corredores)
from instancia import ler_instancia


def main(pasta: Path, saida: Path, k: int = 10, centralidades: bool = False,
         betweenness: bool = False) -> None:
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
                g = para_igraph(M)
                for chave, valor in metricas(g).items():
                    base[f"{nome}_{chave}"] = valor
                if centralidades:
                    cent = metricas_centralidade(g, incluir_betweenness=betweenness)
                    for chave, resumo in cent.items():
                        for estat, valor in resumo.items():
                            base[f"{nome}_{chave}_{estat}"] = valor
            base["tempo_s"] = round(time.time() - t0, 2)
            linhas.append(base)
            print(ds, arq.stem, base["tempo_s"], flush=True)
    with open(saida, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0]))
        w.writeheader()
        w.writerows(linhas)


if __name__ == "__main__":
    centralidades = "--centralidades" in sys.argv
    betweenness = "--betweenness" in sys.argv
    pos = [x for x in sys.argv[1:] if not x.startswith("--")]
    main(
        Path(pos[0]),
        Path(pos[1]),
        int(pos[2]) if len(pos) > 2 else 10,
        centralidades=centralidades,
        betweenness=betweenness,
    )
