# TCG Tools



Aplicação web local para gestão de torneios TCG na loja: premiação, organização Suíço/Eliminatória e export de logs.



## Requisitos



- Windows 10+

- Python **3.13** (recomendado; `py` padrão no Windows pode apontar para 3.14)

- Node.js 18+ (apenas para build do frontend)



> **Nota:** Se `py` usar 3.14 por padrão, prefixe comandos com `py -3.13` ou use `scripts\Iniciar TCG Tools.bat`.



## Desenvolvimento



### Backend



```powershell

cd backend

py -3.13 -m pip install -e ".[dev]"

py -3.13 -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

```



### Frontend



```powershell

cd frontend

npm install

npm run dev          # desenvolvimento

npm run generate:api # regenerar tipos TypeScript a partir do OpenAPI

npm run build

npm run test         # Vitest

```



Acesse `http://127.0.0.1:5173` (proxy `/api` → backend).

**Login (obrigatório):** após o setup, defina a senha do `admin`:

```powershell
$env:TCGTOOLS_DATA_DIR='.\data'; cd backend; py -3.13 -m app.scripts.set_admin_password --password admin123
```

(O `scripts\setup.ps1` imprime o comando equivalente para o data dir em uso.)



### Produção local



```powershell

cd frontend

npm run build

cd ..\backend

py -3.13 -m uvicorn app.main:app --host 127.0.0.1 --port 8000

```



Acesse `http://127.0.0.1:8000`



## Instalação na loja

1. Baixe e execute `TCGTools-{versão}-setup.exe` ([docs/INSTALADOR.md](docs/INSTALADOR.md))
2. Use o atalho **TCG Tools** (launcher com bandeja do sistema)

Checklist: [docs/INSTALACAO.md](docs/INSTALACAO.md) · Build/release: [docs/BUILD_RELEASE.md](docs/BUILD_RELEASE.md)

**Dados:** `%APPDATA%\TCGTools\` (SQLite, exports, logs) · **Dev:** `./data/` via `scripts\setup.ps1`  

**Logs de torneios:** `./logs/` (JSON exportados)  

**CSV de premiação:** `./exports/` (gerados sob demanda)



## Testes



```powershell

cd backend

py -3.13 -m pytest tests/ -v --cov=app --cov-fail-under=80



cd ..\frontend

npm run test

cd ..\launcher

go test ./...

```



CI (GitHub Actions): pytest + coverage ≥80%, frontend test + build.



## Estrutura



```

tcg_tools/

├── backend/

│   ├── app/              # FastAPI, core, services, models

│   ├── config/           # premiacao_presets.json

│   ├── alembic/          # migrações SQLite

│   └── tests/            # unit, integration, db (Alembic fixtures)

├── frontend/             # React + Vite + TypeScript

├── launcher/             # TCGTools.exe (Go, bandeja do sistema)

├── scripts/              # setup.ps1, build-release.ps1, installer.iss

├── config/               # settings.json legado (migração one-shot)

├── exports/              # CSV gerados (gitignored)

└── logs/                 # JSON de torneios exportados

```



## Funcionalidades



- **Premiação:** calcular split, tabela, presets, export CSV

- **Torneios:** Suíço e Eliminatória, pairings, resultados, reabrir rodada, premiação integrada, log JSON

- **Sorteador:** sorteio em lote ou encadeado

- **Auth / LAN:** login `admin`; acesso opcional na rede local

- **Decklists:** opcional após finalizar torneio



## Documentação



| Documento | Conteúdo |

|-----------|----------|

| [docs/OPERADOR.md](docs/OPERADOR.md) | Manual do mesário, fluxograma |

| [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | Problemas comuns e soluções |

| [docs/INSTALADOR.md](docs/INSTALADOR.md) | Instalador setup.exe e atualizações |
| [docs/BUILD_RELEASE.md](docs/BUILD_RELEASE.md) | Pipeline de build e checklist VM |

| [docs/modelo_premiacao.md](docs/modelo_premiacao.md) | Fórmulas e parâmetros do split |

| [docs/configuracao.md](docs/configuracao.md) | Presets JSON, exports, variáveis de ambiente |

| [docs/INSTALACAO.md](docs/INSTALACAO.md) | Checklist loja, backup |

| [CHANGELOG.md](CHANGELOG.md) | Histórico de versões |

