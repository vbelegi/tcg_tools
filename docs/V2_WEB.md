# TCG Tools v2 — hospedagem web (VPS)

Contrato e guia da **Fase 1** (Docker). Single-loja Fourse; instalador LAN permanece até validação do site.

## Escopo

| Incluído na Fase 1 | Depois |
|--------------------|--------|
| Docker + Compose (app, MySQL 8, Caddy) | Avatares em BLOB no banco |
| `.env` na VPS (segredos fora do git) | `PUBLIC_BASE_URL` nos convites |
| Bootstrap opcional do `admin@local` | Cookies `Secure` / CD automático |
| Migrations Alembic no start | Remoção do instalador LAN |

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
nano .env   # MYSQL_* , TCGTOOLS_BOOTSTRAP_ADMIN_PASSWORD, SITE_ADDRESS

docker compose up -d --build
docker compose ps
curl -fsS http://127.0.0.1/api/v1/health
```

Login inicial: **admin@local** + senha do bootstrap. Em seguida **remova** `TCGTOOLS_BOOTSTRAP_ADMIN_PASSWORD` do `.env` e rode `docker compose up -d` de novo (não sobrescreve admin existente).

### SITE_ADDRESS

- `:80` — HTTP pelo IP da VPS (teste)
- `torneios.seudominio.com` — HTTPS (Let's Encrypt); DNS deve apontar antes

## Segredos

- Nunca commitar `.env`
- Senha do MySQL e bootstrap só no servidor
- Hash do admin fica no banco após o primeiro boot

## Dev local (sem Docker)

Continua como hoje: SQLite + `uvicorn` + `npm run dev`. O instalador Windows/LAN ainda é suportado nesta fase.

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

2. Validar stack na VPS Hostinger + domínio  
3. Avatares no DB, URL pública, cookies HTTPS  
4. Cutover da loja; deprecar LAN  
5. Deploy automático pós-merge em `main`
