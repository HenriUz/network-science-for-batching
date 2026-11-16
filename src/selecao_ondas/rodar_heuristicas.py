"""Executa B0, H1--H4 em todas as instâncias oficiais e compara com a BKS.

Uso: python rodar_heuristicas.py <repo_desafio> <saida.csv> [conjuntos...]   (ex.: a b x)
"""
import csv
import sys
from pathlib import Path

from heuristicas import executar_todas
from instancia import ler_instancia


def main(repo: Path, saida: Path, conjuntos=("a", "b", "x")) -> None:
    bks = {(r["dataset"], r["instance"][:-4]): float(r["best_objective"])
           for r in csv.DictReader(open(repo / "best_solutions" / "best_objectives.csv"))}
    campos = ["dataset", "instancia", "metodo", "razao", "BKS", "gap_pct", "corredores", "pedidos", "unidades", "tempo_s"]
    with open(saida, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        for ds in conjuntos:
            for arq in sorted((repo / "datasets" / ds).glob("instance_*.txt")):
                inst = ler_instancia(arq)
                ref = bks[(ds, arq.stem)]
                for s in executar_todas(inst):
                    w.writerow({"dataset": ds.upper(), "instancia": arq.stem[-4:], "metodo": s.metodo,
                                "razao": round(s.razao, 4), "BKS": round(ref, 4),
                                "gap_pct": round(100 * (ref - s.razao) / ref, 2),
                                "corredores": len(s.corredores), "pedidos": len(s.pedidos),
                                "unidades": s.unidades, "tempo_s": round(s.tempo, 2)})
                f.flush()
                print(ds, arq.stem, flush=True)


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]), tuple(sys.argv[3:]) or ("a", "b", "x"))
