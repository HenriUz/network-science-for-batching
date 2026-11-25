# Ablação de métricas para priorizar corredores na H3

Este diretório reúne os resultados de um experimento que pergunta se a escolha
de corredores da heurística H3 melhora ao substituir a força ponderada por
outras medidas de rede. O objetivo aqui é documentar o que cada arquivo contém,
como os números foram produzidos e o que se pode concluir deles.

## Pergunta experimental

H3 começa com cinco corredores-semente escolhidos pelo mesmo critério em todas
as variantes. Depois, acrescenta corredores e avalia as ondas candidatas com o
mesmo seletor de pedidos, decodificador e verificação de viabilidade. A
ablação altera **somente a regra que prioriza o próximo corredor**:

| Nome usado nos CSVs | Regra de prioridade | Intuição |
|---|---|---|
| `forca_local` | Soma dos pesos das ligações entre o candidato e os corredores já abertos. | Favorece corredores fortemente relacionados à onda parcial. É o critério original da H3. |
| `grau_local` | Número de ligações do candidato aos corredores já abertos, ignorando os pesos. | Favorece a quantidade de conexões locais, não sua intensidade. |
| `forca` | Soma dos pesos de todas as ligações incidentes no corredor em `G_A`. | Favorece corredores com alta força total na rede. |
| `grau` | Número de vizinhos do corredor em `G_A`. | Favorece corredores ligados a muitos outros, independentemente do peso. |
| `pagerank` | PageRank ponderado de `G_A`. | Favorece corredores ligados a outros corredores que também são importantes. |
| `k_core` | Número de núcleo do corredor em `G_A`. | Favorece corredores pertencentes a regiões densas e coesas da rede. |

Todas as variantes mantêm o mesmo objetivo: maximizar unidades atendidas por
corredor, respeitando a cobertura por item e os limites `LB` e `UB`. Uma
solução sem viabilidade seria registrada com razão zero, mas esse caso não
ocorreu nas seis variantes das instâncias locais.

## Arquivos

| Arquivo | Conteúdo | Como interpretar |
|---|---|---|
| `metricas_por_instancia.csv` | Uma linha por instância e critério de H3 nas 20 instâncias locais. Inclui razão, unidades, quantidade de corredores, tempo e perfil de centralidade dos corredores da solução. | Use este arquivo para ver casos específicos, comparar as seis regras dentro da mesma instância e investigar exceções à média. |
| `resumo_metricas.csv` | Resumo agregado das 20 instâncias locais por regra. Inclui soluções viáveis, razão média/mediana, vitórias/empates/derrotas contra H3 original, teste pareado e perfil dos corredores selecionados. | É a síntese principal da comparação local. `p_wilcoxon_holm_vs_forca_local` corrige as cinco comparações alternativas pelo método de Holm. |
| `correlacao_centralidades.csv` | Correlação de Spearman entre os rankings de grau, força, PageRank e `k_core` dos corredores, por instância, resumida por mediana e média. | Correlações altas indicam que duas métricas tendem a ordenar os corredores de modo parecido; isso ajuda a explicar quando uma métrica nova traz pouca informação adicional. Uma instância com valor constante pode não contribuir para determinada correlação. |
| `verificacao_bks_oficial.csv` | Conferência individual das 50 soluções BKS oficiais com o avaliador do projeto. | `BKS_viavel=True` e `BKS_confere=True` confirmam que a solução atende às restrições e reproduz o objetivo publicado no CSV de referência. |
| `oficial/metricas_por_instancia.csv` | Comparação das seis regras de H3 em cada instância oficial, com a BKS, o gap percentual e indicação de igualdade com a BKS. | Para cada instância, compare os critérios à linha de `forca_local`; a BKS é uma referência externa de qualidade. |
| `oficial/resumo_metricas.csv` | Resultados agregados nas 50 instâncias oficiais. | Resume viabilidade, razão, gap médio/mediano para a BKS, número de BKS atingidas e comparação pareada com H3 original. |
| `oficial/resumo_por_conjunto.csv` | Mesmo resumo, separado em A, B e X. | Mostra se o comportamento agregado é consistente entre os três conjuntos; cada grupo tem apenas 15 ou 20 instâncias. |

Os três arquivos dentro de `oficial/` são gerados pelo mesmo script que produz
os resultados locais, mas usam as instâncias e objetivos oficiais. A execução
concluída contém 300 linhas detalhadas: seis critérios em cada uma das 50
instâncias.

## Campos importantes nos CSVs

| Campo | Definição |
|---|---|
| `razao` | Unidades da solução divididas pelo número de corredores usados. Maior é melhor entre soluções viáveis da mesma instância. |
| `BKS` | Melhor objetivo conhecido publicado para a instância. |
| `gap_pct` | `100 × (BKS − razão da heurística) / BKS`. Gap 0 significa que atingiu a BKS; gap positivo indica distância abaixo dela; gap negativo significa que a heurística superou o valor de referência e requer verificação antes de qualquer atualização da BKS. |
| `atingiu_BKS` | Indica igualdade entre o objetivo calculado e a BKS, com tolerância numérica de `1e-6`. |
| `*_percentil_medio_selecionado` | Percentil médio da centralidade dos corredores da solução na distribuição de todos os corredores daquela instância. |
| `*_fracao_top10_selecionada` | Fração dos corredores selecionados que está no décimo superior daquela centralidade. Por exemplo, `0,70` significa 70% dos corredores da solução entre os 10% de maior escore. |
| `vitorias/empates/derrotas_vs_forca_local` | Comparação pareada da razão por instância em relação à H3 original. |
| `p_wilcoxon_bruto_vs_forca_local` | Valor-p bruto do teste bilateral de Wilcoxon sobre a razão da solução, pareado por instância e calculado apenas quando ambas as variantes são viáveis. |
| `p_wilcoxon_holm_vs_forca_local` | Correção de Holm do teste sobre a razão para as cinco alternativas; o campo aparece nos resumos locais e oficiais. |
| `p_wilcoxon_bruto_gap_vs_forca_local` | Nos resultados oficiais, valor-p bruto do teste bilateral de Wilcoxon pareado sobre o gap percentual para a BKS. Fica vazio nos resultados locais, que não têm BKS. |
| `p_wilcoxon_holm_gap_vs_forca_local` | Correção de Holm dos testes de gap para as cinco alternativas oficiais. Use esse campo para avaliar diferenças estatísticas na distância relativa à BKS. |
| `rho_mediana` | Mediana, entre instâncias, da correlação de ranking de Spearman entre as duas centralidades. Próximo de 1 significa rankings semelhantes; próximo de 0, pouca associação monotônica. |

## Síntese dos 20 arquivos locais

Todas as seis regras produziram soluções viáveis em 20/20 instâncias. A
força total teve razão média 109,42, contra 106,16 da força local original
(+3,1% na média); PageRank teve 108,59 (+2,3%). Porém, ambas venceram em
apenas seis instâncias, empataram em seis e perderam em oito; a diferença
mediana pareada foi zero. Os valores-p de Holm foram 1,000. Portanto, a
pequena vantagem das médias não demonstra superioridade consistente nem
significativa.

O grau local teve média 93,93; grau global, 93,21; e `k_core`, 94,66. Os
valores-p brutos para grau e `k_core` foram 0,026, mas subiram para 0,131 após
a correção de Holm. Assim, também não há diferença estatisticamente
significativa a 5% depois de considerar as cinco comparações. O padrão sugere
que ignorar a intensidade dos pesos pode perder informação útil, mas esta
amostra não basta para concluir que grau ou `k_core` sejam sempre piores.

O perfil das soluções ajuda a interpretar o efeito. A variante PageRank
selecionou corredores no percentil médio 0,923 de PageRank; 77,8% dos
corredores selecionados estavam no décimo superior dessa métrica. A variante
de força total colocou 79,2% dos corredores selecionados no décimo superior
de força. Isso confirma que os critérios realmente direcionam a busca para
corredores de maior centralidade. Ao mesmo tempo, os rankings de força e
PageRank são muito semelhantes: a correlação de Spearman mediana entre eles
foi 0,939. PageRank pode, portanto, estar recuperando boa parte do sinal já
capturado pela força ponderada, em vez de acrescentar informação independente.

Grau e `k_core` também são correlacionados (rho mediano 0,896). `k_core` é
uma medida inteira e pode empatar muitos corredores; na solução da variante
`k_core`, em média, somente 8,5% dos corredores ficaram no décimo superior
do `k_core`. Isso sugere baixa capacidade discriminativa nessa configuração,
não que regiões coesas sejam irrelevantes em qualquer grafo.

## Resultados oficiais e BKS

As instâncias oficiais A, B e X e o CSV de objetivos foram obtidos do
[repositório do desafio Mercado Livre](https://github.com/mercadolibre/challenge-sbpo-2025).
Antes de comparar a ablação, as 50 soluções BKS foram lidas e reavaliadas: as
50 passaram a verificação de viabilidade e reproduziram seus objetivos.

O experimento oficial aplica os mesmos seis critérios de H3 às mesmas 50
instâncias. A razão é comparada à BKS por instância; o gap médio e mediano é
calculado com a fórmula definida acima. Os resumos por A, B e X são
descritivos. A comparação inferencial usa o teste pareado de Wilcoxon sobre
os gaps percentuais por instância, com correção de Holm para as cinco
alternativas. Vitórias, empates e derrotas comparam os objetivos obtidos,
sem normalização. Os resultados oficiais devem ser interpretados
separadamente dos resultados locais: estes últimos não têm proveniência
confirmada nem BKS.

Todas as regras encontraram solução viável em 50/50 instâncias. A força local
original atingiu a BKS em oito instâncias, com gap médio de 11,67% e mediano
de 8,44%. Força total e PageRank também atingiram a BKS em oito casos, mas
tiveram gaps médios maiores: 13,57% e 14,33%. Os testes pareados dos gaps
percentuais normalizados pela BKS não foram significativos depois da correção
de Holm: $p=0,708$ para força total e PageRank. Logo, as duas métricas
preservam desempenho próximo, mas não mostram melhora sobre o H3 original.

| Prioridade | Gap médio | Gap mediano | Atingiu BKS | Vitórias–empates–derrotas vs. H3 original | $p$ de Holm (gap) |
|---|---:|---:|---:|---:|---:|
| Força local ponderada (H3 original) | 11,67% | 8,44% | 8/50 | — | — |
| Força total | 13,57% | 8,92% | 8/50 | 23–8–19 | 0,708 |
| PageRank | 14,33% | 9,23% | 8/50 | 21–9–20 | 0,708 |
| Grau local | 32,39% | 31,71% | 6/50 | 5–6–39 | $6,20\times10^{-7}$ |
| Grau global | 32,91% | 31,83% | 5/50 | 5–5–40 | $3,20\times10^{-7}$ |
| $k$-core | 36,30% | 35,52% | 6/50 | 3–5–42 | $1,36\times10^{-7}$ |

Grau local, grau global e $k$-core tiveram desempenho significativamente
inferior à força local na comparação pareada, mesmo após Holm. A conclusão é
específica a esta H3 e a estas instâncias: esses rankings topológicos
isolados não representam tão bem a combinação de cobertura de demanda e
economia de corredores que define o objetivo. Um corredor muito conectado
pode estar relacionado a muitos outros sem necessariamente fornecer os itens
mais úteis para a onda.

| Prioridade | Gap médio no conjunto A | Gap médio no B | Gap médio no X |
|---|---:|---:|---:|
| Força local ponderada (H3 original) | 12,86% | 10,77% | 10,97% |
| Força total | 16,19% | 10,88% | 12,76% |
| PageRank | 16,40% | 12,32% | 13,58% |
| Grau local | 22,03% | 38,69% | 39,90% |
| Grau global | 30,60% | 34,60% | 34,31% |
| $k$-core | 31,44% | 39,31% | 39,79% |

Nos conjuntos B e X, força total ficou muito próxima da regra original; em A,
o gap dela foi maior. PageRank teve gap acima do original nos três conjuntos.
Já os três critérios baseados em grau ou $k$-core pioraram em todos os
conjuntos, especialmente B e X. Os grupos têm somente 15 ou 20 instâncias;
por isso, os valores por grupo são descritivos, não testes de superioridade
separados.

As centralidades ajudam a explicar esse padrão. Na variante PageRank, 83,7%
dos corredores finais ficaram no décimo superior de PageRank; na variante de
força total, 85,6% ficaram no décimo superior de força. Portanto, os rankings
estão influenciando a seleção como esperado. Ainda assim, a força local
original alcançou menor gap: o fato de selecionar corredores de alta
centralidade, por si só, não garante uma onda melhor. Além disso, força e
PageRank têm correlação mediana de ranking 0,939, então PageRank tende a
reordenar de forma semelhante os corredores, sem acrescentar um sinal
independente forte.

O grau global também escolheu corredores de grau alto (67,2% dos corredores
finais no décimo superior de grau), mas ficou com gap médio de 32,91%. Isso é
um exemplo concreto de que um “hub” da rede não necessariamente é bom para a
função objetivo: conexões numerosas não garantem oferta útil dos itens
necessários. $k$-core teve somente 3,4% dos corredores finais no décimo
superior de $k$-core; como a métrica é inteira e gera empates, ela oferece
pouca resolução para desempatar corredores nesta representação.

## Reproduzir

Clone o repositório oficial e rode a partir de `src/selecao_ondas`:

```bash
gh repo clone mercadolibre/challenge-sbpo-2025 /tmp/challenge-sbpo-2025
python comparar_metricas_crescimento.py \
  /tmp/challenge-sbpo-2025/datasets \
  ../../results/metricas_crescimento/oficial \
  --bks-repo /tmp/challenge-sbpo-2025
```

O script valida cada solução produzida com o avaliador interno antes de
calcular seu gap para a BKS. Para repetir o experimento local, use
`../../dataset` como primeiro argumento e omita `--bks-repo`.

## Limitações e próximos passos

- As 20 instâncias locais não têm procedência oficial confirmada; a comparação
  com BKS oficial é a análise principal para decidir se os resultados se
  generalizam.
- Há uma execução determinística por critério e instância; os resultados
  representam esta configuração da heurística, não a variabilidade de
  diferentes sementes.
- A H3 usa sempre a mesma estratégia para selecionar sementes; a ablação muda
  apenas a prioridade dos corredores adicionados depois.
- A centralidade dos corredores selecionados é uma descrição associativa.
  Ela não prova que a métrica causou a melhora ou piora da razão.
- Um próximo experimento independente é comparar Leiden/Louvain em projeções
  ponderadas e binárias, mantendo a avaliação operacional de H2/H4. Outra
  linha é usar centralidades no critério de remoção do descascamento H1.
