"""Executa B0, H1--H4 nas instâncias da Zalando convertidas (sem BKS publicada).

Uso: python rodar_zalando.py <pasta_convertidas> <saida.csv> [prefixos...]
"""
import csv
import sys
from pathlib import Path

from heuristicas import executar_todas
from instancia import ler_instancia

if __name__ == "__main__":
    pasta, saida = Path(sys.argv[1]), Path(sys.argv[2])
    prefixos = sys.argv[3:] or ["small", "medium"]
    campos = ["dataset", "instancia", "metodo", "razao", "corredores", "pedidos", "unidades", "tempo_s"]
    with open(saida, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        for arq in sorted(pasta.glob("*.txt")):
            if not any(arq.stem.startswith(p) for p in prefixos):
                continue
            inst = ler_instancia(arq)
            for s in executar_todas(inst):
                w.writerow({"dataset": "Z", "instancia": arq.stem, "metodo": s.metodo,
                            "razao": round(s.razao, 4), "corredores": len(s.corredores),
                            "pedidos": len(s.pedidos), "unidades": s.unidades, "tempo_s": round(s.tempo, 2)})
            f.flush()
            print(arq.stem, flush=True)
