"""Converte as instâncias da Zalando (Abelli et al., 2024) para o formato do desafio.

Correspondência adotada:
    item      <- artigo
    corredor  <- par (zona, corredor) do armazém
    u_ai      <- número de unidades (warehouse items) do artigo naquele corredor
    u_oi      <- número de posições do pedido com o artigo
    LB        <- round(f_lb * demanda total)   (f_lb = 0,105, mediana das instâncias oficiais)
    UB        <- round(f_ub * demanda total)   (f_ub = 0,378, mediana das instâncias oficiais)

Uso: python converter_zalando.py <pasta_instancias_zalando> <pasta_saida> [f_lb f_ub]
"""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path


def converter(pasta: Path, saida: Path, f_lb: float, f_ub: float) -> dict:
    pedidos_json = json.load(open(pasta / "orders.json"))
    itens_json = json.load(open(pasta / "warehouse_items.json"))

    artigos = sorted({w["article"] for w in itens_json} | {a for o in pedidos_json for a in o["positions"]})
    id_item = {a: k for k, a in enumerate(artigos)}
    corredores = sorted({(w["zone"], w["aisle"]) for w in itens_json})
    id_corr = {c: k for k, c in enumerate(corredores)}

    oferta = defaultdict(Counter)
    for w in itens_json:
        oferta[id_corr[(w["zone"], w["aisle"])]][id_item[w["article"]]] += 1
    pedidos = [Counter(id_item[a] for a in o["positions"]) for o in pedidos_json]

    total = sum(sum(p.values()) for p in pedidos)
    lb, ub = round(f_lb * total), round(f_ub * total)
    with open(saida, "w") as f:
        f.write(f"{len(pedidos)} {len(artigos)} {len(corredores)}\n")
        for p in pedidos:
            f.write(" ".join([str(len(p))] + [f"{i} {q}" for i, q in sorted(p.items())]) + "\n")
        for a in range(len(corredores)):
            c = oferta[a]
            f.write(" ".join([str(len(c))] + [f"{i} {q}" for i, q in sorted(c.items())]) + "\n")
        f.write(f"{lb} {ub}\n")
    return {"instancia": pasta.name, "pedidos": len(pedidos), "itens": len(artigos),
            "corredores": len(corredores), "LB": lb, "UB": ub, "demanda": total}


if __name__ == "__main__":
    origem, destino = Path(sys.argv[1]), Path(sys.argv[2])
    f_lb = float(sys.argv[3]) if len(sys.argv) > 3 else 0.105
    f_ub = float(sys.argv[4]) if len(sys.argv) > 4 else 0.378
    destino.mkdir(parents=True, exist_ok=True)
    for p in sorted(origem.iterdir()):
        if (p / "orders.json").exists():
            print(converter(p, destino / f"{p.name}.txt", f_lb, f_ub), flush=True)
