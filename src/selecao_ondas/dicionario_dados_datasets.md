# Dicionário de dados dos conjuntos experimentais

Este documento descreve os dados do desafio Mercado Livre, as 20 instâncias
locais usadas em análises exploratórias e o benchmark público de Zalando, tanto
em seu formato original quanto após a conversão para o formato do desafio.
Esses três conjuntos não devem ser confundidos: em particular, as instâncias
locais do repositório não têm proveniência oficial confirmada.

## 1. Conceitos e notação do formato do desafio

O modelo usa três conjuntos:

| Símbolo | Entidade | Significado |
|---|---|---|
| $\mathcal{O}$ | Pedido | Um pedido de cliente, formado por quantidades de itens. |
| $\mathcal{I}$ | Item | Um tipo de produto/SKU. |
| $\mathcal{A}$ | Corredor | Uma localização ou agrupamento de estoque que pode fornecer itens. |

Para cada pedido $o$ e item $i$, $u_{oi}$ é a quantidade demandada. Para cada
corredor $a$ e item $i$, $u_{ai}$ é a quantidade ofertada. Uma onda seleciona
subconjuntos $\mathcal{O}'$ e $\mathcal{A}'$. A demanda selecionada precisa ser
coberta item a item pela oferta dos corredores selecionados:

$$
\sum_{o\in\mathcal{O}'}u_{oi}\leq\sum_{a\in\mathcal{A}'}u_{ai}
\quad\forall i\in\mathcal{I}.
$$

O total de unidades atendidas deve estar entre $LB$ e $UB$, e a função objetivo
é o número de unidades atendidas dividido pelo número de corredores visitados.
Os arquivos codificam quantidades esparsas: pares de itens com quantidade zero
não são gravados.

## 2. Mercado Livre — formato oficial do desafio

### Fonte e escopo

O conjunto oficial é distribuído pelo
[repositório do Primeiro Desafio Mercado Livre de Otimização](https://github.com/mercadolibre/challenge-sbpo-2025).
Os experimentos principais do artigo consideram 50 instâncias dos conjuntos
A, B e X, com comparação às melhores soluções conhecidas (BKS). Os arquivos
oficiais completos e as BKS não estão copiados neste repositório local.

### Organização do arquivo texto

Cada instância é um arquivo de texto sem cabeçalho de colunas. As linhas são
interpretadas nesta ordem:

| Posição | Conteúdo | Quantidade de linhas |
|---|---|---:|
| 1 | `O I A`: número de pedidos, itens e corredores | 1 |
| 2 até `O+1` | Uma linha por pedido | `O` |
| `O+2` até `O+A+1` | Uma linha por corredor | `A` |
| última | `LB UB`: limites inferior e superior de unidades | 1 |

Assim, um arquivo bem formado tem `O + A + 2` linhas de conteúdo. O identificador
do pedido e o do corredor são implícitos pela ordem das linhas: a primeira
linha de pedido corresponde ao pedido 0 e a primeira linha de corredor ao
corredor 0. Os itens são identificados explicitamente por índices inteiros,
normalmente entre 0 e `I-1`.

### Campos das linhas de pedido e corredor

Uma linha de pedido ou corredor tem a forma:

```text
k item_1 quantidade_1 item_2 quantidade_2 ... item_k quantidade_k
```

| Campo | Tipo | Significado |
|---|---|---|
| `k` | Inteiro não negativo | Número de tipos de item distintos com quantidade positiva nessa linha. Não é o número total de unidades. |
| `item_j` | Índice inteiro | Identificador do item, no universo declarado pela segunda contagem do cabeçalho. |
| `quantidade_j` | Inteiro positivo | Quantidade demandada do item na linha de pedido, ou quantidade ofertada na linha de corredor. |

Cada linha tem `1 + 2k` inteiros. Um pedido que contém três unidades do
mesmo item é representado por um único par para esse item, por exemplo
`1 7 3`; um pedido com dois itens distintos pode ser `2 7 3 12 1`.

O cabeçalho é seguido primeiro por todas as linhas de pedido e só depois por
todas as linhas de corredor. Portanto, o mesmo par de índices de item tem
significados diferentes conforme a seção: demanda em uma linha de pedido e
estoque em uma linha de corredor.

### Exemplo didático

O exemplo abaixo é inventado para explicar o formato; não é uma instância
oficial:

```text
2 3 2
2 0 1 2 2
1 1 1
2 0 2 1 1
2 1 2 2 1
1 4
```

Interpretação:

1. `2 3 2`: há 2 pedidos, 3 itens (`0`, `1`, `2`) e 2 corredores (`0`, `1`).
2. `2 0 1 2 2`: pedido 0 demanda 1 unidade do item 0 e 2 unidades do item 2.
3. `1 1 1`: pedido 1 demanda 1 unidade do item 1.
4. `2 0 2 1 1`: corredor 0 oferece 2 unidades do item 0 e 1 do item 1.
5. `2 1 2 2 1`: corredor 1 oferece 2 unidades do item 1 e 1 do item 2.
6. `1 4`: uma onda válida deve atender entre 1 e 4 unidades, além de respeitar
   a cobertura item a item.

Um arquivo local real, `dataset/instance_0001.txt`, começa pelo cabeçalho
`61 155 116`: 61 pedidos, 155 índices de item e 116 corredores. Sua primeira
linha de pedido é `3 13 1 36 1 135 1`, isto é, três itens distintos, cada um
com uma unidade. Sua última linha é `30 68`, os limites da instância.

### Matrizes usadas pelo código

O leitor [instancia.py](./instancia.py) transforma o arquivo em duas matrizes
esparsas:

| Matriz | Dimensão | Entrada |
|---|---|---|
| `D` | `O × I` | `D[o,i] = u_oi`: demanda do item `i` pelo pedido `o`. |
| `S` | `A × I` | `S[a,i] = u_ai`: oferta do item `i` no corredor `a`. |

As matrizes não armazenam entradas zero. O valor total de um pedido é a soma
de sua linha em `D`; a oferta agregada de um conjunto de corredores é a soma
das linhas correspondentes em `S`.

## 3. Arquivos locais no formato Mercado Livre

O diretório `dataset/` deste repositório contém 20 arquivos
`instance_0001.txt` a `instance_0020.txt`. Eles seguem a estrutura texto
descrita acima e são lidos pelo mesmo parser. Contudo, sua procedência não foi
confirmada por checksum; portanto, não devem ser chamados de uma cópia
verificada do conjunto oficial A, nem usados como se tivessem BKS oficial.

Nos 20 arquivos observados, as dimensões variam entre:

| Quantidade | Mínimo observado | Máximo observado |
|---|---:|---:|
| Pedidos (`O`) | 5 | 12.402 |
| Itens (`I`) | 5 | 10.974 |
| Corredores (`A`) | 5 | 413 |
| Limite inferior (`LB`) | 0 | 1.947 |
| Limite superior (`UB`) | 2 | 7.739 |

Esses intervalos descrevem apenas os arquivos locais presentes; não são a
especificação de tamanho dos conjuntos oficiais A, B ou X.

## 4. Zalando — instâncias originais

### Fonte, tamanho e natureza

O benchmark acompanha o artigo de Abelli et al., *Joint Order Selection,
Allocation, Batching and Picking for Large Scale Warehouses*, e está no
[repositório batching-benchmarks](https://github.com/zalandoresearch/batching-benchmarks)
(licença MIT). O ZIP contém 15 instâncias geradas, cinco de cada porte. Não
são logs de transações ou pedidos reais de clientes. O repositório declara
que são as instâncias usadas nos resultados da publicação.

| Porte | Pedidos | Artigos | Unidades físicas em estoque | Zonas |
|---|---:|---:|---:|---:|
| Pequeno (`small`) | 500 | 3.333 | 10.000 | 10 |
| Médio (`medium`) | 5.000 | 33.333 | 100.000 | 50 |
| Grande (`large`) | 50.000 | 333.333 | 1.000.000 | 100 |

Os tamanhos acima são parâmetros do gerador. Uma instância original é uma
pasta com quatro arquivos JSON.

### `articles.json` — catálogo de artigos

| Campo | Tipo | Significado |
|---|---|---|
| `id` | Texto | Identificador do artigo/SKU. |
| `volume` | Número positivo | Volume unitário do artigo, usado no limite de volume do problema original; o gerador o sorteia de uma distribuição Gamma com parâmetros 2 e 20 e aplica piso mínimo 1. |

### `warehouse_items.json` — estoque físico

Cada objeto representa uma unidade física em estoque, não uma linha agregada
por produto.

| Campo | Tipo | Significado |
|---|---|---|
| `id` | Texto | Identificador da unidade física. |
| `article` | Texto | SKU armazenado, referenciando `articles.json`. |
| `zone` | Texto | Zona do armazém. |
| `aisle` | Inteiro | Coordenada/identificador do corredor dentro da zona. Nos dados gerados, valores de -48 a 49 são usados, exceto 0. |
| `row` | Inteiro | Posição ao longo do corredor. Nos dados gerados, valores de -48 a 49 são usados, exceto 0. |

No problema original, zona e posição são relevantes para formar listas de
coleta e calcular roteamento. A coordenada 0 representa corredores
transversais, onde não há estoque. A conversão deste trabalho usa apenas parte
dessa informação.

### `orders.json` — pedidos

| Campo | Tipo | Significado |
|---|---|---|
| `id` | Texto | Identificador original do pedido. |
| `positions` | Lista de textos | Lista de SKUs pedidos, com uma entrada por unidade. Repetições representam múltiplas unidades do mesmo artigo. |

Por exemplo, `["sku-A", "sku-B", "sku-A"]` significa duas unidades de
`sku-A` e uma de `sku-B`.

### `parameters.json` — parâmetros do problema original

| Campo | Interpretação no benchmark original |
|---|---|
| `min_number_requested_items` | Número mínimo de unidades que a solução original deve coletar; definido como 20% das posições totais. |
| `max_orders_per_batch` | Limite de pedidos por lote, 50. |
| `max_container_volume` | Volume máximo por contêiner/lista de coleta, 1.000. |
| `first_row`, `last_row` | Limites da coordenada de linha no armazém. |
| `first_aisle`, `last_aisle` | Limites da coordenada de corredor. |

### Geração dos dados

O gerador distribui unidades de estoque por artigo, zona, corredor e posição;
zona, corredor e posição são sorteados independentemente e uniformemente. Os
artigos pedidos são retirados do estoque disponível, de modo que a demanda
total não excede a oferta total. Cada pedido tem de 2 a 6 posições; os pesos
relativos usados para esses cinco tamanhos são 100, 50, 20, 5 e 2,
respectivamente. A geração não estabelece correlação planejada entre os
artigos dos pedidos. Assim, o benchmark permite testar escala e uma
distribuição sintética diferente, mas não modela necessariamente padrões
reais de compra.

## 5. Conversão de Zalando para o formato do desafio

A conversão é feita por
[converter_zalando.py](./converter_zalando.py). Ela produz um arquivo de texto
com o mesmo esquema `O I A` / linhas de pedido / linhas de corredor / `LB UB`
descrito na Seção 2. O script lê `orders.json` e `warehouse_items.json`;
não lê `articles.json` nem `parameters.json`. Os SKUs são obtidos pela união
dos identificadores de artigo encontrados nos pedidos e no estoque.

| Conceito no arquivo do desafio | Origem em Zalando | Operação |
|---|---|---|
| Pedido | Objeto de `orders.json` | Cada pedido vira uma linha; o `id` original é substituído pelo índice da linha. |
| Item | `article` em estoque e SKUs em `positions` | Forma-se a união dos SKUs encontrados em pedidos e estoque, ordena-se e atribui-se um índice inteiro. |
| Demanda `u_oi` | `orders[].positions` | Conta-se quantas vezes cada SKU aparece no pedido. Repetições viram a quantidade desse item. |
| Corredor | Par `(zone, aisle)` de `warehouse_items.json` | Cada par distinto vira um corredor e recebe índice inteiro. O `aisle` sozinho não é usado porque pode se repetir em zonas diferentes. |
| Oferta `u_ai` | Unidades de `warehouse_items.json` | Conta-se quantas unidades de cada SKU existem em cada par `(zone, aisle)`. |
| `LB`, `UB` | Demanda total convertida `D` | `LB = round(0,105 × D)` e `UB = round(0,378 × D)`, com `round` do Python. |

Passos da conversão:

1. Carregar pedidos e unidades de estoque.
2. Criar uma tabela de índices de itens a partir da união ordenada dos SKUs
   demandados e estocados.
3. Criar uma tabela de índices de corredores a partir dos pares ordenados
   `(zone, aisle)`.
4. Para cada pedido, contar as ocorrências de cada SKU em `positions`.
5. Para cada corredor, contar unidades físicas por SKU.
6. Somar todas as posições de todos os pedidos para obter `D`, calcular os
   limites e gravar o arquivo no formato do desafio.

Exemplo de agregação: as posições
`["sku-A", "sku-B", "sku-A"]` viram dois pares na linha do pedido: demanda 2
para `sku-A` e 1 para `sku-B`. Se o corredor `(zone-1, -2)` tiver duas unidades
de `sku-A` e uma de `sku-B`, sua linha de oferta também terá dois pares, com
quantidades 2 e 1. O prefixo `k` em cada linha será 2 nos dois casos.

Com as frações padrão, se uma instância tiver `D = 100` posições demandadas,
os limites convertidos serão `LB = 10` e `UB = 38`. Essas frações foram
adotadas a partir das medianas das proporções usadas nas instâncias do Mercado
Livre; **não** são os limites originais do benchmark Zalando.

### Informação não preservada pela conversão

| Informação original | Tratamento na conversão |
|---|---|
| SKU do artigo | Preservado como tipo de item, mas seu ID textual é remapeado para índice inteiro. |
| `zone` | Usado para distinguir corredores junto com `aisle`; a regra operacional de selecionar uma única zona não é imposta. |
| `aisle` | Preservado apenas como parte do identificador do corredor; não é usado para distância ou roteamento. |
| `row` | Descartado; coordenadas e distâncias dentro do armazém não são modeladas. |
| `volume` do artigo | Descartado; não há restrição de volume de contêiner. |
| IDs de pedido e de unidade física | Não preservados; pedidos e corredores são indexados pela ordem das linhas e estoque é agregado. |
| `min_number_requested_items` | Substituído pelos limites 10,5% e 37,8% da demanda total. |
| `max_orders_per_batch` | Descartado; o modelo convertido não impõe máximo de 50 pedidos. |
| `max_container_volume` | Descartado; não há contêineres na variante do desafio. |
| Parâmetros de coordenadas e rota | Descartados; a função objetivo conta corredores, sem calcular distância percorrida. |

Consequentemente, os resultados da conversão são resultados no modelo de
seleção de pedidos e corredores deste trabalho sobre dados gerados por outro
benchmark. Não são uma reprodução dos algoritmos nem dos resultados do
problema original de Zalando, e não há BKS para a variante convertida.
