"""Figura dos grafos de demanda (para o texto e para apresentações).

Painéis:
  (a) G_OA  pedido--corredor da instância A-0001, com a onda da BKS destacada
  (b) G_O   pedido--pedido por itens compartilhados (A-0001)
  (c) G_O   pedido--pedido por corredores compartilhados (A-0001), cores = comunidades
  (d) G_O   por corredores na A-0017 (417 pedidos, um item por pedido), cores = comunidades

Uso: python desenhar_grafos.py <repo_desafio> <saida_sem_extensao>
"""
import sys
from pathlib import Path

import igraph as ig
import leidenalg as la
import matplotlib
import matplotlib.pyplot as plt
import numpy as np

from grafos import afinidade_corredores, afinidade_itens, grafo_pedido_corredor, para_igraph
from instancia import ler_instancia, ler_solucao

matplotlib.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9})

# paleta de referência (skill dataviz), modo claro
PEDIDO, CORREDOR = "#2a78d6", "#eb6834"
CATEG = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#6250d6"]
OUTRAS = "#b9b8b2"
TINTA, TINTA2, ARESTA = "#0b0b0b", "#52514e", "#c9c8c2"


def _desenhar(ax, g, layout, cores, tamanhos, formas, aneis=None, largura_aresta=0.4, alfa_aresta=0.5):
    xy = np.array(layout.coords)
    for e in g.es:
        a, b = e.tuple
        ax.plot(*xy[[a, b]].T, color=ARESTA, lw=largura_aresta, alpha=alfa_aresta, zorder=1)
    for forma in set(formas):
        idx = [i for i, f in enumerate(formas) if f == forma]
        ax.scatter(xy[idx, 0], xy[idx, 1], s=[tamanhos[i] for i in idx], c=[cores[i] for i in idx],
                   marker=forma, edgecolors="white", linewidths=0.6, zorder=2)
    if aneis:
        ax.scatter(xy[aneis, 0], xy[aneis, 1], s=[tamanhos[i] * 2.6 for i in aneis], facecolors="none",
                   edgecolors=TINTA, linewidths=1.2, marker="o", zorder=3)
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)


def _cores_comunidades(membros):
    tamanhos = np.bincount(membros)
    ordem = list(np.argsort(-tamanhos))
    mapa = {c: (CATEG[k] if k < len(CATEG) else OUTRAS) for k, c in enumerate(ordem)}
    return [mapa[m] for m in membros], len(tamanhos)


def main(repo: Path, saida: Path) -> None:
    fig, axs = plt.subplots(2, 2, figsize=(10, 9.4))

    # ------------------------------------------------ A-0001
    inst = ler_instancia(repo / "datasets/a/instance_0001.txt")
    ped_bks, cor_bks = ler_solucao(repo / "best_solutions/a/instance_0001.txt")
    W = grafo_pedido_corredor(inst)
    O, A = inst.n_pedidos, inst.n_corredores

    # (a) bipartido pedido--corredor (só corredores com alguma aresta)
    usados = np.flatnonzero(np.asarray((W > 0).sum(axis=0)).ravel() > 0)
    pos_cor = {a: O + k for k, a in enumerate(usados)}
    C = W.tocoo()
    g = ig.Graph(n=O + len(usados), edges=[(o, pos_cor[a]) for o, a in zip(C.row, C.col)])
    lay = g.layout_fruchterman_reingold(niter=1500, seed=np.random.default_rng(1).random((g.vcount(), 2)).tolist())
    cores = [PEDIDO] * O + [CORREDOR] * len(usados)
    tam = [26] * O + [30] * len(usados)
    formas = ["o"] * O + ["s"] * len(usados)
    aneis = list(ped_bks) + [pos_cor[a] for a in cor_bks]
    _desenhar(axs[0, 0], g, lay, cores, tam, formas, aneis, largura_aresta=0.3, alfa_aresta=0.35)
    axs[0, 0].set_title(f"(a) Pedido–corredor $G_{{OA}}$ — A-0001\n{O} pedidos, {len(usados)} corredores, {W.nnz} arestas",
                        loc="left", color=TINTA, fontsize=10)
    h = [plt.Line2D([], [], marker="o", ls="", color=PEDIDO, label="Pedido"),
         plt.Line2D([], [], marker="s", ls="", color=CORREDOR, label="Corredor"),
         plt.Line2D([], [], marker="o", ls="", mfc="none", mec=TINTA, label="Onda da BKS (9 pedidos, 2 corredores)")]
    axs[0, 0].legend(handles=h, loc="lower left", frameon=False, fontsize=8, labelcolor=TINTA2)

    # (b) pedido--pedido por itens
    gi = para_igraph(afinidade_itens(inst, 10))
    isol = sum(1 for d in gi.degree() if d == 0)
    lay_b = gi.layout_fruchterman_reingold(niter=800, seed=np.random.default_rng(2).random((O, 2)).tolist())
    _desenhar(axs[0, 1], gi, lay_b, [PEDIDO] * O, [34] * O, ["o"] * O, list(ped_bks), largura_aresta=0.9, alfa_aresta=0.9)
    axs[0, 1].set_title(f"(b) Pedido–pedido por itens compartilhados — A-0001\n{gi.ecount()} arestas; {isol} de {O} pedidos isolados ({100*isol/O:.0f}%)",
                        loc="left", color=TINTA, fontsize=10)

    # (c) pedido--pedido por corredores, comunidades
    gc = para_igraph(afinidade_corredores(inst, 10, W))
    part = la.find_partition(gc, la.RBConfigurationVertexPartition, weights="weight", seed=0)
    cores_c, ncom = _cores_comunidades(np.array(part.membership))
    lay_c = gc.layout_fruchterman_reingold(weights="weight", niter=1500,
                                            seed=np.random.default_rng(3).random((O, 2)).tolist())
    _desenhar(axs[1, 0], gc, lay_c, cores_c, [34] * O, ["o"] * O, list(ped_bks), largura_aresta=0.35, alfa_aresta=0.5)
    axs[1, 0].set_title(f"(c) Pedido–pedido por corredores compartilhados — A-0001\n{gc.ecount()} arestas; {ncom} comunidades (Leiden), modularidade {gc.modularity(part.membership, weights='weight'):.2f}",
                        loc="left", color=TINTA, fontsize=10)

    # ------------------------------------------------ (d) A-0017
    inst2 = ler_instancia(repo / "datasets/a/instance_0017.txt")
    W2 = grafo_pedido_corredor(inst2)
    gd = para_igraph(afinidade_corredores(inst2, 10, W2))
    part2 = la.find_partition(gd, la.RBConfigurationVertexPartition, weights="weight", seed=0)
    cores_d, ncom2 = _cores_comunidades(np.array(part2.membership))
    lay_d = gd.layout_fruchterman_reingold(weights="weight", niter=1500,
                                            seed=np.random.default_rng(4).random((gd.vcount(), 2)).tolist())
    ped2, _ = ler_solucao(repo / "best_solutions/a/instance_0017.txt")
    _desenhar(axs[1, 1], gd, lay_d, cores_d, [14] * gd.vcount(), ["o"] * gd.vcount(), list(ped2),
              largura_aresta=0.2, alfa_aresta=0.35)
    gi2 = para_igraph(afinidade_itens(inst2, 10))
    isol2 = sum(1 for d in gi2.degree() if d == 0)
    axs[1, 1].set_title(f"(d) Pedido–pedido por corredores — A-0017 (um item por pedido)\n{gd.vcount()} pedidos; {ncom2} comunidades, modularidade {gd.modularity(part2.membership, weights='weight'):.2f}\n(por itens: {100*isol2/gd.vcount():.0f}% dos pedidos ficariam isolados)",
                        loc="left", color=TINTA, fontsize=10)

    h2 = [plt.Line2D([], [], marker="o", ls="", color=c, label=f"Comunidade {k+1}") for k, c in enumerate(CATEG)]
    h2 += [plt.Line2D([], [], marker="o", ls="", color=OUTRAS, label="Demais comunidades"),
           plt.Line2D([], [], marker="o", ls="", mfc="none", mec=TINTA, label="Pedido da onda da BKS")]
    fig.legend(handles=h2, loc="lower center", ncol=4, frameon=False, fontsize=8.5, labelcolor=TINTA2,
               title="Painéis (c) e (d): cores = comunidades, da maior para a menor", title_fontsize=8.5)
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    for ext in ("png", "pdf"):
        fig.savefig(f"{saida}.{ext}", dpi=200, facecolor="#fcfcfb")
    print("ok", saida)


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
