# Migration 003 — recursos SE

Alembic revision `003` adiciona suporte à eliminatória simples com bronze, Bo por fase e metadados por partida.

## Colunas

| Tabela | Coluna | Tipo | Default |
|--------|--------|------|---------|
| `events` | `third_place_match` | boolean | `false` |
| `events` | `se_bo_config` | JSON | `NULL` |
| `matches` | `is_third_place` | boolean | `false` |
| `matches` | `best_of` | integer | `NULL` |

## Upgrade

```bash
cd backend
alembic upgrade head
```

Torneios **em rascunho** ou **finalizados** antes do upgrade recebem defaults seguros (`third_place_match=false`, `best_of` herdado do evento).

Torneios **em andamento** durante o upgrade: partidas já criadas terão `best_of=NULL` (herda `events.best_of`) e `is_third_place=false`.

## Downgrade

```bash
alembic downgrade 002
```

Remove as colunas SE. Perde-se `se_bo_config`, flags de bronze e Bo por partida — faça backup do SQLite antes.

## Validação

- `se_bo_config` chaves = `rounds_from_final` (1 = final); valores 1, 3 ou 5.
- Ao **iniciar** o torneio, fases com chave maior que `max_rounds` são **podadas** automaticamente (ver `config_warnings` no rascunho).

## Testes

`backend/tests/db/test_migration_003.py` — upgrade 002→003 e downgrade.
