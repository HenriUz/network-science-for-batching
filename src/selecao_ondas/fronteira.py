"""Fronteira aproximada (max U, min |A'|) a partir da trajetória do descascamento.

Para cada tamanho k de onda, guarda as maiores unidades viáveis com no máximo k corredores.
Uso: python fronteira.py <instancia.txt> <saida.csv>
"""
import csv
import sys

import numpy as np

from heuristicas import Nucleo
from instancia import avaliar, ler_instancia


def trajetoria(n: Nucleo, frac=0.05, limiar=60):
    atual = np.flatnonzero(np.diff(n.S.indptr) > 0)
    pontos = []
    while len(atual) > 0:
        ped, U = n.selecionar(list(atual))
        if U < n.lb:
            break
        cor = n.decodificar(ped, permitidos=list(atual))
        if cor:
            ok, _, _ = avaliar(n.inst, ped, cor)
            if ok:
                pontos.append((len(cor), U))
        demanda = np.asarray(n.D[ped].sum(axis=0)).ravel()
        Ssub = n.S[atual].tocsr()
        dados = np.minimum(Ssub.data, demanda[Ssub.indices])
        contrib = np.add.reduceat(dados, Ssub.indptr[:-1])
        contrib[np.diff(Ssub.indptr) == 0] = 0
        r = max(1, int(frac * len(atual))) if len(atual) > limiar else 1
        atual = np.delete(atual, np.argsort(contrib, kind="stable")[:r])
    # envoltória não dominada: para cada k, maior U com |A'| <= k
    pontos.sort()
    frente, melhor_U = [], -1
    for k, U in pontos:
        if U > melhor_U:
            frente.append((k, U))
            melhor_U = U
    return frente


if __name__ == "__main__":
    inst = ler_instancia(sys.argv[1])
    frente = trajetoria(Nucleo(inst))
    with open(sys.argv[2], "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["corredores", "unidades", "razao"])
        for k, U in frente:
            w.writerow([k, U, round(U / k, 4)])
    for k, U in frente:
        print(k, U, round(U / k, 2))
