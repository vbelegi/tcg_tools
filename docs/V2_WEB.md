# TCG Tools v2 — hospedagem web (VPS)

Guia de deploy Docker para produção. Ambientes oficiais: **dev local** + **VPS**.

## Escopo por fase

| Fase | Conteúdo | Status |
|------|----------|--------|
| 1 | Docker + Compose (app, MySQL 8, Caddy) | Concluída |
| 2 | VPS + domínio + HTTPS | Concluída |
| 3 | Avatares no DB, `claim_url`, cookies `Secure` | Concluída |
| 4 | Cutover web; remover instalador LAN / launcher | Concluída (v1.5.0) |
| 5 | Deploy automático na VPS | Concluída (v1.6.0) |
| 6 | Hardening (backup offsite, runbook) | Concluída (v1.7.0) |

## Pré-requisitos (VPS)

- Ubuntu 24.04 (ou similar)
- Docker Engine + Compose plugin
- Firewall: 22, 80, 443
- DNS do domínio → VPS (Cloudflare proxied ok)

## Arquivos

| Path | Função |
|------|--------|
| `Dockerfile` | Build multi-stage (frontend + API) |
| `docker-compose.yml` | `db` + `app` + `caddy` |
| `deploy/Caddyfile` | Reverse proxy / TLS |
| `deploy/docker-entrypoint.sh` | Wait DB → migrate → bootstrap → uvicorn |
| `deploy/backup-db.sh` | Dump MySQL (cron) |
| `deploy/backup-offsite.sh` | Upload dumps para Google Drive (rclone) |
| `docs/RUNBOOK_VPS.md` | Runbook operacional (deploy, backup, restore) |
| `deploy/vps-deploy.sh` | Deploy na VPS: backup → git checkout → compose → health |
| `.env.example` | Modelo de segredos |

## Deploy inicial na VPS

```bash
mkdir -p /opt/tcg_tools
cd /opt/tcg_tools
git clone https://github.com/vbelegi/tcg_tools.git .

cp .env.example .env
nano .env   # MYSQL_* , TCGTOOLS_PUBLIC_BASE_URL, SITE_ADDRESS

docker compose up -d --build
docker compose ps
curl -fsS https://torneios.seudominio.com/api/v1/health
```

Login inicial: **admin@local** (papel **Super Admin**) + senha do bootstrap. Remova `TCGTOOLS_BOOTSTRAP_ADMIN_PASSWORD` do `.env` após o primeiro login.

## Atualizar produção (release)

```bash
cd /opt/tcg_tools
# opcional: ./scripts/backup-db.sh ou deploy/backup-db.sh
git pull origin main
docker compose up -d --build
docker compose ps
curl -fsS https://torneios.seudominio.com/api/v1/health
```

Use `--build` quando mudar código, Dockerfile ou dependências. Só `.env` → `docker compose up -d`.

### Script `deploy/vps-deploy.sh` (Fase 5)

Após `git pull` trazer o script na VPS:

```bash
chmod +x deploy/vps-deploy.sh deploy/backup-db.sh
```

Deploy da branch `main`:

```bash
cd /opt/tcg_tools
export DEPLOY_REF=main
./deploy/vps-deploy.sh
```

Deploy de uma tag (ex.: release):

```bash
export DEPLOY_REF=v1.5.0
./deploy/vps-deploy.sh
```

Variáveis opcionais:

| Variável | Padrão | Uso |
|----------|--------|-----|
| `TCGTOOLS_DEPLOY_PATH` | `/opt/tcg_tools` | Diretório do clone |
| `DEPLOY_REF` | `main` | Branch, tag ou commit |
| `SKIP_BACKUP` | `0` | `1` pula backup pré-deploy |
| `HEALTH_RETRIES` | `30` | Tentativas do health check |
| `HEALTH_SLEEP_SEC` | `5` | Intervalo entre tentativas |

O script: backup MySQL → `git fetch` + checkout → `docker compose up -d --build` → health em `http://127.0.0.1:8000/api/v1/health` (dentro do container `app`).

**Pré-requisito na VPS:** `git fetch` via SSH (deploy key) — ver seção abaixo.

### SITE_ADDRESS

- `torneios.seudominio.com` — HTTPS (produção)
- `:80` — HTTP pelo IP (teste)

### TCGTOOLS_PUBLIC_BASE_URL

- `https://torneios.seudominio.com` (sem barra final)
- Convites em `/usuarios` usam `claim_url` absoluto
- Cookies `Secure` quando URL é HTTPS

### Avatares

- Upload: `POST /auth/me/avatar` → `users.avatar_blob`
- Leitura: `GET /api/v1/media/avatars/{user_id}`
- Favicon: `frontend/public/favicon.ico`

### Backup

Local (MySQL dump):

```bash
chmod 700 deploy/backup-db.sh deploy/backup-offsite.sh
./deploy/backup-db.sh
# cron diário recomendado — ver abaixo
```

Offsite (Google Drive via rclone):

1. Na VPS: `apt install rclone` e `rclone config` (remote ex. `tcg_backup`)
2. No `.env` (opcional se usar os padrões abaixo):

```bash
BACKUP_RCLONE_REMOTE=tcg_backup
BACKUP_RCLONE_PATH=tcg_tools-backups
```

3. Upload:

```bash
./deploy/backup-offsite.sh
```

Cron sugerido:

```cron
0 3 * * * /opt/tcg_tools/deploy/backup-db.sh >> /opt/tcg_tools/backups/backup.log 2>&1
15 3 * * * /opt/tcg_tools/deploy/backup-offsite.sh >> /opt/tcg_tools/backups/offsite.log 2>&1
```

Retenção local: 14 dias (`backup-db.sh`). No Drive, limpe arquivos antigos manualmente ou com política do Google.

Runbook completo (deploy, restore, incidentes): [RUNBOOK_VPS.md](RUNBOOK_VPS.md).

## Segredos

- Nunca commitar `.env`
- `chmod 600 .env` na VPS
- Senhas MySQL só no servidor

## Dev local (sem Docker)

`scripts/setup.ps1` + `scripts/Iniciar TCG Tools.bat` ou `uvicorn` + `npm run dev`. Dados em `./data/`.

## Smoke (dev machine)

```powershell
Invoke-Pester -Path scripts/tests/Docker.Tests.ps1 -CI
./scripts/validate-prod-lock.ps1
docker compose config
```

## Futuro (opcional)

- Revisão Cloudflare (cache, SSL) — quando necessário

## Deploy automático (GitHub Actions)

Secrets no environment **`production`** (recomendado: aprovação manual antes do deploy):

| Secret | Uso |
|--------|-----|
| `VPS_SSH_HOST` | IP ou hostname da VPS |
| `VPS_SSH_USER` | ex.: `root` |
| `VPS_SSH_KEY` | chave privada `tcg_tools_deploy` (Actions → VPS) |
| `VPS_DEPLOY_PATH` | opcional; padrão `/opt/tcg_tools` |

| Workflow | Quando |
|----------|--------|
| **Deploy VPS** (`deploy-vps.yml`) | Manual — Actions → escolher `ref` (ex. `main`, `v1.6.0`) |
| **Release** (`release.yml`) | Tag `v*` → testes → GitHub Release → deploy na VPS |

Na VPS, o job SSH executa `deploy/vps-deploy.sh` (backup → git checkout → compose → health).

## VPS — chaves SSH (deploy automático)

Duas chaves distintas:

| Chave | Uso | Pública em | Privada em |
|-------|-----|------------|------------|
| Actions (`tcg_tools_deploy`) | GitHub Actions → SSH na VPS | VPS `~/.ssh/authorized_keys` | Secret `VPS_SSH_KEY` |
| Git (`tcg_tools_git`) | VPS → `git fetch` / `git pull` | GitHub **Deploy keys** (read-only) | VPS `~/.ssh/tcg_tools_git` |

Na VPS, `~/.ssh/config` para GitHub:

```
Host github.com
  HostName github.com
  User git
  IdentityFile ~/.ssh/tcg_tools_git
  IdentitiesOnly yes
```

```bash
cd /opt/tcg_tools
git remote set-url origin git@github.com:vbelegi/tcg_tools.git
ssh -T git@github.com
git fetch origin
```

