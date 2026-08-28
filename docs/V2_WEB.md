# TCG Tools v2 — hospedagem web (VPS)

Guia de deploy Docker para produção. Ambientes oficiais: **dev local** + **VPS**.

## Escopo por fase

| Fase | Conteúdo | Status |
|------|----------|--------|
| 1 | Docker + Compose (app, MySQL 8, Caddy) | Concluída |
| 2 | VPS + domínio + HTTPS | Concluída |
| 3 | Avatares no DB, `claim_url`, cookies `Secure` | Concluída |
| 4 | Cutover web; remover instalador LAN / launcher | Concluída (v1.5.0) |
| 5 | Deploy automático na VPS | Planejada |
| 6 | Hardening (backup offsite, runbook update, Cloudflare) | Planejada |

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

Login inicial: **admin@local** + senha do bootstrap. Remova `TCGTOOLS_BOOTSTRAP_ADMIN_PASSWORD` do `.env` após o primeiro login.

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

```bash
chmod 700 deploy/backup-db.sh
./deploy/backup-db.sh
# cron diário recomendado — ver INSTALACAO.md
```

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

## Próximas fases

5. Deploy automático (tag `v*` ou workflow manual)  
6. Backup offsite, runbook operacional, revisão Cloudflare SSL
