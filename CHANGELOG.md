# Changelog

Formato baseado em [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added

- **Classificação:** coluna OGW% e tooltip com ordem dos critérios de desempate na tela de resultado
- **Sorteio:** modo encadeado (1 a 1 sem repetir) no módulo Sorteador e no resultado do torneio
- **Sorteio (torneio):** exclusão manual da pool (checkboxes + atalho “Excluir 1º lugar”)
- **Seeds:** validação all-or-nothing no draft (UI + bloqueio ao iniciar)
- **Usabilidade:** Enter/Esc/colar lista no cadastro; Esc nos modais; foco na próxima partida e Ctrl+Enter para concluir rodada; Enter/Espaço no sorteio encadeado
- **Instalador / launcher:** ícone PE no `TCGTools.exe` (atalhos e Explorer) via `rsrc`; `SetupIconFile` / `UninstallDisplayIcon` no Inno Setup
- **Auth:** usuário fixo `admin`, senha (hash) no SQLite; login obrigatório; alterar senha na UI ou no instalador
- **LAN:** `lan_access` no launcher (bind `0.0.0.0`); regra de firewall no instalador; copiar URL da rede na bandeja
- **UI:** tema dark com paleta Fourse (roxo/laranja); crédito “Powered by FOURSE” na sidebar e no login

### Changed

- **Launcher:** Job Object real (kill-on-close), health check com `app=tcg_tools`, checagem de porta, stderr do uvicorn, MessageBox em erros fatais
- **Launcher:** `go.sum` commitado; systray corrigido para `github.com/energye/systray` v1.0.3; ícone embarcado (`assets/icon.ico`)
- **Presets:** gravados em `{data_dir}/premiacao_presets.json` (corrige falha de escrita em Program Files)
- **Build:** `pip install -r requirements-prod.lock` no release; Inno Setup com `AppMutex` e encerramento na desinstalação
- **CI:** Pester + lockfile validation; `windows-test-suite.yml` reutilizável; smoke staging no release
- **Multi-user:** mutex `Local\` (por sessão de usuário); presets em `{data_dir}`
- **Instalador:** merge config no upgrade; uninstall opcional de APPDATA; kill python filho

### Added

- **Instalador Windows:** `scripts/build-release.ps1`, `scripts/installer.iss` (Inno Setup), pipeline [release.yml](.github/workflows/release.yml)
- **Launcher Go** (`launcher/`): bandeja do sistema, single-instance, autostart, `launcher_config.json`
- **Scripts compartilhados:** `scripts/lib/Embed-Python.ps1` + testes Pester
- Docs: [BUILD_RELEASE.md](docs/BUILD_RELEASE.md), [INSTALADOR.md](docs/INSTALADOR.md) atualizado
- Paths: exports/logs sob `data_dir`; testes `test_paths.py`
- CI: job `launcher` com cobertura Go ≥80%
- **Eliminatória simples:** faixas de classificação e premiação (3–4, 5–8…); partida opcional de 3º–4º (bronze); melhor de por fase; invariante `sum(payouts) = N`
- Migration Alembic `003`: `third_place_match`, `se_bo_config`, `matches.is_third_place`, `matches.best_of`
- Premiação standalone: seletor Suíço / Eliminatória + preview por faixas
- Componentes UI `SeFormatOptions`, `PremiacaoBandsTable`, `MatchBadges`
- Schema tipado `PremiacaoResultado`; export JSON **v2**; `total_creditos`; redistribuição de pool em faixas vazias
- Docs: [migration_003.md](docs/migration_003.md), [export_log.md](docs/export_log.md)
- Testes: SE 6/32 jogadores, bronze 16, reopen, drops na semi, `se_bracket`, cobertura frontend ≥80% (utils/components)

### Changed

- `setup.ps1` usa módulo Embed-Python; cria `data/exports` e `data/logs`
- Torneios SE finalizados após update gravam `premiacao_resultado.schema_version = 2` com snapshot congelado
- Torneios finalizados antes da feature: comportamento legado preservado
- `se_bo_config` inválido para o bracket gera `config_warnings` no rascunho e é podado ao iniciar
- CI: `npm run test:coverage` com meta 80% no frontend (utils/components)

## [1.1.0] - 2026-07-31

### Added

- **Reabrir rodada:** endpoint `POST /api/v1/torneios/{id}/rodadas/reabrir` e botões na UI para corrigir resultados após concluir rodada; remove rodada posterior e refaz pairing ao avançar
- **Testes:** `conftest.py` com fixture Alembic (alinhado à produção); fluxo completo Suíço/SE; integração torneios com DB real
- **Cobertura:** pytest-cov com meta mínima de 80% no backend
- **CI:** GitHub Actions (pytest + coverage + frontend test + build)
- **Frontend:** Vitest + Testing Library (smoke tests API e Home)
- **Documentação:** manual do operador, troubleshooting, estratégia de instalador

### Changed

- Testes DB usam Alembic `upgrade head` em vez de `Base.metadata.create_all`
- `can_reopen_round` exposto no resumo do evento

## [1.0.0] - 2026-07-30

### Added

- App web local FastAPI + React + SQLite
- Premiação: calcular, tabela, presets, export CSV
- Torneios Suíço e Eliminatória: pairings, resultados, drops, classificação OMW/OGW
- Fluxo entre rodadas: concluir → drop → iniciar próxima → finalizar
- Placares flexíveis (1-0 por tempo, 0-0 empate Suíço, `scores_submitted`)
- Export log JSON pós-finalização
- Scripts Windows: `setup.ps1`, `Iniciar TCG Tools.bat`
- Alembic migrations (001 schema, 002 scores_submitted)

[1.1.0]: compare/v1.0.0...v1.1.0
[1.0.0]: releases/tag/v1.0.0
