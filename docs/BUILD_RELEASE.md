# Build e release — TCG Tools

## Visão geral

```text
push/tag → GitHub Actions (release.yml)
  → windows-test-suite (reutilizável)
  → validate-prod-lock.ps1
  → build-release.ps1
  → test-staging.ps1 (smoke health)
  → dist/TCGTools-{version}-setup.exe
```

## Build local

Pré-requisitos: Python 3.13, Node 22, Go 1.22+, [Inno Setup 6](https://jrsoftware.org/isinfo.php).

**Go local:** instale [Go 1.22+](https://go.dev/dl/) para compilar/testar o launcher antes do push. Sem Go, `build-release.ps1` falha na etapa do launcher; testes Go rodam no CI (`ci.yml` / `windows-test-suite.yml`).

O build do launcher gera `rsrc_windows_amd64.syso` a partir de `launcher/internal/app/assets/icon.ico` (ícone do `.exe`/atalhos). A bandeja continua usando o mesmo arquivo via `go:embed`.

```powershell
./scripts/build-release.ps1
# Apenas staging, sem Inno:
./scripts/build-release.ps1 -SkipTests -SkipInno
# Smoke após staging:
./scripts/test-staging.ps1
```

Parâmetros:

| Parâmetro | Descrição |
|-----------|-----------|
| `-SkipTests` | Pula pytest/npm/go (útil se testes já rodaram) |
| `-SkipInno` | Gera só `dist/staging/` |
| `-OutputDir` | Pasta de saída alternativa |
| `-Version` | Sobrescreve versão do pyproject.toml |

## Dependências Python (reproducibilidade)

- Lock pinado: `backend/requirements-prod.lock` (formato `pacote==versao`)
- Validar: `./scripts/validate-prod-lock.ps1`
- Regenerar após bump de deps: `./scripts/update-prod-lock.ps1`

Build de release usa **dois layers** (sem `pip install .` no embed):

1. **Deps de terceiros** — `pip install -r requirements-prod.lock` no Python embeddable (`runtime/python/Lib/site-packages`)
2. **Payload da aplicação** — cópia de `backend/` para staging; uvicorn roda com `cwd=backend/` (`python -m uvicorn app.main:app`)

O embed não compila o pacote local (sem setuptools no runtime). Dev continua com `pip install -e backend[dev]`.

## CI reutilizável

| Workflow | Uso |
|----------|-----|
| `ci.yml` | Jobs paralelos (backend, frontend, launcher, pester) via `scripts/ci/*.ps1` |
| `windows-test-suite.yml` | `workflow_call` — suite completa (release + PR) |
| `release.yml` | Test suite + build Inno + smoke staging |

## Artifacts CI

| Trigger | Artefato |
|---------|----------|
| Tag `v*` | GitHub Release + `TCGTools-{version}-setup.exe` |
| Push `main` | Artifact pre-release |
| Push branch (paths release) | `TCGTools-{branch}-{sha}-setup.exe` |

Tag deve coincidir com `version` em `backend/pyproject.toml`.

## Testes de scripts

```powershell
Install-PackageProvider -Name NuGet -MinimumVersion 2.8.5.201 -Force
Install-Module Pester -Force -Scope CurrentUser
Invoke-Pester -Path scripts/tests -CI
./scripts/validate-prod-lock.ps1
```

Ou suite completa:

```powershell
./scripts/ci/run-windows-test-suite.ps1
```

## Checklist VM (validação manual — pendente)

1. Windows limpo, sem Python/Node pré-instalados
2. Executar `TCGTools-x.y.z-setup.exe` offline
3. Atalho → browser abre app; criar torneio
4. Encerrar pelo tray → reabrir → dados persistem em `%APPDATA%\TCGTools\`
5. Instalar versão nova por cima → DB preservado; wizard atualiza config
6. Segundo clique no atalho com app rodando → browser + aviso
7. Alterar `port` em `launcher_config.json` → restart aplica nova porta
8. Desinstalar **sem** marcar remoção de dados → `%APPDATA%\TCGTools\` preservado
9. Desinstalar **com** remoção de dados → pasta apagada

## Conteúdo do staging

```text
dist/staging/
├── TCGTools.exe
├── VERSION.txt
├── runtime/python/
├── backend/
└── frontend/dist/
```
