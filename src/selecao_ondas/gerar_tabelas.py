"""Gera as tabelas LaTeX dos resultados preliminares a partir dos CSVs.

Uso: python gerar_tabelas.py <pasta_csv> <saida.tex>
"""
import sys
from pathlib import Path

import pandas as pd


def br(x, d=2):
    """Número no padrão brasileiro (vírgula decimal, ponto de milhar)."""
    if isinstance(x, (int,)) or (isinstance(x, float) and x.is_integer() and d == 0):
        return f"{int(x):,}".replace(",", ".")
    s = f"{x:,.{d}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def tab_instancias_resumo(c: pd.DataFrame) -> str:
    c = c.copy()
    c["um_item"] = c["itens_por_pedido"] == 1.0
    linhas = []
    for ds, g in c.groupby("dataset"):
        def faixa(col, d=0):
            return f"{br(g[col].min(), d)} -- {br(g[col].max(), d)}"
        linhas.append(
            f"{ds} & {len(g)} & {int(g.um_item.sum())} & {faixa('pedidos')} & {faixa('itens')} & "
            f"{faixa('corredores')} & {br(g['UB_frac'].median(), 2)} & {br(g['BKS_corredores'].median(), 0)} "
            f"({faixa('BKS_corredores')}) \\\\ \\hline")
    tot = c
    linhas.append(
        f"Total & {len(tot)} & {int(tot.um_item.sum())} & {br(tot.pedidos.min(),0)} -- {br(tot.pedidos.max(),0)} & "
        f"{br(tot.itens.min(),0)} -- {br(tot.itens.max(),0)} & {br(tot.corredores.min(),0)} -- {br(tot.corredores.max(),0)} & "
        f"{br(tot.UB_frac.median(),2)} & {br(tot.BKS_corredores.median(),0)} ({br(tot.BKS_corredores.min(),0)} -- {br(tot.BKS_corredores.max(),0)}) \\\\ \\hline")
    return r"""\begin{table*}[hbt!]
\centering
\caption{Resumo das instâncias oficiais do desafio por conjunto (faixas mínima--máxima).}
\label{tab:res_instancias}
\resizebox{\textwidth}{!}{%
\begin{tabular}{|c|c|c|c|c|c|c|c|}
\hline
\textbf{Conjunto} & \textbf{Instâncias} & \textbf{Um item por pedido} & \textbf{Pedidos} & \textbf{Itens} & \textbf{Corredores} & \textbf{$UB$/demanda (mediana)} & \textbf{Corredores na BKS: mediana (faixa)} \\ \hline
""" + "\n".join(linhas) + r"""
\end{tabular}%
}
\end{table*}
"""


def tab_instancias_completa(c: pd.DataFrame) -> str:
    linhas = []
    for _, r in c.iterrows():
        linhas.append(
            f"{r.dataset}-{int(r.instancia):04d} & {br(r.pedidos,0)} & {br(r.itens,0)} & {br(r.corredores,0)} & "
            f"{br(r.LB,0)} & {br(r.UB,0)} & {br(r.itens_por_pedido,2)} & {br(r.corredores_por_item,2)} & "
            f"{br(r.BKS,2)} & {br(r.BKS_pedidos,0)} & {br(r.BKS_corredores,0)} & {br(r.BKS_unidades,0)} \\\\")
    return r"""\begin{table*}[p]
\centering
\caption{Caracterização das 50 instâncias oficiais e das melhores soluções conhecidas (BKS). Todas as BKS foram verificadas com o avaliador oficial.}
\label{tab:ap_instancias}
\scriptsize
\begin{tabular}{lrrrrrrrrrrr}
\hline
\textbf{Instância} & $|\mathcal{O}|$ & $|\mathcal{I}|$ & $|\mathcal{A}|$ & $LB$ & $UB$ & \textbf{Itens/ped.} & \textbf{Corr./item} & \textbf{BKS} & \textbf{Ped. BKS} & \textbf{Corr. BKS} & \textbf{Unid. BKS} \\ \hline
""" + "\n".join(linhas) + r"""
\hline
\end{tabular}
\end{table*}
"""


def tab_redes(r: pd.DataFrame, c: pd.DataFrame) -> str:
    r = r.copy()
    r["familia"] = (c["itens_por_pedido"] == 1.0).map({True: "Um item por pedido", False: "Vários itens por pedido"}).values
    met = [
        ("Pedidos isolados (fração)", "O_itens_isolados_frac", "O_corredores_isolados_frac", None),
        ("Maior componente (fração)", "O_itens_maior_comp_frac", "O_corredores_maior_comp_frac", "A_maior_comp_frac"),
        ("Coeficiente de agrupamento", "O_itens_agrupamento", "O_corredores_agrupamento", "A_agrupamento"),
        ("Modularidade $Q$", "O_itens_modularidade", "O_corredores_modularidade", "A_modularidade"),
        ("Comunidades (não triviais)", "O_itens_comunidades", "O_corredores_comunidades", "A_comunidades"),
        ("Densidade", "O_itens_densidade", "O_corredores_densidade", "A_densidade"),
    ]
    linhas = []
    for fam, g in r.groupby("familia"):
        linhas.append(f"\\multicolumn{{4}}{{|l|}}{{\\textbf{{{fam}}} ({len(g)} instâncias)}} \\\\ \\hline")
        for nome, a, b, cc in met:
            def med(col, d=2):
                return br(g[col].median(), d) if col else "--"
            d = 0 if "Comunidades" in nome else (4 if nome == "Densidade" else 2)
            linhas.append(f"{nome} & {med(a, d)} & {med(b, d)} & {med(cc, d)} \\\\ \\hline")
    return r"""\begin{table}[hbt!]
\centering
\caption{Métricas das redes de demanda (medianas por família de instâncias). $G_O$ com $k = 10$ vizinhos.}
\label{tab:res_redes}
\resizebox{\columnwidth}{!}{%
\begin{tabular}{|l|c|c|c|}
\hline
\textbf{Métrica} & \textbf{$G_O$ (itens)} & \textbf{$G_O$ (corredores)} & \textbf{$G_A$} \\ \hline
""" + "\n".join(linhas) + r"""
\end{tabular}%
}
\end{table}
"""


def tab_heuristicas(h: pd.DataFrame) -> str:
    h = h.copy()
    h["bks"] = h.gap_pct <= 0.01
    melhor = h.groupby(["dataset", "instancia"]).razao.transform("max")
    h["melhor"] = (h.razao >= melhor - 1e-9)
    linhas = []
    for (ds, m), g in h.groupby(["dataset", "metodo"]):
        linhas.append(f"{ds} & {m} & {br(g.gap_pct.mean(),1)} & {br(g.gap_pct.median(),1)} & {int(g.bks.sum())} & "
                      f"{int(g.melhor.sum())} & {br(g.tempo_s.mean(),1)} \\\\")
        if m == "H4":
            linhas[-1] += r" \hline"
    for m, g in h.groupby("metodo"):
        linhas.append(f"Todos & {m} & {br(g.gap_pct.mean(),1)} & {br(g.gap_pct.median(),1)} & {int(g.bks.sum())} & "
                      f"{int(g.melhor.sum())} & {br(g.tempo_s.mean(),1)} \\\\")
    linhas[-1] += r" \hline"
    # melhor das heurísticas de rede (H1--H4) por instância
    rede = h[h.metodo.isin(["H1", "H2", "H3", "H4"])].groupby(["dataset", "instancia"]).agg(razao=("razao", "max"), BKS=("BKS", "first"))
    rede["gap"] = 100 * (rede.BKS - rede.razao) / rede.BKS
    linhas.append(f"Todos & Melhor de H1--H4 & {br(rede.gap.mean(),1)} & {br(rede.gap.median(),1)} & "
                  f"{int((rede.gap <= 0.01).sum())} & -- & -- \\\\ \\hline")
    return r"""\begin{table}[hbt!]
\centering
\caption{Desempenho das heurísticas construtivas nas instâncias oficiais: \textit{gap} em relação à BKS (\%), número de instâncias em que a BKS foi atingida, número de instâncias em que a heurística obteve a melhor razão entre as cinco e tempo médio (s).}
\label{tab:res_heuristicas}
\resizebox{\columnwidth}{!}{%
\begin{tabular}{|c|c|c|c|c|c|c|}
\hline
\textbf{Conj.} & \textbf{Método} & \textbf{\textit{Gap} médio} & \textbf{\textit{Gap} mediano} & \textbf{BKS} & \textbf{Melhor} & \textbf{Tempo} \\ \hline
""" + "\n".join(linhas) + r"""
\end{tabular}%
}
\end{table}
"""


def tab_heuristicas_completa(h: pd.DataFrame) -> str:
    p = h.pivot_table(index=["dataset", "instancia"], columns="metodo", values="gap_pct")
    bks = h.groupby(["dataset", "instancia"]).BKS.first()
    linhas = []
    for (ds, inst), r in p.iterrows():
        mn = r.min()
        cel = [(r"\textbf{" + br(v, 1) + "}") if abs(v - mn) < 1e-9 else br(v, 1) for v in r.values]
        linhas.append(f"{ds}-{int(inst):04d} & {br(bks[(ds, inst)], 2)} & " + " & ".join(cel) + r" \\")
    return r"""\begin{table*}[p]
\centering
\caption{\textit{Gap} (\%) de cada heurística construtiva em relação à BKS, por instância. Em negrito, o menor \textit{gap} da instância.}
\label{tab:ap_heuristicas}
\scriptsize
\begin{tabular}{lrrrrrr}
\hline
\textbf{Instância} & \textbf{BKS} & \textbf{B0} & \textbf{H1} & \textbf{H2} & \textbf{H3} & \textbf{H4} \\ \hline
""" + "\n".join(linhas) + r"""
\hline
\end{tabular}
\end{table*}
"""


def tab_zalando(z: pd.DataFrame) -> str:
    z = z.copy()
    z["porte"] = z.instancia.str.split("-").str[0]
    melhor = z.groupby("instancia").razao.transform("max")
    z["rel"] = 100 * (melhor - z.razao) / melhor
    linhas = []
    for (porte, m), g in z.groupby(["porte", "metodo"], sort=False):
        linhas.append(f"{ {'small': 'Pequena', 'medium': 'Média', 'large': 'Grande'}[porte]} & {m} & {br(g.razao.mean(),2)} & {br(g.rel.mean(),1)} & "
                      f"{int((g.rel <= 1e-9).sum())} & {br(g.corredores.mean(),0)} & {br(g.tempo_s.mean(),1)} \\\\")
        if m == "H4":
            linhas[-1] += r" \hline"
    return r"""\begin{table}[hbt!]
\centering
\caption{Heurísticas construtivas nas instâncias convertidas da Zalando (médias de 5 instâncias por porte). Distância (\%) em relação à melhor razão obtida entre as cinco heurísticas.}
\label{tab:res_zalando}
\resizebox{\columnwidth}{!}{%
\begin{tabular}{|c|c|c|c|c|c|c|}
\hline
\textbf{Porte} & \textbf{Método} & \textbf{Razão} & \textbf{Dist. (\%)} & \textbf{Melhor} & \textbf{Corredores} & \textbf{Tempo (s)} \\ \hline
""" + "\n".join(linhas) + r"""
\end{tabular}%
}
\end{table}
"""


if __name__ == "__main__":
    pasta, saida = Path(sys.argv[1]), Path(sys.argv[2])
    c = pd.read_csv(pasta / "instancias_caracterizacao.csv")
    r = pd.read_csv(pasta / "redes_caracterizacao.csv")
    h = pd.read_csv(pasta / "heuristicas_resultados.csv")
    partes = [tab_instancias_resumo(c), tab_redes(r, c), tab_heuristicas(h)]
    zal = pasta / "heuristicas_zalando.csv"
    if zal.exists():
        partes.append(tab_zalando(pd.read_csv(zal)))
    Path(saida).write_text("\n".join(partes), encoding="utf-8")
    Path(str(saida).replace(".tex", "_apendice.tex")).write_text(
        tab_instancias_completa(c) + "\n" + tab_heuristicas_completa(h), encoding="utf-8")
    print("ok")
