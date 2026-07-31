# Instalação — TCG Tools (loja)

## Checklist manual (12 passos)

1. Instalar **Python 3.13** e Node.js 18+ (ou executar `scripts\setup.ps1`)
2. Executar `scripts\setup.ps1` na raiz do projeto
3. Executar `scripts\Iniciar TCG Tools.bat`
4. Abrir `http://127.0.0.1:8000` no navegador
5. Calcular premiação para 16 jogadores com valor de inscrição
6. Criar torneio Suíço com 4 jogadores
7. Iniciar, informar resultados, **concluir** rodada 1
8. Na tela **Entre rodadas**, opcionalmente testar drop ou **reabrir rodada** para correção
9. Iniciar rodada 2, concluir todas as rodadas
10. Finalizar e verificar premiação + classificação
11. Exportar log JSON
12. Reiniciar app e confirmar que torneio persiste no SQLite

Manual do operador: [OPERADOR.md](OPERADOR.md)

## Backup

Copie o arquivo `%APPDATA%\TCGTools\tcg_tools.db` (produção via `.bat`) ou `./data/tcg_tools.db` em desenvolvimento.

Logs JSON exportados ficam em `./logs/` (ou subpasta `logs` dentro de `TCGTOOLS_DATA_DIR` se configurado).

## Porta ocupada

Altere a porta no `.bat` ou encerre o processo que usa a 8000:

```powershell
netstat -ano | findstr :8000
```

Mais problemas: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

## Variáveis de ambiente

| Variável | Descrição |
|----------|-----------|
| `TCGTOOLS_DATA_DIR` | Pasta de dados (SQLite) |
| `TCGTOOLS_DATABASE_URL` | URL SQLAlchemy (opcional) |

## Python embeddable (fallback)

Se `py -3.13` e `uv` não estiverem disponíveis, `scripts\setup.ps1` baixa o Python 3.13 embeddable para `runtime\python\` e instala as dependências. O `.bat` usa essa instalação automaticamente.

## Instalador único (futuro)

Para distribuição sem Git/Node na loja, veja [INSTALADOR.md](INSTALADOR.md).
