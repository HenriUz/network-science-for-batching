# Seleção de pedidos e corredores por onda guiada por ciência de redes

Código do TCC de Nikolas Pires (UNIFEI), *Order Batching e Análise de Redes*. Ele cobre a
caracterização das instâncias, o gerador de grafos de demanda, as métricas de rede e as
heurísticas construtivas para o modelo monoobjetivo do Primeiro Desafio de Otimização do
Mercado Livre (SBPO 2025): maximizar unidades coletadas ÷ corredores visitados, com o
total de unidades da onda entre `LB` e `UB`.

A pasta é independente do restante do repositório: não importa nem altera `src/process`
ou `src/methods`.

## Relação com o restante do repositório

`src/methods/similarity.py` liga dois pedidos por itens em comum (`common_items`) ou pelo
Jaccard dos corredores tocados (`common_aisles`). Aqui a projeção pedido–pedido usa a
afinidade por corredores com o peso de Adamic–Adar, que reduz o peso de corredores que
atendem quase todos os pedidos. Ela é esparsificada pelos `k` vizinhos mais afins, o que
permite processar as 50 instâncias oficiais (até 68 mil pedidos) em no máximo cerca de 30 s.
Também são construídos o grafo bipartido pedido–corredor e a projeção corredor–corredor,
usados pelas heurísticas.

## Requisitos

```
pip install -r src/selecao_ondas/requirements.txt
```

As instâncias completas (conjuntos A, B e X) e as melhores soluções conhecidas (BKS) vêm do
repositório oficial, que não é copiado para cá:

```
git clone https://github.com/mercadolibre/challenge-sbpo-2025
```

## Arquivos

| Arquivo | O que faz |
|---|---|
| `instancia.py` | Lê instâncias e soluções no formato oficial; avalia viabilidade e objetivo com a mesma lógica do `checker.py` oficial. |
| `grafos.py` | Gerador de grafos: pedido–item, item–corredor, pedido–corredor, projeção pedido–pedido (afinidade por itens, por corredores ou combinada, com `k` vizinhos) e projeção corredor–corredor; métricas de rede (densidade, componentes, agrupamento, modularidade por Leiden). |
| `heuristicas.py` | Seletor de pedidos, decodificador de corredores e as heurísticas B0 (sem rede), H1 (descascamento), H2 (comunidades de pedidos), H3 (crescimento guiado pela rede de corredores) e H4 (comunidades de corredores). |
| `caracterizar_instancias.py` | Id, quantitativos e BKS das 50 instâncias, verificando cada BKS. |
| `caracterizar_redes.py` | Métricas de rede de todas as instâncias. |
| `rodar_heuristicas.py` | Executa as cinco heurísticas e calcula o *gap* em relação à BKS. |
| `fronteira.py` | Fronteira aproximada unidades × corredores (modelo biobjetivo) pela trajetória do descascamento. |
| `converter_zalando.py`, `rodar_zalando.py` | Conversão das instâncias da Zalando (Abelli et al., 2024) para o formato do desafio e execução das heurísticas. |
| `dicionario_dados_zalando.md` | Dicionário de dados das instâncias da Zalando. |
| `dicionario_dados_datasets.md` | Dicionário conjunto: formato oficial Mercado Livre, arquivos locais e dados originais e convertidos da Zalando. |
| `gerar_tabelas.py` | Tabelas LaTeX do texto a partir dos CSVs. |
| `desenhar_grafos.py` | Figura dos grafos de demanda (instâncias A-0001 e A-0017). |
| `comparar_comunidades.py` | Compara Leiden e Louvain em G_O e G_A, incluindo modularidade, tamanhos e NMI. |
| `comparar_metricas_crescimento.py` | Ablation de critérios de H3: força/grau locais e rankings por força, grau, PageRank e k-core; mede viabilidade, razão e perfil de centralidade dos corredores selecionados. |
| `results/metricas_crescimento/README.md` | Dicionário dos arquivos da ablação, método de comparação, síntese dos resultados e instruções para reproduzi-los com as instâncias oficiais e BKS. |

## Uso

Os comandos abaixo são executados a partir de `src/selecao_ondas`:

```
REPO=caminho/para/challenge-sbpo-2025

# grafos de uma instância (salva .npz)
python grafos.py $REPO/datasets/a/instance_0005.txt --afinidade corredores --k 10 --salvar grafos

# caracterização, redes e heurísticas
python caracterizar_instancias.py $REPO resultados/instancias_caracterizacao.csv
python caracterizar_redes.py $REPO/datasets resultados/redes_caracterizacao.csv 10
python rodar_heuristicas.py $REPO resultados/heuristicas_resultados.csv        # ~40 min em 2 núcleos
python rodar_heuristicas.py $REPO resultados/heuristicas_x.csv x               # um conjunto só

# comparação controlada de comunidades em uma instância
python comparar_comunidades.py $REPO/datasets/a/instance_0005.txt resultados/comunidades.csv 10

# ablação de métricas para priorizar corredores na H3
python comparar_metricas_crescimento.py ../../dataset resultados/metricas_crescimento

# caracterização estrutural com centralidades
python caracterizar_redes.py $REPO/datasets resultados/redes.csv 10 --centralidades
# incluir betweenness também (mais caro):
python caracterizar_redes.py $REPO/datasets resultados/redes.csv 10 --centralidades --betweenness

# fronteira e figura
python fronteira.py $REPO/datasets/a/instance_0005.txt resultados/fronteira_a5.csv
python desenhar_grafos.py $REPO resultados/grafos_demanda

# Zalando (https://github.com/zalandoresearch/batching-benchmarks; descompactar instances.zip)
python converter_zalando.py instancias_zalando zalando_convertidas
python rodar_zalando.py zalando_convertidas resultados/heuristicas_zalando.csv small medium

# tabelas LaTeX
python gerar_tabelas.py resultados resultados/tabelas_resultados.tex
```

O experimento de ablação mantém a mesma heurística de crescimento e varia
somente a regra de priorização do próximo corredor. `forca_local` é o H3
original (soma de pesos das conexões com corredores já abertos); `grau_local`
conta vizinhos já abertos sem pesos; `forca`, `grau`, `pagerank` e `k_core`
usam rankings globais dos corredores. O CSV detalhado também reporta o
percentil médio e a fração entre os 10% de maior centralidade dos corredores
da solução. O resumo compara as razões pareadas pelo teste de Wilcoxon e
corrige os valores-p pelo método de Holm. Essas estatísticas ajudam a
interpretar o perfil selecionado, mas não devem ser interpretadas como
causalidade. Os 20 arquivos locais não têm procedência oficial confirmada;
valide as hipóteses também nas instâncias oficiais antes de generalizar.

## Resultados

A pasta `resultados/` traz as saídas usadas no texto. Nas 50 instâncias oficiais, o
descascamento (H1) teve *gap* médio de 6,0% em relação à BKS e atingiu a BKS em 14 delas; a
referência sem rede (B0) teve 22,3%. As heurísticas são determinísticas (Leiden com semente
fixa), de modo que uma nova execução reproduz os mesmos valores de razão; apenas os tempos variam.
