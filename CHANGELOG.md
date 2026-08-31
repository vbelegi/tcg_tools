# Changelog

Formato baseado em [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added

- **Backup offsite (Fase 6):** `deploy/backup-offsite.sh` — upload de dumps MySQL para Google Drive via rclone
- **Runbook VPS (Fase 6):** [RUNBOOK_VPS.md](docs/RUNBOOK_VPS.md) — deploy, backup, restore, operação

## [1.6.0] - 2026-08-31

### Added

- **Deploy automático VPS (Fase 5):** `deploy/vps-deploy.sh`; workflow manual **Deploy VPS**; deploy após tag `v*` no `release.yml` (environment `production` + secrets SSH)

### Changed

- **Release:** tag `v*` dispara testes, GitHub Release e deploy na VPS via SSH
- **Docs:** `V2_WEB.md` e `BUILD_RELEASE.md` — secrets, chaves SSH e workflows

## [1.5.0] - 2026-08-28

### Added

- **Favicon web:** `favicon.ico` + `apple-touch-icon` no frontend (ícone herdado do antigo launcher)

### Removed

- **Launcher Go** (`TCGTools.exe`, bandeja, LAN)
- **Instalador Windows** (`setup.exe`, Inno Setup, Python embeddable no release)
- **CI:** jobs Go launcher, build Inno, artifact `TCGTools-*-setup.exe`

### Changed

- **Produção:** apenas VPS Docker ([docs/V2_WEB.md](docs/V2_WEB.md)); dev local via `setup.ps1` / `Iniciar TCG Tools.bat`
- **Release:** tag `v*` publica GitHub Release (notas); deploy manual na VPS com `git pull` + `docker compose up -d --build`
- **Docs:** `INSTALADOR.md` arquivado em `docs/archive/`; README, BUILD_RELEASE, INSTALACAO, OPERADOR atualizados

## [1.4.0] - 2026-08-28

### Added

- **V2 web (Fase 3):** avatares WebP em `users.avatar_blob` (`GET /api/v1/media/avatars/{id}`); `claim_url` absoluto nos convites via `TCGTOOLS_PUBLIC_BASE_URL`; cookies de sessão com `Secure` quando a URL pública é HTTPS; script `deploy/backup-db.sh`

### Fixed

- **CI Pester:** registra PSGallery quando ausente no runner Windows (flake `No repository with the name 'PSGallery'`)

## [1.3.0] - 2026-08-26

### Fixed

- **CI smoke:** `requirements-prod.lock` inclui Pillow (avatars); `test-staging.ps1` imprime log do uvicorn se o processo cair
- **Perfil:** caixa de Fourse Points com altura proporcional ao conteúdo (sem stretch no hero)
- **Perfil incomplete:** contas incomplete passam a ter perfil e busca públicos (decklists/histórico)
- **Resultado:** `GET/PATCH /classificacao` responde `{ standings: [...] }` — corrige tela em branco ao finalizar

### Added

- **Torneio draft UX:** inscrição unificada (busca → conta existente ou incomplete); header com Iniciar; Excluir no menu ⋯
- **Home UX:** atalhos densos por papel (público / operação / admin), CTA Entrar ou Meu Perfil, mini top ranking
- **Import externo UX:** header denso, grid do evento, tabela de colocações com busca de conta / incomplete / só nome, decklist e resumo; Enter não submete o form (só vincula hit da busca)
- **Perfil — navegação:** Meu Perfil no sidebar; nome linkado em Usuários; busca pública `GET /jogadores/buscar`
- **Perfil — senha:** modal Alterar senha no próprio perfil (removido do sidebar)
- **Perfil do jogador:** dashboard com stats, Insights, badges TCG, Recharts (FP por jogo/mês), histórico filtrável; avatar + editar nome
- **Avatar:** `POST /auth/me/avatar` (512 KB, WebP 256px) em `users.avatar_blob`; `GET /api/v1/media/avatars/{id}`; placeholder `/avatars/default.png`
- **PATCH /auth/me:** atualizar `display_name`
- **Calendário público** (`/calendario`): grade mensal com todos os torneios, painel do dia e CTAs por status/auth
- **TCGs:** catálogo com cor hex (admin `/tcgs`); seed Magic/Pokémon/Yu-Gi-Oh!/One Piece/Digimon/Lorcana/Riftbound; ícones em `frontend/public/tcg-icons/`
- **Torneio:** campos `description`, `start_time`, `tcg_game_id`; default inscrição aberta
- **Auth modal:** login e criar conta (player completo) sem sair da página; `/login` redireciona para `/?auth=login`
- **Auto-cadastro player:** `POST /auth/register` (nome, e-mail, celular, senha → conta ativa)
- **Excluir torneio:** `DELETE /torneios/{id}` (admin) com confirmação pelo nome na UI
- **Inscrever conta existente** e criar incomplete na ficha do draft; convite com **copiar link** (sem e-mail automático)
- **`fp_k`** opcional no preset de premiação
- **Multi-usuário / Fourse Points:** papéis `admin` | `staff` | `player`; login por e-mail (`admin@local`); contas incompletas + convite (7 dias); check-in / bloqueio de início com pendências; ledger FP no finalize; torneios externos; ranking e perfis públicos
- **Docs:** contrato em `docs/PLATFORM_USERS_FP.md`

### Changed

- **Torneio draft:** sem walk-in puro; inscrição 1 a 1 via busca; incomplete exige e-mail+celular; seed em opções avançadas; convite só em Usuários (não no cadastro rápido)
- **Rodadas:** hub intermediário removido com rodada ativa (redirect); pairings em cards; “Entre rodadas” compacto (scoreline + chips de ativos); drop com confirmação digitando o nome
- **Perfil:** admin bootstrap tem perfil nativo (sem precisar ter jogado torneio)
- **Perfil:** seção renomeada para **Insights**; `/conta/senha` redireciona à home
- **Nav/Home:** “Ranking Fourse Points” (FP só como abreviação em colunas/espaços curtos)
- **Torneio:** `tcg_game_id` obrigatório na criação (API + UI interno/externo)
- **Perfil:** FP oculto para visitantes (visível para dono e admin); decklists e histórico públicos
- **Inscrição aberta:** guest/player veem drafts com `registration_open` (vitrine + CTA); draft fechado continua oculto
- **Incomplete / inscrição:** validação de celular com erro junto ao formulário (hint DDD + número); API exige conta (`user_id`/e-mail) ou `create_account`
- **Player:** lista só `finished` ou inscritos; detalhe sem “Gerenciar rodada” (pairings/classificação só leitura); GET rodada liberado para quem pode ver o evento
- **Visitante:** lista só torneios `finished`; clique abre resultado (classificação + decklists leitura); API oculta draft/running
- **Auth modal:** padding na scrollbar do formulário
- **Lista de torneios:** “Novo torneio” / “Importar externo” só para staff/admin (externo só admin); links `.secondary` no estilo pill
- **Auth modal:** layout mais estreito, inputs full-width, body scrollável e ações no footer
- **Data de nascimento:** obrigatória no register/claim; responsável só se menor de 18
- **Home:** atalhos Premiação/Sorteador só para staff/admin; layout denso (listas + mini ranking) em vez de cards
- **Perfil:** “Jogo principal” usa histórico/badges quando FP está oculto para o visitante
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

[1.6.0]: compare/v1.5.0...v1.6.0
[1.5.0]: compare/v1.4.0...v1.5.0
[1.4.0]: compare/v1.3.0...v1.4.0
[1.3.0]: compare/v1.2.0...v1.3.0
[1.2.0]: compare/v1.1.0...v1.2.0
[1.1.0]: compare/v1.0.0...v1.1.0
[1.0.0]: releases/tag/v1.0.0
