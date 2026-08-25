# Instalação — TCG Tools (loja)

## Instalação recomendada (produção)

1. Baixe `TCGTools-{versão}-setup.exe` ([INSTALADOR.md](INSTALADOR.md))
2. Execute o instalador (admin)
3. Abra o atalho **TCG Tools** na bandeja / navegador
4. Siga o checklist abaixo para validar

Dados em `%APPDATA%\TCGTools\` (SQLite, exports, logs). Configuração em `launcher_config.json` — ver [configuracao.md](configuracao.md).

## Checklist manual (12 passos)

1. Abrir `http://127.0.0.1:8000` (ou porta configurada) e entrar com **admin** + senha do instalador
2. Calcular premiação para 16 jogadores com valor de inscrição
3. Criar torneio Suíço com 4 jogadores
4. Iniciar, informar resultados, **concluir** rodada 1
5. Na tela **Entre rodadas**, opcionalmente testar drop ou **reabrir rodada**
6. Iniciar rodada 2, concluir todas as rodadas
7. Finalizar e verificar premiação + classificação
8. Exportar log JSON
9. Encerrar pelo tray e reabrir pelo atalho — torneio persiste
10. (Opcional) Testar segunda instância do atalho — browser abre, aviso exibido
11. Backup de `tcg_tools.db`
12. Documentar versão em **Sobre** no menu da bandeja

## Desenvolvimento (clone do repositório)

1. Instalar Python 3.13 e Node.js 22+
2. Executar `scripts\setup.ps1`
3. Definir senha do admin (comando impresso pelo setup)
4. Executar `scripts\Iniciar TCG Tools.bat`

Manual do operador: [OPERADOR.md](OPERADOR.md)

## Backup

Copie `%APPDATA%\TCGTools\tcg_tools.db` (instalação via setup.exe) ou `./data/tcg_tools.db` em desenvolvimento.

Exports e logs: `%APPDATA%\TCGTools\exports\` e `%APPDATA%\TCGTools\logs\` (produção).

## Porta ocupada

Altere `launcher_config.json` ou encerre o processo na porta:

```powershell
netstat -ano | findstr :8000
```

Mais problemas: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

## Variáveis de ambiente

| Variável | Descrição |
|----------|-----------|
| `TCGTOOLS_DATA_DIR` | Pasta de dados (SQLite) |
| `TCGTOOLS_DATABASE_URL` | URL SQLAlchemy (opcional) |

## Python embeddable (desenvolvimento)

Se `py -3.13` e `uv` não estiverem disponíveis, `scripts\setup.ps1` baixa o Python 3.13 embeddable para `runtime\python\`.

## Referências

- [INSTALADOR.md](INSTALADOR.md) — setup.exe para a loja
- [BUILD_RELEASE.md](BUILD_RELEASE.md) — pipeline de release
