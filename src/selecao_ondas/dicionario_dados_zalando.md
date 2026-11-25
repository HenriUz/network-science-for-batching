# Dicionário de dados — instâncias da Zalando (Abelli et al., 2024)

Fonte: https://github.com/zalandoresearch/batching-benchmarks (licença MIT).
O repositório não traz dicionário formal; este documento foi montado a partir de
`batching_problem/definitions.py`, `batching_problem/generator.py`,
`generate_instances.py` e de uma instância real (`small-0`).

Cada instância é uma pasta com quatro arquivos JSON.

## articles.json — catálogo de artigos (produtos)

| Campo | Tipo | Significado | Exemplo |
|---|---|---|---|
| `id` | texto | Identificador do artigo (SKU) | `"article-0"` |
| `volume` | inteiro | Volume de uma unidade do artigo; sorteado de uma Gama(2, 20), mínimo 1 | `14` |

## warehouse_items.json — estoque físico (uma linha = uma unidade)

| Campo | Tipo | Significado | Exemplo |
|---|---|---|---|
| `id` | texto | Identificador da unidade física | `"warehouse-item-0"` |
| `article` | texto | Artigo desta unidade (referência a `articles.id`) | `"article-0"` |
| `zone` | texto | Zona do armazém; uma lista de coleta só pode ter itens de uma zona | `"zone-7"` |
| `aisle` | inteiro | Corredor (coordenada horizontal); de −48 a 49, sem o 0 | `-45` |
| `row` | inteiro | Posição ao longo do corredor (coordenada vertical); de −48 a 49, sem o 0 | `-5` |

Os valores 0 de `aisle` e `row` são os corredores transversais, onde não há itens.

## orders.json — pedidos

| Campo | Tipo | Significado | Exemplo |
|---|---|---|---|
| `id` | texto | Identificador do pedido | `"order-0"` |
| `positions` | lista de texto | Artigos pedidos, um por unidade (um artigo repetido = mais de uma unidade) | `["article-165", "article-502", "article-722"]` |

## parameters.json — parâmetros do problema original

| Campo | Significado | Valor |
|---|---|---|
| `min_number_requested_items` | Mínimo de unidades que a solução deve coletar (20% do total de posições) | 264 em `small-0` |
| `max_orders_per_batch` | Máximo de pedidos por lote | 50 |
| `max_container_volume` | Volume máximo de cada contêiner (lista de coleta) | 1000 |
| `first_row`, `last_row` | Limites das posições ao longo dos corredores | −50, 50 |
| `first_aisle`, `last_aisle` | Limites dos corredores | −50, 50 |

## Como as instâncias foram geradas (generator.py)

| Porte | Unidades em estoque | Artigos | Pedidos | Zonas |
|---|---|---|---|---|
| small | 10.000 | 3.333 | 500 | 10 |
| medium | 100.000 | 33.333 | 5.000 | 50 |
| large | 1.000.000 | 333.333 | 50.000 | 100 |

- Cada unidade recebe corredor, posição e zona **sorteados de forma independente e uniforme**.
- Cada pedido tem de 2 a 6 posições (pesos 100, 50, 20, 5 e 2) e é formado retirando
  unidades reais do estoque; por isso a demanda total nunca excede o estoque.
- Os artigos dos pedidos são sorteados aleatoriamente: **não há correlação planejada entre
  artigos nem entre pedidos**.

## Conversão para o formato do desafio (converter_zalando.py)

| Desafio | Zalando |
|---|---|
| item | artigo (`articles.id`) |
| corredor | par (`zone`, `aisle`) |
| oferta u_ai | número de unidades do artigo naquele par (zona, corredor) |
| demanda u_oi | número de vezes que o artigo aparece em `positions` do pedido |
| LB / UB | 10,5% / 37,8% da demanda total (medianas das instâncias do Mercado Livre) |

Campos **não usados** na conversão: `volume`, `row`, `max_orders_per_batch`,
`max_container_volume` e `min_number_requested_items` (o problema do desafio não tem
lotes, contêineres nem roteamento).
