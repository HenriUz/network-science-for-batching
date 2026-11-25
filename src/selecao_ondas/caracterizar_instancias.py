"""Tabela de caracterização das instâncias oficiais (id, quantitativos, BKS).

Uso: python caracterizar_instancias.py <repo_desafio> <saida.csv>
"""
import csv
import sys
from pathlib import Path

import numpy as np

from instancia import avaliar, ler_instancia, ler_solucao


def main(repo: Path, saida: Path) -> None:
    bks = {}
    with open(repo / "best_solutions" / "best_objectives.csv") as f:
        for r in csv.DictReader(f):
            bks[(r["dataset"], r["instance"].replace(".txt", ""))] = float(r["best_objective"])

    linhas = []
    for ds in ["a", "b", "x"]:
        for arq in sorted((repo / "datasets" / ds).glob("instance_*.txt")):
            inst = ler_instancia(arq)
            u_ped = inst.unidades_pedido
            itens_por_pedido = np.diff(inst.D.indptr)
            itens_por_corr = np.diff(inst.S.indptr)
            # em quantos corredores cada item demandado aparece
            corr_por_item = np.diff(inst.S.tocsc().indptr)
            demandados = np.asarray((inst.D != 0).sum(axis=0)).ravel() > 0
            ped, cor = ler_solucao(repo / "best_solutions" / ds / arq.name)
            viavel, obj, unid = avaliar(inst, ped, cor)
            ref = bks[(ds, arq.stem)]
            linhas.append({
                "dataset": ds.upper(),
                "instancia": arq.stem.replace("instance_", ""),
                "pedidos": inst.n_pedidos,
                "itens": inst.n_itens,
                "corredores": inst.n_corredores,
                "LB": inst.lb,
                "UB": inst.ub,
                "unid_total": int(u_ped.sum()),
                "UB_frac": round(inst.ub / u_ped.sum(), 4),
                "itens_por_pedido": round(itens_por_pedido.mean(), 2),
                "unid_por_pedido": round(u_ped.mean(), 2),
                "itens_por_corredor": round(itens_por_corr.mean(), 2),
                "corredores_por_item": round(corr_por_item[demandados].mean(), 2),
                "BKS": round(ref, 4),
                "BKS_pedidos": len(ped),
                "BKS_corredores": len(cor),
                "BKS_unidades": unid,
                "BKS_viavel": viavel,
                "BKS_confere": abs(obj - ref) < 1e-6,
            })
            print(linhas[-1]["dataset"], linhas[-1]["instancia"], "ok" if viavel and abs(obj - ref) < 1e-6 else "DIVERGE")

    with open(saida, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0]))
        w.writeheader()
        w.writerows(linhas)


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
