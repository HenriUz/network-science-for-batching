import unittest

from comparar_metricas_crescimento import CENTRALIDADES, METRICAS, resumir


class CompararMetricasCrescimentoTest(unittest.TestCase):
    def test_compara_gaps_bks_com_wilcoxon_e_correcao_de_holm(self):
        linhas = []
        for indice in range(6):
            for metrica in METRICAS:
                razao = 100.0 if metrica == "forca_local" else 99.0
                gap = 0.0 if metrica == "forca_local" else 1.0
                linha = {
                    "instancia": f"A/instance_{indice:04d}",
                    "metrica": metrica,
                    "viavel": True,
                    "razao": razao,
                    "BKS": 100.0,
                    "gap_pct": gap,
                    "atingiu_BKS": metrica == "forca_local",
                }
                for centralidade in CENTRALIDADES:
                    linha[f"{centralidade}_percentil_medio_selecionado"] = 0.5
                    linha[f"{centralidade}_fracao_top10_selecionada"] = 0.1
                linhas.append(linha)

        resumos = {linha["metrica"]: linha for linha in resumir(linhas)}

        self.assertAlmostEqual(
            resumos["forca"]["p_wilcoxon_bruto_gap_vs_forca_local"], 0.03125
        )
        self.assertAlmostEqual(
            resumos["forca"]["p_wilcoxon_holm_gap_vs_forca_local"], 0.15625
        )
        self.assertEqual(
            resumos["forca"]["gap_medio_pct_vs_BKS"], 1.0
        )


if __name__ == "__main__":
    unittest.main()
