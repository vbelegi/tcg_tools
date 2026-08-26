# Changelog

Formato baseado em [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added

- **Auth modal:** login e criar conta (player completo) sem sair da página; `/login` redireciona para `/?auth=login`
- **Auto-cadastro player:** `POST /auth/register` (nome, e-mail, celular, senha → conta ativa)
- **Excluir torneio:** `DELETE /torneios/{id}` (admin) com confirmação pelo nome na UI
- **Inscrever conta existente** e criar incomplete na ficha do draft; convite com **copiar link** (sem e-mail automático)
- **`fp_k`** opcional no preset de premiação
- **Multi-usuário / Fourse Points:** papéis `admin` | `staff` | `player`; login por e-mail (`admin@local`); contas incompletas + convite (7 dias); check-in / bloqueio de início com pendências; ledger FP no finalize; torneios externos; ranking e perfis públicos
- **Docs:** contrato em `docs/PLATFORM_USERS_FP.md`

### Changed

- **Lista de torneios:** “Novo torneio” / “Importar externo” só para staff/admin (externo só admin); links `.secondary` no estilo pill
- **Auth modal:** layout mais estreito, inputs full-width, body scrollável e ações no footer
- **Data de nascimento:** obrigatória no register/claim; responsável só se menor de 18
- **Home:** atalhos Premiação/Sorteador só para staff/admin
- **`/usuarios`:** gated por `RequireAdmin` no frontend
- **Guardian:** obrigatório no register/claim quando birth_date indica menor de 18
- **Auth:** login deixa de usar username `admin` e passa a usar e-mail (`admin@local`; legado `admin` ainda aceito no login); UI sem dicas de bootstrap

## [1.2.0] - 2026-08-25

### Fixed

- **Inno Setup:** `PasswordOnlyMode` como função (Check:) — corrige compile do instalador
- **CI release:** job `build` (ISCC + staging) também roda em PRs com paths de release

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

[1.2.0]: compare/v1.1.0...v1.2.0
[1.1.0]: compare/v1.0.0...v1.1.0
[1.0.0]: releases/tag/v1.0.0
