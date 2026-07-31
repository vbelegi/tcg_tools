# Export JSON — log de torneio

Disponível após **finalizar** o torneio (botão em Resultado).

## Versões

| `version` | Descrição |
|-----------|-----------|
| **1** | Legado (sem campos SE no evento/partidas) |
| **2** | Inclui `third_place_match`, `se_bo_config`, `is_third_place`, `best_of`, IDs de jogadores nas partidas |

## Estrutura (v2) — valores sugeridos

```json
{
  "version": 2,
  "exported_at": "2026-07-31T18:00:00Z",
  "premiacao_schema_version": 2,
  "event": {
    "id": 1,
    "name": "Torneio Local",
    "format": "single_elimination",
    "third_place_match": true,
    "se_bo_config": { "1": 5, "2": 3 },
    "best_of": 3,
    "entry_fee": 35.0
  },
  "players": [{ "id": 1, "name": "Alice", "seed": 1 }],
  "rounds": [{
    "number": 2,
    "matches": [{
      "player1_id": 1,
      "player2_id": 2,
      "player1": "Alice",
      "player2": "Bob",
      "winner_id": 1,
      "score": "2-0",
      "is_third_place": false,
      "best_of": 5
    }]
  }],
  "standings": [],
  "premiacao": {
    "schema_version": 2,
    "total_creditos": 140.0,
    "jogadores": 4
  }
}
```

## Premiação no export

- `premiacao.schema_version` **1** — Suíço ou SE legado (tiers por colocação).
- `premiacao.schema_version` **2** — SE com `bands` e `player_payouts`.

## Invariante de créditos

Quando `entry_fee > 0`:

`premiacao.total_creditos` = `premiacao.jogadores` × `entry_fee`

Todos os inscritos são considerados pagantes.
