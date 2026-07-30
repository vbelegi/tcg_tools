# Modelo de Premiação TCG

## Objetivo

Distribuir 100% das inscrições entre os melhores colocados utilizando um modelo matemático escalável. Os prêmios são pagos em **Créditos na Loja**, portanto valores com centavos são aceitos sem restrição.

## Fonte dos parâmetros

Os valores usados em cada execução vêm exclusivamente de `config/settings.json`. Os defaults em `core/config.py` servem **apenas** para gerar esse arquivo quando ele não existe ou precisa ser recriado.

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

### Exemplo com `crescimento = 3` (configuração atual)

| Jogadores | Premiados |
|-----------|-----------|
| 4–8 | Top 3 |
| 9–11 | Top 4 |
| 12–14 | Top 5 |
| 15–17 | Top 6 |
| 18–20 | Top 7 |
| 21+ | Top 8 |

> A tabela muda conforme `crescimento`. Consulte sempre o `settings.json` ativo.

## Pesos

```
peso(i) = r^(i - 1)    onde i = 1º, 2º, 3º lugar...
```

Implementação: `[r^0, r^1, ..., r^(Y-1)]`

## Distribuição

```
premio(i) = N × peso(i) / soma(pesos)
```

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

Arquivos gerados em `exports/premiacao_{min_jogadores}_a_{limite}.csv`:

- Encoding UTF-8 com BOM (`utf-8-sig`) para Excel.
- Separador `;`
- **Substitui** arquivo existente com o mesmo nome ao exportar novamente.
- Ao **alterar configurações**, o sistema pergunta se deseja limpar exports anteriores (podem estar desatualizados).
- No menu de configurações, use `limpar_exports` para remover todos os CSVs manualmente.
