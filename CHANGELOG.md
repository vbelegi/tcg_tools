# Changelog

Formato baseado em [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added

- **Ações promocionais:** tipo Sorteio de Direito de Compra Físico, inscrição por QR (10 min, uso único), regulamento em PDF versionado, sorteio persistido e CSV de contemplados
- **Ações promocionais:** e-mail transacional a todos os inscritos (incluindo pendentes de verificação) quando a ação muda, ganha novo regulamento ou é publicada já com participantes
- **Calendário:** faixa contínua no período das ações publicadas com `show_in_calendar` (sobreposição no mês; rascunhos fora do feed mesmo para staff)

### Database

- Migration `015`: tabelas de ações promocionais, regulamentos, tokens de inscrição, participantes e resultado do sorteio

## [1.12.1] - 2026-09-03

### Fixed

- **Testes:** `test_invite_api_returns_claim_url` alinhado à API sem campo `token` (só `claim_path` / `claim_url`)

## [1.12.0] - 2026-09-03

### Added

- **LGPD:** páginas Termos de uso e Política de privacidade; aceite obrigatório no cadastro e no claim de convite
- **LGPD:** preferência de marketing (opt-out) no perfil; default apto a contato WhatsApp/e-mail
- **LGPD:** exclusão de conta (self + admin); histórico de torneios permanece como **Anônimo**
- **LGPD:** exportação dos próprios dados (`GET /auth/me/export`)
- **Admin:** export CSV “Aptos a contato” (nome + telefone) em `/usuarios`
- **Admin:** trilha `staff_audit_logs` (listagem, busca, criações, invites, reset, export, exclusão, papel)
- **Ops:** script `purge_incomplete_users` (incomplete sem claim após 180 dias)

### Changed

- **Layout:** área principal preenche telas médias/grandes (até 1440px) e centraliza em ultrawide; mobile (≤900px) inalterado
- **Layout:** rodapé global do site (Termos · Privacidade · Powered by FOURSE) fora do menu — visível no mobile
- **Convites:** tokens armazenados com hash (como reset/verify); API deixa de devolver o token cru

### Fixed

- **Auth modal:** checkbox de termos não estica mais à largura total do modal
- **Cadastro:** placeholder/hint de celular com exemplo DDD (`11987654321`)

### Database

- Migration `014`: campos de privacidade/marketing em `users`, status `deleted`, tabela `staff_audit_logs`, hash de invites existentes

## [1.11.1] - 2026-09-01

### Fixed

- **Usuários:** coluna de ações centralizada na tabela admin (`/usuarios`)
- **Perfil:** hero e card de FP empilhados em telas estreitas (≤640px)

### Changed

- **Calendário:** torneios em fase de inscrição aparecem no calendário público mesmo sem inscrição online (`registration_open: false`); badge **"Sem inscrição online"** e nota orientando inscrição na loja (sem CTA pelo site)
- **Self-inscrição:** mensagem de erro deixa claro que o bloqueio é só pelo site, não do evento em si

## [1.11.0] - 2026-09-01

### Added

- **E-mail:** envio transacional via SMTP (Hostinger em produção; log no console em dev)
- **E-mail:** verificação de endereço no cadastro (link válido 24h, banner global, reenvio com rate limit)
- **E-mail:** convite automático por e-mail ao criar conta incomplete
- **Auth:** “Esqueci minha senha” para contas com e-mail verificado (resposta genérica)
- **Torneios:** drag-and-drop para reordenar colocações na página de registro manual

### Changed

- **Auth:** ativação por convite marca e-mail como verificado automaticamente
- **Admin:** reset de senha envia e-mail quando a conta está verificada

### Database

- Migration `013`: `users.email_verified_at` + tabela `email_verification_tokens`

## [1.10.1] - 2026-09-01

### Changed

- **Agenda:** lista de eventos apenas em cards (desktop e mobile); destaque visual do card em edição

## [1.10.0] - 2026-09-01

### Added

- **Agenda:** layout do formulário e tabela corrigidos; lista em cards no mobile
- **Auth:** reset de senha por admin (link `/redefinir-senha/:token`); hint de requisitos de senha no cadastro
- **Torneios:** formulário para editar torneios em rascunho (nome, data, horário, TCG, inscrição, etc.)
- **Torneios:** modo **sem rodadas** (`pairing_mode: manual`) — inscrição no calendário com colocações manuais ao final

### Changed

- **Auth:** login não bloqueia submit por tamanho de senha; validação de senha no cadastro ocorre no submit
- **Torneios:** unicidade de nome por combinação **nome + data** (torneios recorrentes com mesmo nome)

### Database

- Migration `011`: tabela `password_reset_tokens`
- Migration `012`: coluna `events.pairing_mode` (default `platform`)

## [1.9.0] - 2026-08-31

### Added

- **Security hardening:** rate limiting em login/registro/claim-invite; hash SHA-256 de tokens de sessão no DB; revogação de sessões anteriores no login
- **Calendário:** filtro de visibilidade alinhado à listagem pública (rascunhos fechados ocultos)
- **Headers HTTP** no Caddy (CSP, X-Frame-Options, nosniff, Referrer-Policy)
- **Frontend:** validação de redirect `next` (anti open-redirect)

### Changed

- Senha mínima **10 caracteres**
- `/docs` e OpenAPI desabilitados quando `TCGTOOLS_ENVIRONMENT=production`
- SPA fallback com proteção contra path traversal
- Buscas `ilike` escapam `%` e `_`; limite de body HTTP (1 MB)
- Upload de avatar lê stream com limite; exports do client enviam cookies corretamente

### Security

- Migration `010`: invalida sessões existentes (re-login após deploy)

## [1.8.0] - 2026-08-31

### Added

- **Papéis (admin):** `PATCH /api/v1/users/{id}/role` — promover/rebaixar entre `staff` e `player` (UI em Usuários)
- **Agenda:** eventos no calendário sem inscrição — tabela `calendar_announcements`, CRUD staff em `/agenda`, feed unificado em `GET /api/v1/calendar`
- **Mobile:** menu hambúrguer em telas ≤900px; sidebar em drawer; Perfil/Sair/Entrar acima dos links

### Changed

- **Calendário público:** exibe torneios e eventos da agenda com estilos distintos

## [1.7.0] - 2026-08-31

### Added

- **Backup offsite (Fase 6):** `deploy/backup-offsite.sh` — upload de dumps MySQL para Google Drive via rclone
- **Runbook VPS (Fase 6):** [RUNBOOK_VPS.md](docs/RUNBOOK_VPS.md) — deploy, backup, restore e operação

### Changed

- **Docs:** `V2_WEB.md`, `INSTALACAO.md`, `TROUBLESHOOTING.md` — links para runbook e offsite; Fase 6 concluída

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

[1.9.0]: compare/v1.8.0...v1.9.0
[1.8.0]: compare/v1.7.0...v1.8.0
[1.7.0]: compare/v1.6.0...v1.7.0
[1.6.0]: compare/v1.5.0...v1.6.0
[1.5.0]: compare/v1.4.0...v1.5.0
[1.4.0]: compare/v1.3.0...v1.4.0
[1.3.0]: compare/v1.2.0...v1.3.0
[1.2.0]: compare/v1.1.0...v1.2.0
[1.1.0]: compare/v1.0.0...v1.1.0
[1.0.0]: releases/tag/v1.0.0
