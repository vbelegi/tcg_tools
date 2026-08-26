# Plataforma: usuários, Fourse Points e torneios externos

Contrato de produto (LAN v1 → web v2). Moeda: **Fourse Points (FP)**.

## Papéis

| Papel | Capacidades |
|-------|-------------|
| **admin** | Tudo: usuários, presets, reabrir/excluir torneio, torneios externos, FP |
| **staff** | Criar/operar torneios, inscrições, check-in, sorteio, split de premiação |
| **player** | Ver conteúdo público; se `active`, autoinscrever-se |

## Identidade

- Login: **email + senha** (sem username de login); UI em **modal** (sem hints de bootstrap na interface).
- Nome de exibição: não precisa ser único.
- Email e celular: **únicos**; erro se já existirem.
- **Auto-cadastro (player):** nome + e-mail + celular + senha + **data de nascimento** → status `active` (conta completa).
- **Menor de 18:** data de nascimento obrigatória para todos os players; se &lt; 18 anos, exige também `guardian_name` + `guardian_phone` (register e claim-invite).
- **Conta rápida incomplete (só staff/admin):** na ficha do torneio (ou painel Usuários) → nome + celular + email, sem senha; finalização via **link de convite** (7 dias, uso único). Admin **copia o link** e encaminha manualmente (sem e-mail automático na LAN v1).
- Admin pode **excluir torneio** (qualquer status) com confirmação pelo nome.
- Staff pode **buscar conta existente** e inscrever na ficha do draft.
- Preset opcional **`fp_k`** (default 10) para Fourse Points.

## Inscrição e presença

- Fontes: walk-in sem conta, conta existente, criação rápida, self-service.
- `attendance`: `pending` | `checked_in`.
- Self-service → `pending`; staff na loja pode criar já `checked_in`.
- **Bloquear start** se houver `pending`.
- Remover inscrito = delete da inscrição; conta permanece.
- `N` para FP = jogadores `checked_in` no **start** (inclui drops posteriores).

## Fourse Points

\[
FP_i = \mathrm{round}(\mathrm{premio\_fracao}(i) \times N \times K)
\]

- Mesmo preset de spread do torneio; **K default = 10** (`fp_k` no preset, opcional).
- Gravados no **finalize**.
- Drop / walkover na classificação → **0 FP**.
- Ledger por `(event_id, user_id)`; re-finalize substitui linhas do evento.

## Visibilidade pública

Sem login / player: vê torneios **`finished`**, drafts com **`registration_open`** (vitrine + CTA) e, se player, eventos em que está inscrito. Em andamento (inscrito): pairings/classificação só leitura.

**Calendário** (`/calendario`): público; lista **todos** os torneios do mês (status + TCG + descrição/horário). CTAs:
- finished → resultado
- draft com inscrição aberta → self-inscrição / entrar
- running → só inscrito ou staff
- draft fechado → só infos (sem CTA)

**TCG:** catálogo admin (`/tcgs`) com nome + cor hex para chips do calendário. Torneio **exige** `tcg_game_id` na criação (interno e externo). Campos opcionais: `description`, `start_time`. Default de criação: **inscrição aberta**.

Ícones estáticos em `frontend/public/tcg-icons/` (`magic_the_gathering.png`, …; fallback `other.png`).

## Perfil do jogador (`/jogadores/{id}`)

Público: stats (torneios, títulos, top 8, melhor colocação), **Insights** heurísticos, badges de TCG (torneios **finalizados**), gráficos FP por jogo/mês, histórico + decklists.

**Acesso:** Ranking Fourse Points; **Meu Perfil** no sidebar (logado); nome linkado em `/usuarios` (admin); busca pública no topo do perfil (`GET /jogadores/buscar?q=` → só `id`, `display_name`, `avatar_url`).

**FP:** visível só para o **próprio jogador** e **admin**.

**Avatar:** upload próprio (`POST /auth/me/avatar`, máx. 512 KB; redimensiona para 256×256 WebP em `data/media/avatars/`). Placeholder: `/avatars/default.png`. Edição de nome: `PATCH /auth/me`. **Alterar senha** só no próprio perfil (modal); removido do sidebar.

Staff/admin: todos os status e operação completa.

**Nunca** expor email, celular, nascimento ou responsável em endpoints públicos.

## Torneios externos

Admin registra evento `source=external` com nome, data, formato opcional, preset, N e colocações (conta ou nome + decklist). Sem rodadas. Finalize grava snapshot + FP.

## Auth técnico

Sessão cookie HttpOnly (como hoje). JWT fica para v2 internet.
