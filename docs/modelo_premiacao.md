# Modelo de Premiação TCG

## Objetivo

Distribuir 100% das inscrições entre os melhores colocados utilizando um modelo matemático escalável. Os prêmios são pagos em **Créditos na Loja**, portanto valores com centavos são aceitos sem restrição.

## Fonte dos parâmetros

Os valores usados em cada cálculo vêm do **preset** selecionado:

- Arquivo gravável: `{data_dir}/premiacao_presets.json` (padrão: `%APPDATA%\TCGTools\` na loja)
- Defaults embarcados: `backend/config/premiacao_presets.json` (somente leitura após instalação)
- API: `GET /api/v1/premiacao/presets/{id}`
- Torneios: snapshot em `events.premiacao_preset` no momento da criação do evento

Implementação: `backend/app/core/premiacao/calculator.py`

## Parâmetros

| Parâmetro | Descrição |
|-----------|-----------|
| `N` | Número de jogadores |
| `min_jogadores` | Mínimo de jogadores aceito no cálculo |
| `min_premiados` | Mínimo de colocados premiados |
| `max_premiados` | Máximo de colocados premiados |
| `crescimento` | Escala para aumentar premiados conforme `N` |
| `r` | Razão da curva exponencial (0 < r < 1) |
| `casas_decimais` | Precisão do arredondamento (0 a 4) |

## Número de premiados

```
Y = min(max_premiados, max(min_premiados, floor((N + 1) / crescimento)))
Y = min(Y, N)
```

A última linha garante que nunca haja mais premiados do que jogadores.

### Exemplo com `crescimento = 4`

| Jogadores | Premiados |
|-----------|-----------|
| 4–14 | Top 3 |
| 15–18 | Top 4 |
| 19–22 | Top 5 |
| 23–26 | Top 6 |
| 27–30 | Top 7 |
| 31+ | Top 8 |

### Exemplo com `crescimento = 3`

| Jogadores | Premiados |
|-----------|-----------|
| 4–8 | Top 3 |
| 9–11 | Top 4 |
| 12–14 | Top 5 |
| 15–17 | Top 6 |
| 18–20 | Top 7 |
| 21+ | Top 8 |

> A tabela muda conforme `crescimento`. Consulte o preset ativo na UI ou em [configuracao.md](configuracao.md).

## Pesos

```
peso(i) = r^(i - 1)    onde i = 1º, 2º, 3º lugar...
```

Implementação: `[r^0, r^1, ..., r^(Y-1)]`

## Distribuição

```
premio(i) = N × peso(i) / soma(pesos)
```

Quando informado **valor de inscrição** (R$), a UI e a API também exibem **Créditos na Loja** = `premio(i) × valor_inscricao`.

## Arredondamento (maior resto)

Após o cálculo proporcional, aplica-se o **método do maior resto**:

1. Cada prêmio é arredondado para baixo na precisão configurada.
2. O residual (diferença até totalizar exatamente `N`) é distribuído em unidades mínimas (ex.: centésimos) entre as posições com maior parte fracionária.

Isso evita concentrar todo o ajuste na última colocação e mantém a soma sempre igual a `N`.

### Por que essa abordagem?

- Compatível com pagamento em Créditos na Loja com centavos.
- Distribui o residual de forma mais justa entre colocados.
- Garante soma exata sem depender de uma única posição absorver o erro.

## Ajustando a curva

- **`r` menor** → premiação mais concentrada no topo.
- **`r` maior** → premiação mais distribuída entre colocados.
- Valores entre **0,70 e 0,80** costumam funcionar bem em torneios locais.

## Exportação CSV

Arquivos gerados em `exports/premiacao_{min_jogadores}_a_{limite}.csv` (download HTTP + cópia local opcional):

- Encoding UTF-8 com BOM (`utf-8-sig`) para Excel.
- Separador `;`
- **Substitui** arquivo existente com o mesmo nome ao exportar novamente.

## Torneios

Ao **finalizar** um torneio, `N` = total de jogadores inscritos (incluindo drops). O resultado é gravado em `premiacao_resultado` e exibido em **Torneios → Resultado**.

### Suíço

Cada tier absoluto (`premios[0]`, `premios[1]`, …) corresponde a um jogador na ordem de classificação (1º, 2º, 3º…).

### Eliminatória simples (faixas)

Tiers absolutos do preset são agrupados em **faixas**:

| Faixa | Tiers (índices) |
|-------|-----------------|
| 1º | `[0]` |
| 2º | `[1]` |
| 3º / 4º (com bronze) | `[2]`, `[3]` |
| 3–4 (sem bronze) | `[2]` + `[3]` → pool único |
| 5–8 | `[4..7]` |
| 9–16 | `[8..15]` | … |

Para cada faixa: `pool = soma(premios[i])`, dividido igualmente entre jogadores elegíveis na faixa (excluindo drops). Se a faixa tiver menos jogadores que o esperado (ex.: drop na semi), o pool inteiro é dividido só entre os presentes.

**Invariante:** `sum(payout_j) = N` inscrições (tolerância = uma unidade na última casa decimal do preset).

Preview standalone em **Premiação → Calcular** com formato Eliminatória usa a mesma lógica de faixas.

### `schema_version` em `premiacao_resultado`

| Versão | Formato | Conteúdo |
|--------|---------|----------|
| **1** | Suíço ou SE legado | `premios[]`, `creditos[]` por tier; sem `bands` |
| **2** | SE (pós-feature) | `bands`, `player_payouts`, `standings_snapshot`, `total_creditos` |

Torneios SE **finalizados antes** da feature permanecem em v1: classificação recalculada via standings Suíço (`compute_standings`). Não há migração automática para v2.

**Créditos:** `total_creditos = jogadores × entry_fee` (todos inscritos são pagantes).

Ver também [export_log.md](export_log.md) e [migration_003.md](migration_003.md).
