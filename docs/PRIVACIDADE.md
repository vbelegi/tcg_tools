# Privacidade e LGPD (operação)

Espelho operacional da política pública (`/privacidade`). Controlador: FOURSE · contato@fourse.com.br.

## Preferências de marketing

- Default: usuário **apto** a comunicações comerciais (WhatsApp primário, e-mail também).
- Opt-out: perfil do jogador (“Receber novidades…”) ou futuro link em e-mail.
- Admin: **Aptos a contato (CSV)** em `/usuarios` — só `active`, com telefone, sem opt-out, idade ≥ 18.
- E-mails transacionais (verificar, convite, reset, **troca de e-mail**, avisos de ação promocional) **não** dependem do opt-out.

## Contato (e-mail e telefone)

- **Troca de e-mail:** perfil → senha + novo endereço. Verificado: pendência 24h (confirma no novo; cancela no antigo). Não verificado: troca imediata + reenvio de verificação. Login/recuperação usam o e-mail atual até a confirmação.
- **Telefone:** edição no perfil; limpa verificação (`phone_verified_at`). Colunas `pending_phone` / `phone_verified_at` reservadas para SMS futuro.

## Exclusão de conta

- Self-service: perfil → Excluir minha conta (senha + digitar `EXCLUIR`). Único Super Admin / único admin+ não pode se excluir.
- Admin+: botão Excluir na lista (admin/superadmin só via Super Admin; nunca o último Super Admin).
- Efeito: PII removido; status `deleted`; jogadores nos torneios viram **Anônimo**. Tokens de verificação/reset/troca de e-mail são apagados.

## Incomplete abandonado

```bash
cd /opt/tcg_tools  # ou backend local
py -3.13 -m app.scripts.purge_incomplete_users --dry-run
py -3.13 -m app.scripts.purge_incomplete_users
```

Padrão: 180 dias sem claim. Agendar via cron na VPS se desejado.

## Auditoria staff

Tabela `staff_audit_logs` (somente append). UI: **`/auditoria`** (admin+), filtros por ação, período, ID do ator e ID do alvo.

Ações típicas:

| Prefixo / ação | Exemplos |
|----------------|----------|
| `user.*` | `list`, `search`, `create_incomplete`, `invite`, `password_reset`, `delete`, `role_change` |
| `account.*` | `email_change` (status em `meta`: pending / confirmed / cancelled / direct) |
| `marketing.*` | `export` |
| `promo.*` | `create`, `edit`, `publish`, `regulation`, `enroll_token`, `draw`, `export_winners` |

Meta sem dump de telefones/e-mails completos (troca de e-mail usa máscara).

**Retenção:** hoje não há purge automático. Volume costuma ser aceitável em loja única; leituras (`user.list` / `user.search`) são as mais frequentes. Planejar retenção (ex. 12–24 meses) ou reduzir audit de listagem se a tabela crescer demais.

## Versões legais

Constantes em `app/core/privacy.py`: `PRIVACY_POLICY_VERSION`, `TERMS_VERSION`. Ao alterar textos em `/termos` e `/privacidade`, incrementar versões e exigir novo aceite em cadastros futuros (já gravado no create/claim).
