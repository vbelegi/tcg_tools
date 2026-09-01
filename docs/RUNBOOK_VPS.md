# Runbook — produção VPS (TCG Tools)

Operação diária do ambiente Docker na Hostinger. Deploy inicial e arquitetura: [V2_WEB.md](V2_WEB.md).

| Item | Valor típico |
|------|----------------|
| URL | `https://torneios.fourse.com.br` |
| Path no servidor | `/opt/tcg_tools` |
| Stack | `db` (MySQL 8) + `app` (FastAPI) + `caddy` (HTTPS) |
| Dados MySQL | volume Docker `tcg_mysql_data` |
| Uploads / exports app | volume `tcg_app_data` → `/data` no container |

## Deploy

### Automático (release)

1. Merge em `main` com versão no `pyproject.toml` e CHANGELOG
2. `git tag vX.Y.Z && git push origin vX.Y.Z`
3. Workflow **Release**: testes → GitHub Release → job **deploy-vps**
4. Aprovar environment **`production`** no GitHub se configurado

### Manual (GitHub Actions)

**Actions → Deploy VPS → Run workflow**

- `ref`: `main` ou `vX.Y.Z`
- `skip_backup`: desmarcado (recomendado)

### Manual (SSH na VPS)

```bash
cd /opt/tcg_tools
export DEPLOY_REF=main          # ou v1.6.0
./deploy/vps-deploy.sh
```

O script: backup MySQL → `git fetch`/checkout → `docker compose up -d --build` → health check.

### Rollback

```bash
cd /opt/tcg_tools
export DEPLOY_REF=v1.5.0        # tag estável anterior
./deploy/vps-deploy.sh
```

## Health e status

```bash
cd /opt/tcg_tools
docker compose ps
curl -fsS https://torneios.fourse.com.br/api/v1/health
docker compose exec app curl -fsS http://127.0.0.1:8000/api/v1/health
```

Resposta esperada: `{"status":"ok",...}`.

## Logs

```bash
docker compose logs app --tail 80
docker compose logs db --tail 40
docker compose logs caddy --tail 40
docker compose logs -f app          # follow
```

## Backup

### Local (MySQL)

```bash
cd /opt/tcg_tools
./deploy/backup-db.sh
ls -lah backups/
```

Retenção local: **14 dias** (script apaga dumps mais antigos).

Cron sugerido:

```cron
0 3 * * * /opt/tcg_tools/deploy/backup-db.sh >> /opt/tcg_tools/backups/backup.log 2>&1
```

### Offsite (Google Drive / rclone)

Pré-requisito: remote `tcg_backup` (ou valor em `.env`).

```bash
cd /opt/tcg_tools
./deploy/backup-offsite.sh
rclone ls tcg_backup:tcg_tools-backups/
```

Variáveis opcionais no `.env`:

```bash
BACKUP_RCLONE_REMOTE=tcg_backup
BACKUP_RCLONE_PATH=tcg_tools-backups
```

Cron sugerido (após backup local):

```cron
15 3 * * * /opt/tcg_tools/deploy/backup-offsite.sh >> /opt/tcg_tools/backups/offsite.log 2>&1
```

## Restore MySQL

**Cuidado:** sobrescreve o banco atual. Faça backup antes.

1. Escolha o dump (local ou baixe do Drive com `rclone copy`).

```bash
cd /opt/tcg_tools
# Exemplo: dump local
DUMP=backups/tcg_tools-2026-08-31_0300.sql.gz
```

2. Pare o app para evitar escrita durante o restore:

```bash
docker compose stop app
```

3. Importe:

```bash
gunzip -c "$DUMP" | docker compose exec -T db sh -c \
  'mysql -u root -p"$MYSQL_ROOT_PASSWORD" "$MYSQL_DATABASE"'
```

4. Suba o app e valide:

```bash
docker compose up -d app
docker compose exec app curl -fsS http://127.0.0.1:8000/api/v1/health
```

Teste login e um torneio na UI.

### Validar backups (recomendado)

Após configurar cron local + offsite, execute um **restore de teste** em horário de baixo movimento (pode ser em clone do dump, não em produção). Confirme login, torneios e avatares. Anote data e dump usado nesta seção para referência da equipe.

**Deploy v1.9+:** a migration `010` invalida sessões ativas — usuários precisam fazer login novamente após o deploy.

## Senha do admin

Conta bootstrap: **admin@local**.

```bash
cd /opt/tcg_tools
docker compose exec app python -m app.scripts.set_admin_password --password 'SuaSenhaSegura'
```

Remova `TCGTOOLS_BOOTSTRAP_ADMIN_PASSWORD` do `.env` após o primeiro login em produção.

## Segredos e acesso

| O quê | Onde |
|-------|------|
| MySQL, URL pública, Caddy | `/opt/tcg_tools/.env` (`chmod 600`) |
| Deploy automático (SSH) | GitHub → environment **production** (`VPS_SSH_*`) |
| Git pull na VPS | Deploy key + `~/.ssh/tcg_tools_git` |
| OAuth rclone | `~/.config/rclone/rclone.conf` (não commitar) |

### Chaves SSH

| Chave | Uso |
|-------|-----|
| `tcg_tools_deploy` | GitHub Actions → SSH na VPS |
| `tcg_tools_git` | VPS → `git fetch` / `git pull` |

Detalhes: [V2_WEB.md — chaves SSH](V2_WEB.md#vps--chaves-ssh-deploy-automático).

## Problemas comuns

| Sintoma | Ação |
|---------|------|
| 502 / site fora | `docker compose ps`, `docker compose logs app`, `docker compose up -d --build` |
| Health falha após deploy | Aguardar migrate; ver logs do `app`; conferir `.env` (MySQL, URL) |
| `git pull` negado | Deploy key / `ssh -T git@github.com` |
| Disco cheio | `df -h`, limpar `backups/` antigos, `docker system prune` (cuidado) |
| Favicon antigo no browser | Purge cache Cloudflare em `/favicon.ico` |
| Convites com URL errada | `TCGTOOLS_PUBLIC_BASE_URL` no `.env` + `docker compose up -d` |
| E-mails não chegam | Conferir `TCGTOOLS_SMTP_*` no `.env`, logs `docker compose logs app`, SPF/DKIM no domínio |

Mais cenários: [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

## Referências

- [V2_WEB.md](V2_WEB.md) — deploy, fases, Actions
- [BUILD_RELEASE.md](BUILD_RELEASE.md) — tags e CI
- [INSTALACAO.md](INSTALACAO.md) — checklist pós-deploy
- [OPERADOR.md](OPERADOR.md) — uso do sistema na loja
