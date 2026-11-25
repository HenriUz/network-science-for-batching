"""Compara criterios de rede para priorizar corredores durante H3.

Uso: python comparar_metricas_crescimento.py <pasta_instancias> <pasta_saida>
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import igraph as ig
import numpy as np
import scipy.sparse as sp
from scipy.stats import rankdata, wilcoxon

from grafos import grafo_pedido_corredor, projecao_corredores
from heuristicas import Nucleo, crescimento_guiado
from instancia import avaliar, ler_instancia

METRICAS = ("forca_local", "grau_local", "forca", "grau", "pagerank", "k_core")
CENTRALIDADES = ("grau", "forca", "pagerank", "k_core")


def _centralidades_corredores(G_A):
    n = G_A.shape[0]
    grau = np.asarray((G_A != 0).sum(axis=1)).ravel().astype(float)
    forca = np.asarray(G_A.sum(axis=1)).ravel().astype(float)
    superior = sp.triu(G_A, k=1).tocoo()
    ig_grafo = ig.Graph(
        n=n,
        edges=list(zip(superior.row.tolist(), superior.col.tolist())),
        directed=False,
    )
    ig_grafo.es["weight"] = superior.data.astype(float).tolist()
    return {
        "grau": grau,
        "forca": forca,
        "pagerank": np.asarray(
            ig_grafo.pagerank(weights="weight", directed=False), dtype=float
        ),
        "k_core": np.asarray(ig_grafo.coreness(), dtype=float),
    }


def _resumo_selecao(corredores, centralidades):
    if not corredores:
        return {}
    ids = np.asarray(corredores, dtype=int)
    resumo = {}
    for nome, valores in centralidades.items():
        percentis = rankdata(valores, method="average") / len(valores)
        resumo[f"{nome}_percentil_medio_selecionado"] = float(percentis[ids].mean())
        resumo[f"{nome}_fracao_top10_selecionada"] = float((percentis[ids] > 0.9).mean())
    return resumo


def _p_wilcoxon(pares):
    if len(pares) < 2:
        return ""
    diferencas = [a - b for a, b in pares]
    if all(d == 0 for d in diferencas):
        return 1.0
    return float(wilcoxon(diferencas, alternative="two-sided").pvalue)


def comparar_instancia(caminho: Path, bks: dict | None = None) -> list[dict]:
    inst = ler_instancia(caminho)
    n = Nucleo(inst)
    W = grafo_pedido_corredor(inst)
    G_A = projecao_corredores(W)
    centralidades = _centralidades_corredores(G_A)
    chave_bks = (caminho.parent.name.lower(), caminho.stem)
    referencia = bks.get(chave_bks) if bks else None
    saida = []
    for metrica in METRICAS:
        sol = crescimento_guiado(n, G_A, metrica=metrica)
        if sol:
            viavel, objetivo, unidades = avaliar(inst, sol.pedidos, sol.corredores)
            if not viavel or abs(objetivo - sol.razao) > 1e-9 or unidades != sol.unidades:
                raise ValueError(f"Solução inválida para {inst.nome} com {metrica}")
        row = {
            "instancia": inst.nome,
            "metrica": metrica,
            "viavel": sol is not None,
            "razao": sol.razao if sol else 0.0,
            "unidades": sol.unidades if sol else 0,
            "n_corredores": len(sol.corredores) if sol else 0,
            "tempo_s": sol.tempo if sol else 0.0,
            "BKS": referencia if referencia is not None else "",
            "gap_pct": (
                100 * (referencia - sol.razao) / referencia
                if referencia is not None and sol else
                100.0 if referencia is not None else ""
            ),
            "atingiu_BKS": (
                abs(sol.razao - referencia) <= 1e-6
                if referencia is not None and sol else False if referencia is not None else ""
            ),
        }
        if sol:
            row.update(_resumo_selecao(sol.corredores, centralidades))
        else:
            row.update({
                f"{nome}_{estat}": ""
                for nome in CENTRALIDADES
                for estat in ("percentil_medio_selecionado", "fracao_top10_selecionada")
            })
        saida.append(row)
    return saida


def resumir(linhas: list[dict]) -> list[dict]:
    por_metrica = {
        nome: [r for r in linhas if r["metrica"] == nome]
        for nome in METRICAS
    }
    base = {r["instancia"]: r for r in por_metrica["forca_local"]}
    resumos = []
    pvalores = {}
    pvalores_gap = {}
    for nome, rows in por_metrica.items():
        viaveis = [r for r in rows if r["viavel"]]
        pareados = [
            (r["razao"], base[r["instancia"]]["razao"])
            for r in rows
            if r["instancia"] in base and r["viavel"] and base[r["instancia"]]["viavel"]
        ]
        wins = sum(a > b for a, b in pareados)
        ties = sum(a == b for a, b in pareados)
        losses = sum(a < b for a, b in pareados)
        pvalor = _p_wilcoxon(pareados)
        if nome != "forca_local" and pvalor != "":
            pvalores[nome] = pvalor
        com_bks = [r for r in rows if r["BKS"] != ""]
        gaps = [float(r["gap_pct"]) for r in com_bks]
        atingiu = sum(bool(r["atingiu_BKS"]) for r in com_bks)
        base_gap = {
            r["instancia"]: float(r["gap_pct"])
            for r in por_metrica["forca_local"]
            if r["BKS"] != "" and r["viavel"]
        }
        pareados_gap = [
            (float(r["gap_pct"]), base_gap[r["instancia"]])
            for r in rows
            if r["BKS"] != "" and r["viavel"] and r["instancia"] in base_gap
        ]
        p_gap = _p_wilcoxon(pareados_gap)
        if nome != "forca_local" and p_gap != "":
            pvalores_gap[nome] = p_gap
        resumo = {
            "metrica": nome,
            "instancias": len(rows),
            "solucoes_viaveis": len(viaveis),
            "fracao_viavel": len(viaveis) / len(rows) if rows else 0.0,
            "razao_media_viaveis": float(np.mean([r["razao"] for r in viaveis])) if viaveis else "",
            "razao_mediana_viaveis": float(np.median([r["razao"] for r in viaveis])) if viaveis else "",
            "razao_media_com_falhas_zero": float(np.mean([r["razao"] for r in rows])) if rows else "",
            "pares_viaveis_com_base": len(pareados),
            "vitorias_vs_forca_local": wins,
            "empates_vs_forca_local": ties,
            "derrotas_vs_forca_local": losses,
            "delta_mediano_razao_pareada": (
                float(np.median([a - b for a, b in pareados])) if pareados else ""
            ),
            "p_wilcoxon_bruto_vs_forca_local": pvalor,
            "p_wilcoxon_bruto_gap_vs_forca_local": p_gap,
            "instancias_com_BKS": len(com_bks),
            "gap_medio_pct_vs_BKS": float(np.mean(gaps)) if gaps else "",
            "gap_mediano_pct_vs_BKS": float(np.median(gaps)) if gaps else "",
            "atingiu_BKS_n_instancias": atingiu,
        }
        for centralidade in CENTRALIDADES:
            resumo[f"{centralidade}_percentil_medio_selecionado"] = (
                float(np.mean([r[f"{centralidade}_percentil_medio_selecionado"] for r in viaveis]))
                if viaveis else ""
            )
            resumo[f"{centralidade}_fracao_top10_selecionada"] = (
                float(np.mean([r[f"{centralidade}_fracao_top10_selecionada"] for r in viaveis]))
                if viaveis else ""
            )
        resumos.append(resumo)

    ordenados = sorted(pvalores.items(), key=lambda item: item[1])
    p_ajustados = {}
    maior_ajustado = 0.0
    quantidade = len(ordenados)
    for posicao, (nome, pvalor) in enumerate(ordenados):
        candidato = min(1.0, (quantidade - posicao) * pvalor)
        maior_ajustado = max(maior_ajustado, candidato)
        p_ajustados[nome] = maior_ajustado
    for resumo in resumos:
        resumo["p_wilcoxon_holm_vs_forca_local"] = p_ajustados.get(resumo["metrica"], "")
    ordenados_gap = sorted(pvalores_gap.items(), key=lambda item: item[1])
    p_ajustados_gap = {}
    maior_ajustado_gap = 0.0
    quantidade_gap = len(ordenados_gap)
    for posicao, (nome, pvalor) in enumerate(ordenados_gap):
        candidato = min(1.0, (quantidade_gap - posicao) * pvalor)
        maior_ajustado_gap = max(maior_ajustado_gap, candidato)
        p_ajustados_gap[nome] = maior_ajustado_gap
    for resumo in resumos:
        resumo["p_wilcoxon_holm_gap_vs_forca_local"] = p_ajustados_gap.get(
            resumo["metrica"], ""
        )
    return resumos


def resumir_por_conjunto(linhas: list[dict]) -> list[dict]:
    grupos = {}
    for row in linhas:
        conjunto = row["instancia"].split("/", 1)[0].lower()
        grupos.setdefault(conjunto, []).append(row)
    saida = []
    for conjunto, rows in sorted(grupos.items()):
        for resumo in resumir(rows):
            saida.append({"conjunto": conjunto.upper(), **resumo})
    return saida


def _salvar(caminho: Path, linhas: list[dict]):
    caminho.parent.mkdir(parents=True, exist_ok=True)
    campos = list(dict.fromkeys(k for row in linhas for k in row))
    with caminho.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writeheader()
        escritor.writerows(linhas)


def main(pasta: Path, saida: Path, repo_bks: Path | None = None):
    arquivos = sorted(pasta.rglob("instance_*.txt"))
    if not arquivos:
        raise FileNotFoundError(f"Nenhuma instância instance_*.txt em {pasta}")
    bks = None
    if repo_bks is not None:
        caminho_bks = repo_bks / "best_solutions" / "best_objectives.csv"
        with caminho_bks.open(encoding="utf-8", newline="") as arquivo:
            bks = {
                (r["dataset"].lower(), Path(r["instance"]).stem): float(r["best_objective"])
                for r in csv.DictReader(arquivo)
            }
    linhas = []
    for caminho in arquivos:
        novas = comparar_instancia(caminho, bks)
        linhas.extend(novas)
        print(f"{caminho}: concluído", flush=True)
    _salvar(saida / "metricas_por_instancia.csv", linhas)
    resumo = resumir(linhas)
    _salvar(saida / "resumo_metricas.csv", resumo)
    _salvar(saida / "resumo_por_conjunto.csv", resumir_por_conjunto(linhas))
    for row in resumo:
        print(
            row["metrica"],
            f"viáveis={row['solucoes_viaveis']}/{row['instancias']}",
            f"média={row['razao_media_viaveis']}",
            f"gap_BKS={row['gap_medio_pct_vs_BKS']}",
            f"p_Holm={row['p_wilcoxon_holm_vs_forca_local']}",
            flush=True,
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("pasta_instancias", type=Path)
    parser.add_argument("pasta_saida", type=Path)
    parser.add_argument("--bks-repo", type=Path)
    args = parser.parse_args()
    main(args.pasta_instancias, args.pasta_saida, args.bks_repo)
