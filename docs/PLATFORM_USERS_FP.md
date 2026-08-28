# Plataforma: usuários, Fourse Points e torneios externos

Contrato de produto (LAN v1 → web v2). Moeda: **Fourse Points (FP)**. Hospedagem VPS: ver `docs/V2_WEB.md`.

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
- **Conta rápida incomplete (só staff/admin):** na ficha do torneio (ou painel Usuários) → nome + celular + email, sem senha; finalização via **link de convite** (7 dias, uso único). Admin **copia o link** (`claim_url` com `TCGTOOLS_PUBLIC_BASE_URL` em produção) e encaminha manualmente (sem e-mail automático).
- Admin pode **excluir torneio** (qualquer status) com confirmação pelo nome.
- Staff pode **buscar conta existente** e inscrever na ficha do draft.
- Preset opcional **`fp_k`** (default 10) para Fourse Points.

## Inscrição e presença

- Fontes: conta existente, criação rápida (incomplete), self-service. **Sem walk-in** sem conta.
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

Público: stats (torneios, títulos, top 8, melhor colocação), **Insights** heurísticos, badges de TCG (torneios **finalizados**), histórico + decklists. Gráficos e totais FP só para dono/admin (abaixo).

**Perfil:** usuários `active` e `incomplete` têm perfil público em `/jogadores/{id}` (stats, histórico, decklists; FP só dono/admin). Contas incomplete aparecem na busca e no ranking quando tiverem FP. Admin bootstrap tem perfil nativo. Sem exigência de inscrição em torneio.

**Home** (`/`): atalhos densos — Calendário · Torneios · Ranking; staff + Novo torneio / Premiação / Sorteador; admin + Importar externo / Usuários / TCGs; CTA Entrar ou Meu Perfil; mini top ranking.

**Acesso:** Ranking Fourse Points (pódio top 3 + lista; `GET /ranking` com `avatar_url`); **Meu Perfil** no sidebar e na Home (logado); nome linkado em `/usuarios` (admin); busca pública no topo do perfil (`GET /jogadores/buscar?q=` → só `id`, `display_name`, `avatar_url`).

**FP:** total e breakdown (`fp_by_*`, `fp_earned`, gráficos, posição no ranking) visíveis só para o **próprio jogador** e **admin**. Ranking público (`GET /ranking`) continua listando totais agregados.

**Avatar:** upload próprio (`POST /auth/me/avatar`, máx. 512 KB; redimensiona para 256×256 WebP em `users.avatar_blob`). Leitura: `GET /api/v1/media/avatars/{user_id}`. Placeholder: `/avatars/default.png`. Edição de nome: `PATCH /auth/me`. **Alterar senha** só no próprio perfil (modal); removido do sidebar.

**Inscrição (draft / staff):** um campo de busca (conta existente). Se não achar → criar **incomplete** (nome + e-mail + celular) e inscrever. Sem walk-in sem conta; um jogador por vez; seed em “opções avançadas”. Link de convite **não** é gerado nessa hora — admin gera depois em `/usuarios` (futuro: rotina automática).

**Rodadas (staff):** com rodada ativa, a ficha redireciona para `/torneios/{id}/rodadas/{n}` (pairings compactos: `Nome · [0][1][2] · × · [0][1][2] · Nome`; best-of só no header; botões de placar com opções inválidas desabilitadas). Entre rodadas: primary **Iniciar próxima** / **Finalizar** no header; resumo compacto em scoreline; ativos em chips; drop e reabrir secundários; drop exige digitar o nome no 2º passo do modal.

**Resultado:** classificação/premiação compactas; sorteio com chips na pool; export de log no menu ⋯; **Sortear** como ação primary do bloco.

Staff/admin: todos os status e operação completa. Telas auxiliares (**Premiação**, **Sorteador**, **Usuários**, **TCGs**) seguem o mesmo padrão visual denso (header, chips, tabelas compactas).

**Nunca** expor email, celular, nascimento ou responsável em endpoints públicos.

## Torneios externos

Admin registra evento `source=external` com nome, data, formato, TCG, preset, taxa e colocações. UI densa: busca de conta / incomplete / só nome; decklist e drop por linha; resumo de N. Sem rodadas. Finalize grava snapshot + FP.

## Auth técnico

Sessão cookie HttpOnly (como hoje). JWT fica para v2 internet.
