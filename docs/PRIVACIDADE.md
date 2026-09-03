# Privacidade e LGPD (operação)

Espelho operacional da política pública (`/privacidade`). Controlador: FOURSE · contato@fourse.com.br.

## Preferências de marketing

- Default: usuário **apto** a comunicações comerciais (WhatsApp primário, e-mail também).
- Opt-out: perfil do jogador (“Receber novidades…”) ou futuro link em e-mail.
- Admin: **Aptos a contato (CSV)** em `/usuarios` — só `active`, com telefone, sem opt-out, idade ≥ 18.
- E-mails transacionais (verificar, convite, reset, avisos de torneio inscrito) **não** dependem do opt-out.

## Exclusão de conta

- Self-service: perfil → Excluir minha conta (senha + digitar `EXCLUIR`).
- Admin: botão Excluir na lista (exceto admin).
- Efeito: PII removido; status `deleted`; jogadores nos torneios viram **Anônimo**.

## Incomplete abandonado

```bash
cd /opt/tcg_tools  # ou backend local
py -3.13 -m app.scripts.purge_incomplete_users --dry-run
py -3.13 -m app.scripts.purge_incomplete_users
```

Padrão: 180 dias sem claim. Agendar via cron na VPS se desejado.

## Auditoria staff

Tabela `staff_audit_logs`: ações `user.list`, `user.search`, `user.create_incomplete`, `user.invite`, `user.password_reset`, `user.delete`, `user.role_change`, `marketing.export`. Meta sem dump de telefones.

## Versões legais

Constantes em `app/core/privacy.py`: `PRIVACY_POLICY_VERSION`, `TERMS_VERSION`. Ao alterar textos em `/termos` e `/privacidade`, incrementar versões e exigir novo aceite em cadastros futuros (já gravado no create/claim).
