# StreamZone Bot (MT5) — Guia Completo em Português

Documentação oficial do bot do repositório **14666**, preparada para replicar o comportamento do projeto 14555 e funcionar com todos os sinais, pares e proteções já existentes no código. O foco é Windows + MetaTrader 5, com múltiplas instâncias do terminal e controlo total por Telegram.

## 📌 O que o bot faz
- Lê sinais de um canal do Telegram e abre posições nas contas MT5 configuradas (suporte multi-conta).
- Normaliza símbolos (XAUUSD, GOLD, XAUUSD.p, etc.) e evita duplicação de sinais.
- Aplica **Guardian Shield** (limites de perda/lucro, fecho de emergência) antes de cada execução.
- Monitora **TP1 → Break Even** e fecha posições antes do fecho do mercado, se configurado.
- Mantém os terminais MT5 abertos com o **Watchdog** (reinicia, limpa processos zombie, valida caminhos).
- Deteta ordens manuais abertas/fechadas diretamente no MT5 e notifica.
- Notifica todas as ações importantes no canal de notificações do Telegram.

## 🖥 Requisitos
- **Sistema operativo:** Windows (o `start_bot.bat` automatiza dependências). Em Linux só com Wine + MT5 (não incluído nesta versão).
- **Python:** apenas **3.10.11** é suportado pelas bibliotecas MT5. Evita 3.11/3.12/3.13.
- **MetaTrader 5:** instalado para cada conta, com caminho completo para `terminal64.exe` definido em `config.py`.
- **Pacotes Python:** `MetaTrader5`, `telethon`, `psutil`, `pytz` (já listados em `requirements.txt`).

## 🚀 Instalação rápida (Windows)
1. Instala Python 3.10.11 (https://www.python.org/downloads/release/python-31011/).
2. Clona ou copia o repositório para uma pasta local.
3. Corre `start_bot.bat` (instala dependências e inicia o bot). O script também oferece reinício automático se algo falhar.

### Instalação manual (opcional)
```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main.py
```

## 🔧 Configuração principal (`config.py`)
Editar obrigatoriamente antes de arrancar:
- `BOT_TOKEN`: token do bot Telegram.
- `API_ID` e `API_HASH`: credenciais da API do Telegram.
- `TELEGRAM_CHANNEL`: ID (chat id negativo) do canal onde chegam os sinais.
- `NOTIFY_CHAT`: chat ou canal para enviar notificações (idealmente privado).

### Contas MT5 (multi-instância)
Adiciona um dicionário por conta na lista `ACCOUNTS`:
```python
{
    "name": "ACC1",          # etiqueta apenas para logs
    "login": 123456,          # número de login
    "password": "***",       # senha MT5
    "server": "Broker-Server",
    "lot": 0.01,              # volume padrão por ordem
    "path": r"C:\\Caminho\\Para\\MT5\\terminal64.exe"
}
```

### Guardian Shield
Controla risco e fechos automáticos:
```python
GUARDIAN = {
    "enabled": True,
    "daily_loss_limit": 0.03,        # 3% de perda diária máxima
    "max_loss_limit": 0.06,          # 6% de perda total máxima
    "daily_profit_target": 0.05,     # 5% de lucro diário → bloqueia novas entradas
    "stop_after_N_losses": 3,        # preparado para expansão
    "auto_close_before_market_close": True,  # fecha posições antes do fecho diário
    "block_trading_on_guardian_trigger": True
}
```

### Outras definições
- `MAGIC_NUMBER`: etiqueta MT5 usada em todas as ordens automáticas.
- `RISK_PERCENT`: percentagem de risco usada nos cálculos internos (0.009 = 0.9%).

## 🏗 Arquitetura dos ficheiros
- `main.py`: ponto de entrada. Inicia watchdog, price watcher, guardian, market hours, manual detector e por fim o handler Telegram.
- `telegram_handler.py`: liga ao Telegram, recebe sinais do `TELEGRAM_CHANNEL`, evita duplicados e envia para o executor.
- `signal_parser.py`: normaliza símbolos (XAUUSD/GOLD e sufixos .p/.pi/.r/.m/.i/.var), lê direção (BUY/SELL), ENTRY (valor ou MARKET), TP1–TP3 e SL.
- `trade_executor.py`: login isolado por conta, abre ordens com `MAGIC_NUMBER`, regista o trade para o break-even, respeita bloqueios do Guardian.
- `price_watcher.py`: por conta, vigia se o preço bate **TP1** e move o SL para a entrada (Break Even). Pode fechar posições antes do fecho do mercado.
- `market_hours.py`: monitoriza estado de mercado (aberto/fechado, pré-fecho) e emite notificações.
- `manual_detector.py`: deteta ordens abertas/fechadas manualmente no MT5 e notifica.
- `watchdog_mt5.py`: garante que cada `terminal64.exe` das contas está ativo, reinicia se cair, limpa processos zombie e valida caminhos.
- `telegram_notifier.py`: fila de notificações para evitar spam; usado por todas as threads.
- `logger.py`: logging diário em `logs/`, com ficheiros dedicados para guardian, watchdog, telegram e trades.

## 🧾 Formato de sinais suportado
O parser aceita variações em maiúsculas/minúsculas e remove sufixos de corretora.

Exemplos válidos:
```
BUY XAUUSD
ENTRY: 4234.50
TP1: 4240.00
TP2: 4245.00
SL: 4228.00
```
```
SELL GOLD
ENTRY MARKET
TP1 2315.4
STOP LOSS: 2321.0
```

Campos lidos:
- Direção: `BUY` ou `SELL`.
- Símbolo: `XAUUSD`, `GOLD`, `XAU`, `XAUUSD.p/.pi/.r/.m/.i/.var`.
- Entrada: número ou `ENTRY MARKET` (usa preço atual se não vier valor).
- TP1/TP2/TP3: qualquer combinação; o break-even usa **TP1**.
- SL: obrigatório para envio seguro ao MT5.

## 🔔 Notificações
O bot usa `NOTIFY_CHAT` para enviar mensagens estruturadas:
- Arranque do bot e watchdog.
- Novo sinal recebido e detalhes de entrada.
- Break Even aplicado após TP1.
- Mercado a fechar (e posições fechadas automaticamente, se ativado).
- Quedas ou reinícios do MT5 por conta.
- Bloqueios do Guardian e fechos de emergência.

## 📡 Comandos de Telegram
O código atual é focado em processamento automático de sinais do canal definido. Não há comandos `/status` ou outros handlers de chat implementados neste repositório. Para comandos adicionais, acrescenta um handler no `telegram_handler.py` usando `@client.on(events.NewMessage(pattern="/..."))` e envia respostas com `notify()`.

## ▶️ Como executar
### Método recomendado
```bat
start_bot.bat
```
- Verifica Python 3.10.11.
- Instala dependências (usa `requirements.txt`).
- Inicia `python main.py` com opção de reiniciar se falhar.

### Método manual
```bash
python main.py
```
Corre todas as threads (watchdog, guardian, price watcher, market hours, manual detector e Telegram handler).

## 🧪 Testes rápidos
Depois de configurar, valida:
1. Abrir/fechar manualmente o MT5 → watchdog deve relançar e notificar.
2. Enviar um sinal de teste pelo `TELEGRAM_CHANNEL` → ordens devem abrir em todas as contas ativas.
3. Atualizar preço até bater TP1 → SL deve mover para a entrada e gerar notificação de Break Even.
4. Fechar ordens manualmente → manual detector deve registar e notificar.
5. Simular fecho de mercado (perto das 21:00 UTC) → `auto_close_before_market_close` fecha posições e avisa.

## ❗️ Boas práticas e notas
- Mantém cada conta MT5 com **um caminho exclusivo** para `terminal64.exe` (evita conflitos no watchdog e no login isolado).
- Não mistures instalações de Python; garante que `python` no terminal é a versão 3.10.11.
- Guarda os logs em `logs/` para auditoria (rodagem diária automática).
- Se alterares limites do Guardian, testa com contas demo antes de colocar em produção.

## 🔄 A alinhar com o projeto 14555
A lógica de parsing, proteção de risco e multi-instância foi mantida para aceitar todos os símbolos e comportamentos do projeto 14555. Caso existam sinais adicionais específicos, basta ajustar o `signal_parser.py` seguindo o padrão existente.
