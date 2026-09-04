# TCG Tools

Aplicação web para gestão de torneios TCG: premiação, organização Suíço/Eliminatória, Fourse Points e export de logs.

**Produção (Fourse):** site hospedado na VPS — [docs/V2_WEB.md](docs/V2_WEB.md), runbook [docs/RUNBOOK_VPS.md](docs/RUNBOOK_VPS.md).  
**Desenvolvimento:** SQLite local no Windows — seções abaixo.

## Requisitos (dev)

- Windows 10+ (ou Linux/macOS com Python/Node)
- Python **3.13** (recomendado; prefixe `py -3.13` se o padrão for outra versão)
- Node.js 18+

## Desenvolvimento

### Setup rápido (Windows)

```powershell
scripts\setup.ps1
scripts\Iniciar TCG Tools.bat
```

Dados em `./data/` (SQLite). Defina a senha do Super Admin bootstrap (`admin@local`):

```powershell
$env:TCGTOOLS_DATA_DIR='.\data'; cd backend; py -3.13 -m app.scripts.set_admin_password --password admin123
```

### Backend / frontend separados

```powershell
cd backend
py -3.13 -m pip install -e ".[dev]"
py -3.13 -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

cd frontend
npm install
npm run dev    # http://127.0.0.1:5173 (proxy /api)
npm run test
```

## Produção (VPS)

Deploy Docker: [docs/V2_WEB.md](docs/V2_WEB.md).

```bash
cd /opt/tcg_tools
git pull origin main
docker compose up -d --build
```

## Testes

```powershell
cd backend
py -3.13 -m pytest tests/ -v --cov=app --cov-fail-under=80

cd ..\frontend
npm run test

Invoke-Pester -Path scripts/tests -CI
```

CI: pytest, frontend Vitest, Pester, Docker packaging tests.

## Estrutura

```
tcg_tools/
├── backend/          # FastAPI, Alembic, testes
├── frontend/         # React + Vite
├── deploy/           # Caddy, entrypoint, backup-db.sh
├── scripts/          # setup.ps1, CI helpers
├── Dockerfile
└── docker-compose.yml
```

## Funcionalidades

- **Premiação:** calcular split, tabela, presets, export CSV
- **Torneios:** Suíço e Eliminatória, pairings, FP, torneios externos; busca/filtros na lista
- **Agenda / Calendário:** eventos e faixas de ações promocionais
- **Ações promocionais:** inscrição por QR, regulamento PDF, sorteio
- **Sorteador:** sorteio em lote ou encadeado
- **Usuários:** papéis player/staff/admin/Super Admin; convites; troca de e-mail; logs de auditoria
- **Decklists:** opcional após finalizar torneio

## Documentação

| Documento | Conteúdo |
|-----------|----------|
| [docs/V2_WEB.md](docs/V2_WEB.md) | **Produção VPS / Docker** |
| [docs/RUNBOOK_VPS.md](docs/RUNBOOK_VPS.md) | **Runbook operação VPS** |
| [docs/OPERADOR.md](docs/OPERADOR.md) | Manual do mesário |
| [docs/INSTALACAO.md](docs/INSTALACAO.md) | Checklist pós-deploy |
| [docs/BUILD_RELEASE.md](docs/BUILD_RELEASE.md) | Tags, CI, release |
| [docs/PLATFORM_USERS_FP.md](docs/PLATFORM_USERS_FP.md) | Usuários e FP |
| [docs/PRIVACIDADE.md](docs/PRIVACIDADE.md) | LGPD / marketing / exclusão |
| [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | Problemas comuns |
| [docs/configuracao.md](docs/configuracao.md) | Presets, env vars |
| [CHANGELOG.md](CHANGELOG.md) | Histórico de versões |
