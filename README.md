# Premiação TCG

Calculadora de premiação para torneios locais de TCG. Distribui **100% das inscrições** entre os melhores colocados usando um modelo exponencial escalável.

## Execução

```bash
python main.py
```

## Configuração

Todas as regras do torneio ficam em `config/settings.json`. Esse arquivo é a **fonte da verdade** durante a execução.

- Se não existir, é criado automaticamente a partir dos valores padrão definidos em `core/config.py`.
- Se estiver corrompido ou inválido, é removido, recriado e o console informa o ocorrido.
- Alterações pelo menu (opção 3) só reescrevem o arquivo quando houver mudança real.

Consulte `docs/configuracao.md` para detalhes de cada parâmetro.

## Funcionalidades

1. **Calcular um torneio** — informa jogadores e, opcionalmente, valor da inscrição. Prêmios podem ser exibidos em Créditos na Loja (centavos permitidos).
2. **Gerar tabela** — simula premiações de `min_jogadores` até N e exporta CSV em `exports/`. Arquivo com o mesmo nome é substituído.
3. **Configurações** — edita parâmetros persistidos em `settings.json`. Ao salvar alterações, pergunta se deseja limpar exports antigos. Inclui opção `limpar_exports` para remoção manual.

## Documentação

- `docs/modelo_premiacao.md` — fórmulas e lógica matemática
- `docs/configuracao.md` — parâmetros de `settings.json`

## Estrutura

```
premiacao-tcg/
├── main.py              # CLI
├── core/
│   ├── calculator.py    # Cálculo de premiados e prêmios
│   ├── config.py        # Leitura/gravação de settings.json
│   ├── paths.py         # Caminhos ancorados na raiz do projeto
│   └── validation.py    # Guardrails de config e entrada
├── helpers/
│   ├── display.py       # Saída formatada
│   ├── export.py        # Exportação CSV
│   └── io.py            # Entrada do usuário
├── config/settings.json
├── exports/
└── tests/
```

## Testes

```bash
python -m unittest discover -s tests -v
```
