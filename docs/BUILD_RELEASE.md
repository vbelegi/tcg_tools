# Build e release — TCG Tools

Produção é **VPS + Docker** ([V2_WEB.md](V2_WEB.md)). Desenvolvimento local usa `scripts/setup.ps1` e `scripts/Iniciar TCG Tools.bat`.

O instalador Windows (`setup.exe`) e o launcher Go foram **removidos na v1.5.0**. Documentação legada: [archive/INSTALADOR.md](archive/INSTALADOR.md).

## Versionamento

- Versão canônica: `backend/pyproject.toml` (`version = "x.y.z"`)
- Tag Git: `vX.Y.Z` deve coincidir com o pyproject (validado no workflow `release.yml`)

## CI

| Workflow | Uso |
|----------|-----|
| `ci.yml` | Backend, frontend, Pester, lockfile (push/PR) |
| `windows-test-suite.yml` | Suite reutilizável (release + PR) |
| `release.yml` | Testes + `docker compose config` + GitHub Release em tag `v*` |

## Release (tag)

```bash
git checkout main
git pull
# CHANGELOG e pyproject já na versão alvo
git tag v1.5.0
git push origin v1.5.0
```

O workflow publica **GitHub Release** com notas geradas (sem artefato `.exe`).

## Deploy na VPS (após merge ou tag)

Manual (passo a passo):

```bash
cd /opt/tcg_tools
git pull origin main
docker compose up -d --build
curl -fsS https://torneios.seudominio.com/api/v1/health
```

Ou com o script unificado ([V2_WEB.md](V2_WEB.md)):

```bash
cd /opt/tcg_tools
chmod +x deploy/vps-deploy.sh
export DEPLOY_REF=main   # ou v1.5.0
./deploy/vps-deploy.sh
```

Recomendado: backup MySQL antes (`deploy/backup-db.sh` ou cron).

## Dev local — validação antes do push

```powershell
cd backend
py -3.13 -m pytest tests/ -v --cov=app --cov-fail-under=80

cd ..\frontend
npm run test
npm run build

Invoke-Pester -Path scripts/tests -CI
./scripts/validate-prod-lock.ps1
```

Com Docker:

```powershell
$env:MYSQL_PASSWORD="test"; $env:MYSQL_ROOT_PASSWORD="test"
docker compose config
```

## Dependências Python (produção Docker)

- Lock: `backend/requirements-prod.lock`
- Validar: `./scripts/validate-prod-lock.ps1`
- Regenerar: `./scripts/update-prod-lock.ps1`

## Próximo

- **Fase 5 (em andamento):** `deploy/vps-deploy.sh`; pendente workflows + secrets
- **Fase 6:** hardening (backup offsite, runbook de update)
