# Instalação — TCG Tools

## Produção (loja Fourse)

O sistema roda em **https://torneios.fourse.com.br** (VPS Docker). Deploy e operação: [V2_WEB.md](V2_WEB.md). Runbook: [RUNBOOK_VPS.md](RUNBOOK_VPS.md).

### Checklist pós-deploy ou release

1. `curl -fsS https://torneios.seudominio.com/api/v1/health` → `{"status":"ok",...}`
2. Login **admin@local** (Super Admin) + senha definida na VPS
3. Calcular premiação (teste) e criar torneio Suíço de validação
4. Iniciar, resultados, finalizar, export JSON
5. Gerar convite em `/usuarios` — link com domínio público; testar troca de papel (modal + senha)
6. Upload de avatar e perfil público; troca de e-mail no perfil (dev)
7. `/auditoria` lista ações recentes; `/acoes` cria ação promocional de teste (staff)
8. Backup MySQL (`deploy/backup-db.sh`) + offsite (`deploy/backup-offsite.sh` / cron)

## Desenvolvimento (clone do repositório)

1. Python 3.13 e Node.js 22+
2. `scripts\setup.ps1`
3. Senha do admin (comando impresso pelo setup)
4. `scripts\Iniciar TCG Tools.bat` → `http://127.0.0.1:8000`

Dados em `./data/tcg_tools.db`.

Manual do operador: [OPERADOR.md](OPERADOR.md).

## Backup

| Ambiente | O quê |
|----------|--------|
| **VPS** | `deploy/backup-db.sh` (local) + `deploy/backup-offsite.sh` (Google Drive / rclone) |
| **Dev** | Copiar `./data/tcg_tools.db` |

## Porta ocupada (dev)

```powershell
netstat -ano | findstr :8000
```

Mais problemas: [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

## Referências

- [V2_WEB.md](V2_WEB.md) — produção VPS
- [RUNBOOK_VPS.md](RUNBOOK_VPS.md) — operação (deploy, backup, restore)
- [BUILD_RELEASE.md](BUILD_RELEASE.md) — tags e CI
- [archive/INSTALADOR.md](archive/INSTALADOR.md) — instalador Windows (legado, removido v1.5.0)
