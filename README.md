# Ciência de Redes aplicada à formação de lotes de pedidos

Este repositório é um projeto acadêmico da UNIFEI que aplica conceitos de
Ciência de Redes ao problema de formação de lotes de pedidos (`batching`). As
instâncias estudadas vêm do Primeiro Desafio de Otimização do Mercado Livre,
realizado no LVII Simpósio Brasileiro de Pesquisa Operacional (SBPO 2025).

O objetivo do projeto é representar relações entre pedidos como uma rede e
analisar suas propriedades ao longo de atividades, apresentações e artigos. O
repositório não tem como objetivo declarado reproduzir uma solução competitiva
completa do desafio.

## Fonte e proveniência

- **Fonte declarada:** Mercado Livre.
- **Desafio:** Primeiro Desafio de Otimização do Mercado Livre — SBPO 2025.
- **Referência oficial:**
  [mercadolibre/challenge-sbpo-2025](https://github.com/mercadolibre/challenge-sbpo-2025).
- **Período e cobertura geográfica:** não informados nos arquivos locais.
- **Entidades principais:** pedidos, itens e corredores de armazenamento.

A fonte oficial organiza as entradas nos conjuntos A, B e X e informa que o
dataset A possui 20 instâncias. Os 20 arquivos deste repositório são compatíveis
com o conjunto A em quantidade e nomenclatura, mas a cópia local não registra o
commit de origem nem checksums oficiais. Portanto, essa correspondência deve ser
tratada como uma inferência, não como proveniência comprovada.

## O que cada instância representa

Cada arquivo `dataset/instance_*.txt` descreve um problema de formação de lote:

- um **pedido** contém pares `item_id -> quantidade`;
- um **item** é identificado por um inteiro no intervalo `0..I-1`;
- um **corredor** contém pares `item_id -> quantidade disponível`;
- `LB` e `UB` são os limites inferior e superior aplicados ao total de itens
  recebido pela função objetivo do parser local.

As quantidades representam unidades demandadas nos pedidos ou disponíveis nos
corredores. Elas não são usadas pelas duas funções de similaridade atualmente
implementadas; essas funções trabalham apenas com a presença dos IDs.

## Formato dos arquivos

O parser [`Problem`](src/process/dataset.py) interpreta cada instância nesta
ordem:

1. primeira linha: `O I A`, com o número de pedidos, itens e corredores;
2. próximas `O` linhas: `N item_id quantidade ...`, com `N` pares por pedido;
3. próximas `A` linhas: o mesmo formato, agora descrevendo cada corredor;
4. última linha: `LB UB`, os limites inclusivos usados pela função objetivo.

As linhas de pedidos e corredores têm comprimentos variáveis. Por isso, o TXT
bruto **não é uma matriz de adjacência** e não deve ser carregado diretamente
com `numpy.loadtxt` como uma matriz retangular.

## Inventário das instâncias

Os valores abaixo foram extraídos dos cabeçalhos e das últimas linhas dos 20
arquivos locais.

| Instância | Pedidos (`O`) | Itens (`I`) | Corredores (`A`) | `LB` | `UB` |
| --- | ---: | ---: | ---: | ---: | ---: |
| `instance_0001.txt` | 61 | 155 | 116 | 30 | 68 |
| `instance_0002.txt` | 7 | 7 | 33 | 0 | 2 |
| `instance_0003.txt` | 82 | 246 | 124 | 33 | 106 |
| `instance_0004.txt` | 16 | 59 | 91 | 4 | 40 |
| `instance_0005.txt` | 2.625 | 6.407 | 161 | 1.322 | 4.395 |
| `instance_0006.txt` | 10.341 | 7.089 | 184 | 452 | 3.892 |
| `instance_0007.txt` | 8.320 | 5.747 | 180 | 1.306 | 3.847 |
| `instance_0008.txt` | 2.185 | 5.831 | 168 | 1.304 | 2.840 |
| `instance_0009.txt` | 70 | 222 | 304 | 52 | 153 |
| `instance_0010.txt` | 1.602 | 3.689 | 383 | 416 | 1.746 |
| `instance_0011.txt` | 1.029 | 2.784 | 375 | 330 | 2.045 |
| `instance_0012.txt` | 133 | 337 | 342 | 35 | 177 |
| `instance_0013.txt` | 8.375 | 7.525 | 413 | 1.510 | 4.583 |
| `instance_0014.txt` | 12.402 | 10.974 | 413 | 1.947 | 7.739 |
| `instance_0015.txt` | 7.367 | 6.633 | 402 | 384 | 3.679 |
| `instance_0016.txt` | 1.108 | 1.051 | 88 | 149 | 686 |
| `instance_0017.txt` | 417 | 411 | 83 | 54 | 175 |
| `instance_0018.txt` | 2.682 | 2.309 | 90 | 537 | 1.205 |
| `instance_0019.txt` | 2.257 | 2.104 | 134 | 152 | 999 |
| `instance_0020.txt` | 5 | 5 | 5 | 5 | 12 |

### Resumo do conjunto local

| Característica | Valor observado |
| --- | ---: |
| Arquivos | 20 |
| Tamanho total | 2.161.477 bytes |
| Pedidos somados | 61.084 |
| Pedidos por instância | 5 a 12.402 |
| Itens por instância | 5 a 10.974 |
| Corredores por instância | 5 a 413 |

Esses números caracterizam a estrutura dos arquivos locais. Eles não comprovam
identidade com os arquivos publicados na fonte oficial nem avaliam a qualidade
semântica dos dados.

## Da instância para a rede

O fluxo usado pelo projeto é:

```text
dataset/instance_*.txt
        -> Problem
        -> função de similaridade
        -> lista de arestas ponderadas
        -> igraph.Graph
        -> matriz de adjacência esparsa
```

Na projeção atual:

- cada vértice representa um pedido;
- uma aresta não dirigida conecta dois pedidos quando a similaridade é
  diferente de zero;
- `common_items` usa como peso a quantidade de IDs de itens distintos em comum;
- `common_aisles` usa o índice de Jaccard entre os conjuntos de corredores
  tocados pelos dois pedidos;
- pesos iguais a zero não geram arestas.

As definições estão em
[`src/methods/similarity.py`](src/methods/similarity.py), e a construção do
grafo está em [`src/process/graph.py`](src/process/graph.py). O fluxo atual de
[`src/main.py`](src/main.py) usa `common_aisles`.

## Limitações conhecidas

- A rede projetada pode ser muito densa: com `O` pedidos existem até
  `O(O-1)/2` pares possíveis.
- `instance_0020.txt`, com cinco pedidos, é a menor entrada para verificações
  rápidas; `instance_0014.txt`, com 12.402 pedidos, possui 76.898.601 pares
  possíveis antes da remoção das similaridades nulas.
- As similaridades atuais ignoram quantidades demandadas, estoque e capacidade.
- A função objetivo de `Problem` recebe totais já calculados; isoladamente, ela
  não valida cobertura, capacidade ou a viabilidade completa de uma solução.
- Resultados de rede dependem da similaridade escolhida e não devem ser
  comparados sem identificar a projeção utilizada.
