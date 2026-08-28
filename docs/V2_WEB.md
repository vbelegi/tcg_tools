# TCG Tools v2 — hospedagem web (VPS)

Contrato e guia da **Fase 1** (Docker). Single-loja Fourse; instalador LAN permanece até validação do site.

## Escopo

| Incluído na Fase 1 | Fase 3 (web produção) |
|--------------------|------------------------|
| Docker + Compose (app, MySQL 8, Caddy) | Avatares WebP em `users.avatar_blob` |
| `.env` na VPS (segredos fora do git) | `claim_url` absoluto nos convites (`TCGTOOLS_PUBLIC_BASE_URL`) |
| Bootstrap opcional do `admin@local` | Cookies de sessão com flag `Secure` em HTTPS |
| Migrations Alembic no start | — |

Ambientes finais desejados: **dev local** + **VPS**; LAN só enquanto o web não estiver validado.

## Pré-requisitos (VPS)

- Ubuntu 24.04 (ou similar)
- Docker Engine + Compose plugin
- Firewall: 22, 80, 443
- (Produção) DNS A/AAAA do domínio → IP da VPS

## Arquivos

| Path | Função |
|------|--------|
| `Dockerfile` | Build multi-stage (frontend + API) |
| `docker-compose.yml` | `db` + `app` + `caddy` |
| `deploy/Caddyfile` | Reverse proxy / TLS |
| `deploy/docker-entrypoint.sh` | Wait DB → migrate → bootstrap → uvicorn |
| `.env.example` | Modelo de segredos |

## Deploy na VPS

```bash
# como root ou user com docker
mkdir -p /opt/tcg_tools
cd /opt/tcg_tools
git clone https://github.com/vbelegi/tcg_tools.git .
# ou: git pull

cp .env.example .env
nano .env   # MYSQL_* , TCGTOOLS_PUBLIC_BASE_URL, SITE_ADDRESS

docker compose up -d --build
docker compose ps
curl -fsS https://torneios.seudominio.com/api/v1/health
```

Login inicial: **admin@local** + senha do bootstrap. Em seguida **remova** `TCGTOOLS_BOOTSTRAP_ADMIN_PASSWORD` do `.env` e rode `docker compose up -d` de novo (não sobrescreve admin existente).

### SITE_ADDRESS

- `:80` — HTTP pelo IP da VPS (teste)
- `torneios.seudominio.com` — HTTPS (Let's Encrypt); DNS deve apontar antes

### TCGTOOLS_PUBLIC_BASE_URL

- Produção: `https://torneios.seudominio.com` (sem barra final)
- Usado em `claim_url` ao gerar convites em `/usuarios`
- Quando começa com `https://`, cookies de sessão recebem `Secure` automaticamente
- Override: `TCGTOOLS_COOKIE_SECURE=true|false`

### Avatares (Fase 3)

- Upload: `POST /auth/me/avatar` → WebP 256×256 em `users.avatar_blob`
- Leitura: `GET /api/v1/media/avatars/{user_id}`
- Migration `008` importa arquivos antigos de `data/media/avatars/` se existirem
- Backup MySQL inclui avatares (não depende mais de volume de arquivos)

### Backup periódico (recomendado na VPS)

Script manual em `/opt/tcg_tools/scripts/backup-db.sh` (cron diário) — ver runbook do operador ou histórico de deploy.

## Segredos

- Nunca commitar `.env`
- Senha do MySQL e bootstrap só no servidor
- Hash do admin fica no banco após o primeiro boot
- `chmod 600 .env` na VPS

## Dev local (sem Docker)

Continua como hoje: SQLite + `uvicorn` + `npm run dev`. Cookies sem `Secure` quando `TCGTOOLS_PUBLIC_BASE_URL` não é HTTPS.

## Smoke / testes de empacotamento

```powershell
# Na máquina de desenvolvimento (Windows)
Invoke-Pester -Path scripts/tests/Docker.Tests.ps1 -CI
./scripts/validate-prod-lock.ps1
```

Com Docker disponível:

```powershell
docker compose config
# build completo (demorado):
# docker compose build app
```

## Próximas fases

2. ~~Validar stack na VPS Hostinger + domínio~~  
3. ~~Avatares no DB, URL pública, cookies HTTPS~~  
4. Cutover da loja; deprecar LAN  
5. Deploy automático pós-merge em `main` (ou por tag de release)
