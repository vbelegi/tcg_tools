# Troubleshooting — TCG Tools

## Aplicação não inicia

### Porta 8000 ocupada

```powershell
netstat -ano | findstr :8000
taskkill /PID <pid> /F
```

Ou altere a porta no `scripts\Iniciar TCG Tools.bat`.

### Python errado (3.14 vs 3.13)

O projeto requer **Python 3.13**. Se `py` aponta para 3.14:

```powershell
py -3.13 -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Use sempre `scripts\Iniciar TCG Tools.bat`, que tenta 3.13 primeiro.

### Lock de instância (`.bat`)

Se o app “não abre” mas a porta está livre, remova o lock:

```
%TEMP%\tcg_tools.lock
```

Feche qualquer janela do TCG Tools antes de reiniciar.

## Banco de dados

### Onde fica o SQLite

| Modo | Caminho |
|------|---------|
| Loja (`.bat`) | `%APPDATA%\TCGTools\tcg_tools.db` |
| Desenvolvimento | `./data/tcg_tools.db` |

### Backup

Copie o arquivo `.db` com o app **fechado**. Restaure substituindo o arquivo.

### Migração falhou na inicialização

1. Faça backup do `.db`.
2. Veja o log no terminal ao iniciar (erro Alembic).
3. Se o DB for muito antigo (pré-Alembic), o startup tenta carimbar `001` e aplicar migrações.
4. Em último caso: exporte logs JSON dos torneios finalizados, renomeie o `.db` corrompido e deixe o app criar um novo.

### Coluna `scores_submitted` ausente

Reinicie o app — `init_db` adiciona a coluna em DBs legados. Se persistir, backup + delete do `.db` (perde dados locais).

## Torneios

### “Informe todos os resultados antes de concluir”

Alguma mesa está sem placar válido. Abra a rodada e preencha todas (bye já vem preenchido).

### “Rodada não está ativa”

Tentou editar placar com rodada já concluída. Use **Reabrir rodada** (ver [OPERADOR.md](OPERADOR.md)).

### “Não há próxima rodada a iniciar”

Suíço: todas as rodadas configuradas foram concluídas — use **Finalizar**.  
Eliminatória: resta um campeão — **Finalizar**.

### “Resultado de WO não pode ser alterado”

Drop mid-round gera WO irreversível. Se errou, reabra a rodada **antes** de qualquer drop incorreto (se ainda possível).

### Reabrir rodada removeu a rodada seguinte

Comportamento esperado: ao corrigir R1 com R2 já criada, R2 é apagada e será pareada de novo ao **Iniciar próxima rodada**.

### Eliminatória — bronze não apareceu

A disputa 3º–4º só é criada se **Disputa de 3º–4º** estiver marcada no rascunho **e** houver dois perdedores ativos na semifinal. Se ambos desistiram, só a final é jogada.

### Eliminatória — aviso “Bo por fase … ignorado”

`se_bo_config` tinha fases além do `max_rounds` do bracket (ex.: oitavas com 8 jogadores). Ajuste as fases ou o número de jogadores; fases inválidas são podadas ao iniciar.

### Eliminatória — jogadores não potência de 2 (6, 12…)

BYEs na 1ª rodada preenchem o bracket. Use seeds opcionais para priorizar quem recebe bye. Se o torneio não avança, verifique se todos os placares foram salvos.

### Não consigo finalizar (SE)

Todas as rodadas devem estar **concluídas** com placares válidos. Partida de bronze sem oponente (WO/drop) é ignorada na validação.

## Premiação

### Presets alterados / conflito ao salvar

Recarregue a página. O header `X-Presets-Mtime` evita sobrescrever edições de outra aba.

### CSV desatualizado

Banner na aba Presets — regenere o export após editar presets.

## Frontend

### Página em branco em produção

```powershell
cd frontend
npm run build
```

Reinicie o backend. O FastAPI serve `frontend/dist`.

### Tipos TypeScript desatualizados

```powershell
cd frontend
npm run generate:api
```

## Logs e exports

| Tipo | Pasta | Doc |
|------|-------|-----|
| CSV premiação | `exports/` | — |
| JSON torneios | `logs/` | [export_log.md](export_log.md) |

Export JSON **v2** inclui campos SE (`third_place_match`, `best_of` por partida, etc.).

## Instalador e launcher

### SmartScreen bloqueia o setup.exe

Instalador não assinado na v1. Clique **Mais informações → Executar mesmo assim**.

### Ícone da bandeja não aparece (RDP / política de grupo)

Verifique `%APPDATA%\TCGTools\launcher.log`. O servidor pode estar rodando — abra manualmente a URL em `launcher_config.json`.

### Porta alterada não surte efeito

Edite `%APPDATA%\TCGTools\launcher_config.json`, **Encerrar** pelo menu da bandeja e abra o atalho novamente.

### Backup antes de desinstalar

Desinstalar remove `%APPDATA%\TCGTools\` inteiro. Copie `tcg_tools.db` antes.

## Suporte técnico

1. Anote a mensagem de erro exata.
2. Verifique versão: `README.md` / `CHANGELOG.md`.
3. Rode testes: `cd backend && py -3.13 -m pytest tests/ -v`.
4. Abra issue com passos para reproduzir.
