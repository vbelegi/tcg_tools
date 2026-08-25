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
├── rsrc_windows_amd64.syso  # gerado no build (ícone PE); gitignored
└── internal/
    ├── app/
    │   └── assets/icon.ico  # bandeja (go:embed) + fonte do .syso
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
go run github.com/akavel/rsrc@v0.10.2 -arch amd64 -ico internal/app/assets/icon.ico -o rsrc_windows_amd64.syso
go test ./... -coverprofile=coverage.out
go tool cover -func coverage.out
go build -ldflags "-H windowsgui -s -w" -o TCGTools.exe .
```

O `.syso` incorpora o ícone nos recursos do PE (Explorer, atalhos, desinstalador). O `go:embed` do mesmo `.ico` continua sendo usado só pela bandeja em runtime. `launcher/*.syso` está no `.gitignore`.

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
  "start_with_windows": false,
  "lan_access": false
}
```

Com `lan_access: true`, o uvicorn escuta em `0.0.0.0` (acesso na LAN). JSON inválido é copiado para `.bak` e recriado com defaults. Log: `%APPDATA%\TCGTools\launcher.log` (com timestamp).

## Systray

Usa [`github.com/energye/systray`](https://github.com/energye/systray) v1.0.3 (pure Go, sem CGO).

Menu: Abrir, Sobre, pastas (dados/exports/logs), **Copiar URL da rede (LAN)** (quando `lan_access`), autostart, Encerrar.

## Processo filho

- uvicorn spawnado sem janela (`CREATE_NO_WINDOW`)
- Job Object Windows com `KILL_ON_JOB_CLOSE`
- Health: `GET /api/v1/health` com `"app":"tcg_tools"`
- Checagem de porta livre antes do spawn
