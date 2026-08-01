# Build e release — TCG Tools

## Visão geral

```text
push/tag → GitHub Actions (release.yml)
  → pytest + npm test + go test (≥80%)
  → build-release.ps1
  → dist/TCGTools-{version}-setup.exe
```

## Build local

Pré-requisitos: Python 3.13, Node 22, Go 1.22, [Inno Setup 6](https://jrsoftware.org/isinfo.php).

```powershell
./scripts/build-release.ps1
# Apenas staging, sem Inno:
./scripts/build-release.ps1 -SkipTests -SkipInno
```

Parâmetros:

| Parâmetro | Descrição |
|-----------|-----------|
| `-SkipTests` | Pula pytest/npm/go (útil se testes já rodaram) |
| `-SkipInno` | Gera só `dist/staging/` |
| `-OutputDir` | Pasta de saída alternativa |
| `-Version` | Sobrescreve versão do pyproject.toml |

## Artifacts CI

| Trigger | Artefato |
|---------|----------|
| Tag `v*` | GitHub Release + `TCGTools-{version}-setup.exe` |
| Push `main` | Artifact pre-release |
| Push branch | `TCGTools-{branch}-{sha}-setup.exe` |

Tag deve coincidir com `version` em `backend/pyproject.toml`.

## Cache

O workflow usa cache npm/go. Python embeddable é baixado no job de build (cache manual futuro).

## Testes de scripts

```powershell
Install-Module Pester -Force -Scope CurrentUser
Invoke-Pester -Path scripts/tests
```

## Checklist VM (validação manual)

1. Windows limpo, sem Python/Node pré-instalados
2. Executar `TCGTools-x.y.z-setup.exe` offline
3. Atalho → browser abre app; criar torneio
4. Encerrar pelo tray → reabrir → dados persistem em `%APPDATA%\TCGTools\`
5. Instalar versão nova por cima → DB preservado
6. Segundo clique no atalho com app rodando → browser + aviso
7. Alterar `port` em `launcher_config.json` → restart aplica nova porta
8. Desinstalar → confirma remoção → `%APPDATA%\TCGTools\` removido

## Conteúdo do staging

```text
dist/staging/
├── TCGTools.exe
├── VERSION.txt
├── runtime/python/
├── backend/
└── frontend/dist/
```
