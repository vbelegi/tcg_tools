# Plataforma: usuários, Fourse Points e torneios externos

Contrato de produto (LAN v1 → web v2). Moeda: **Fourse Points (FP)**.

## Papéis

| Papel | Capacidades |
|-------|-------------|
| **admin** | Tudo: usuários, presets, reabrir/excluir torneio, torneios externos, FP |
| **staff** | Criar/operar torneios, inscrições, check-in, sorteio, split de premiação |
| **player** | Ver conteúdo público; se `active`, autoinscrever-se |

## Identidade

- Login: **email + senha** (sem username de login).
- Nome de exibição: não precisa ser único.
- Email e celular: **únicos**; erro se já existirem.
- Conta rápida (staff): nome + celular + email → status `incomplete` (sem senha).
- Finalização: **só link de convite** (7 dias, uso único); jogador define senha.
- Menor de 18: responsável como metadado (`guardian_*`).
- LAN v1: convite gera token (envio de e-mail fica para v2 web).

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

Sem login: lista/resultados de torneios, perfis públicos (nome de exibição, histórico, decklists), ranking FP.

**Nunca** expor email, celular, nascimento ou responsável em endpoints públicos.

Logado (player ativo): + inscrição em torneios com `registration_open`.

## Torneios externos

Admin registra evento `source=external` com nome, data, formato opcional, preset, N e colocações (conta ou nome + decklist). Sem rodadas. Finalize grava snapshot + FP.

## Auth técnico

Sessão cookie HttpOnly (como hoje). JWT fica para v2 internet.
