# TCG Tools Launcher

Launcher Windows (`TCGTools.exe`) com bandeja do sistema: inicia uvicorn, abre o navegador e gerencia ciclo de vida do servidor local.

## Pré-requisitos

- Go **1.22+** ([download](https://go.dev/dl/))
- Windows (build alvo)

Sem Go instalado localmente, os testes/build do launcher rodam no CI; instale Go para validar antes do push.

## Estrutura

```text
launcher/
├── main.go
├── assets/icon.ico          # embarcado via go:embed
└── internal/
    ├── app/
    ├── config/              # launcher_config.json em %APPDATA%\TCGTools
    ├── instance/            # mutex Local\TCGTools_SingleInstance (multi-user)
    ├── process/             # spawn uvicorn, Job Object, health check
    ├── tray/                # wrapper energye/systray
    ├── registry/
    └── browser/
```

## Comandos

```powershell
cd launcher
go mod tidy
go test ./... -coverprofile=coverage.out
go tool cover -func coverage.out
go build -ldflags "-H windowsgui -s -w" -o TCGTools.exe .
```

Ou via CI script:

```powershell
./scripts/ci/run-launcher-tests.ps1
```

## Cobertura

Meta **≥80%** (gate no CI). Pacotes testados: `config`, `process`, `registry`, `instance`, `app`, `tray/labels`.

## Single-instance (multi-user)

Mutex: `Local\TCGTools_SingleInstance` — uma instância **por sessão de usuário Windows** (vários logins na mesma máquina podem rodar em paralelo, cada um com `%APPDATA%\TCGTools\`).

O mesmo mutex é usado por `scripts/lib/Instance-Lock.ps1` (dev `.bat` / `start-dev.ps1`).

## Configuração

Arquivo `%APPDATA%\TCGTools\launcher_config.json`:

```json
{
  "port": 8000,
  "start_with_windows": false
}
```

JSON inválido é copiado para `.bak` e recriado com defaults. Log: `%APPDATA%\TCGTools\launcher.log` (com timestamp).

## Systray

Usa [`github.com/energye/systray`](https://github.com/energye/systray) v1.0.3 (pure Go, sem CGO).

Menu: Abrir, Sobre, pastas (dados/exports/logs), autostart, Encerrar.

## Processo filho

- uvicorn spawnado sem janela (`CREATE_NO_WINDOW`)
- Job Object Windows com `KILL_ON_JOB_CLOSE`
- Health: `GET /api/v1/health` com `"app":"tcg_tools"`
- Checagem de porta livre antes do spawn
