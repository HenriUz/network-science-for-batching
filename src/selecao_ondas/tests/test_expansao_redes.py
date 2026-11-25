import unittest

import igraph as ig
import numpy as np
import scipy.sparse as sp

from grafos import detectar_comunidades, metricas_centralidade
from heuristicas import Nucleo, crescimento_guiado
from instancia import Instancia, avaliar


class ExpansaoRedesTest(unittest.TestCase):
    def setUp(self):
        self.grafo = ig.Graph(
            n=6,
            edges=[(0, 1), (1, 2), (0, 2), (3, 4), (4, 5), (3, 5), (2, 3)],
            directed=False,
        )
        self.grafo.es["weight"] = [3.0, 2.0, 4.0, 3.0, 2.0, 4.0, 1.0]

    def test_leiden_detecta_comunidades(self):
        particao = detectar_comunidades(self.grafo, "leiden", resolucao=1.0, semente=7)
        self.assertGreaterEqual(len(particao), 2)
        self.assertEqual(sum(particao.sizes()), self.grafo.vcount())

    def test_louvain_detecta_comunidades(self):
        particao = detectar_comunidades(self.grafo, "louvain", semente=7)
        self.assertGreaterEqual(len(particao), 2)
        self.assertEqual(sum(particao.sizes()), self.grafo.vcount())

    def test_louvain_respeita_semente(self):
        primeira = detectar_comunidades(self.grafo, "louvain", semente=7)
        segunda = detectar_comunidades(self.grafo, "louvain", semente=7)
        self.assertEqual(primeira.membership, segunda.membership)

    def test_centralidades_retorna_resumos_validos(self):
        metricas = metricas_centralidade(self.grafo, incluir_betweenness=True)
        for nome in ("grau", "forca", "betweenness", "closeness",
                     "eigenvector", "pagerank", "k_core"):
            resumo = metricas[nome]
            self.assertIn("media", resumo)
            self.assertGreaterEqual(resumo["max"], resumo["min"])

    def test_grafo_sem_arestas(self):
        grafo = ig.Graph(n=3)
        grafo.es["weight"] = []
        particao = detectar_comunidades(grafo, "louvain")
        self.assertEqual(len(particao), 3)

    def test_metricas_alternativas_de_crescimento_geram_solucoes_viaveis(self):
        D = sp.csr_matrix([[1, 0], [0, 1], [1, 1]], dtype=np.int64)
        S = sp.csr_matrix([[1, 0], [0, 1], [1, 1]], dtype=np.int64)
        inst = Instancia(
            nome="toy",
            n_pedidos=3,
            n_itens=2,
            n_corredores=3,
            pedidos=[{0: 1}, {1: 1}, {0: 1, 1: 1}],
            corredores=[{0: 1}, {1: 1}, {0: 1, 1: 1}],
            lb=1,
            ub=3,
            D=D,
            S=S,
        )
        G_A = sp.csr_matrix(
            [[0, 3, 1], [3, 0, 2], [1, 2, 0]], dtype=float
        )
        n = Nucleo(inst)
        padrao = crescimento_guiado(n, G_A, sementes=1)
        explicita = crescimento_guiado(n, G_A, sementes=1, metrica="forca_local")
        self.assertEqual(padrao.corredores, explicita.corredores)
        self.assertEqual(padrao.pedidos, explicita.pedidos)
        self.assertEqual(padrao.razao, explicita.razao)
        for metrica in (
            "forca_local",
            "grau_local",
            "forca",
            "grau",
            "pagerank",
            "k_core",
        ):
            with self.subTest(metrica=metrica):
                sol = crescimento_guiado(n, G_A, sementes=1, metrica=metrica)
                self.assertIsNotNone(sol)
                viavel, objetivo, _ = avaliar(inst, sol.pedidos, sol.corredores)
                self.assertTrue(viavel)
                self.assertAlmostEqual(objetivo, sol.razao)

    def test_crescimento_guiado_rejeita_metrica_desconhecida(self):
        inst = Instancia(
            nome="toy",
            n_pedidos=1,
            n_itens=1,
            n_corredores=1,
            pedidos=[{0: 1}],
            corredores=[{0: 1}],
            lb=1,
            ub=1,
            D=sp.csr_matrix([[1]], dtype=np.int64),
            S=sp.csr_matrix([[1]], dtype=np.int64),
        )
        with self.assertRaises(ValueError):
            crescimento_guiado(Nucleo(inst), sp.csr_matrix((1, 1)), metrica="bogus")


if __name__ == "__main__":
    unittest.main()
