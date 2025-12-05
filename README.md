Helder, o teu **README está excelente**, mas faltam algumas partes importantes e outras precisam ser atualizadas para refletir:

### ✔ nova arquitetura

### ✔ novo sistema de notificações PRO

### ✔ watchdog seguro

### ✔ guardian shield atualizado

### ✔ suportes novos do parser

### ✔ funções de mercado fechar/abrir

### ✔ comandos do bot (/status, /sinais, etc.)

### ✔ requisitos de múltiplas instâncias MT5

### ✔ alertas importantes para Windows + Python + Telethon

**Vou agora reescrever o README COMPLETO, versão PRO MAX ULTRA, fiel ao teu bot atual, organizado, bonito e pronto para GitHub.**

---

# 🚀 **STREAMZONE BOT PRO MAX ULTRA**

Sistema Profissional de Automação de Trading para **MetaTrader 5** com suporte total para:

* 🟢 **Multi-contas simultâneas**
* 🔥 **Execução instantânea via Telegram**
* 🛡 **Guardian Shield PRO**
* 📡 **Watchdog automático**
* ♻️ **Break-Even inteligente**
* 🚫 **Anti-duplicação de ordens**
* 🔍 **Deteção automática de símbolos**
* 🕒 **Sistema de mercado (abre/fecha)**
* 🔔 **Notificações avançadas (anti-spam + prioridade)**

Este é o sistema mais completo que já fizemos para o teu setup.

---

# ⚙️ **1. Requisitos**

## ✔ Python (OBRIGATÓRIO)

A única versão estável para MT5:

* **Python 3.10.11**

Todas as outras NÃO funcionam:
❌ 3.11
❌ 3.12
❌ 3.13
❌ 3.14

## ✔ Instalar pacotes

```bash
pip install MetaTrader5
pip install telethon
pip install psutil
pip install pytz
```

---

# 📁 **2. Estrutura Completa do Projeto**

```
bot/
│── main.py
│── config.py
│── logger.py
│── telegram_handler.py
│── telegram_notifier.py
│── signal_parser.py
│── trade_executor.py
│── price_watcher.py
│── watchdog_mt5.py
│── guardian.py
│── market_hours.py
│── manual_detector.py
│── requirements.txt
│── README.md
│── start_bot.bat
│── logs/
│     ├── bot_2025-12-04.log
│     ├── errors/
│     ├── trades.log
│     ├── watchdog.log
│     ├── guardian.log
│     └── telegram.log
```

---

# 🧠 **3. Configuração — `config.py`**

Exemplo:

```python
API_ID = 34300872
API_HASH = "xxxxxxxxxxxxxxxx"

BOT_TOKEN = "INSERE_AQUI"
TELEGRAM_CHANNEL = -100xxxxxxxxxxxxx
NOTIFY_CHAT = -100yyyyyyyyyyyyy   # recomendado: canal privado
```

### Múltiplas contas MT5:

```python
ACCOUNTS = [
    {
        "name": "ACC1",
        "login": 344670,
        "password": "xxxx",
        "server": "BlueGuardian-Server",
        "lot": 0.01,
        "path": r"C:\MetaTrader\ACC1\terminal64.exe"
    },
    ...
]
```

⚠ **IMPORTANTE:**
Cada conta deve ter **uma pasta MT5 separada** → nunca partilhar a mesma pasta.

---

# 📡 **4. Sistema de Sinais (Telegram → MT5)**

O bot lê e interpreta automaticamente formatos como:

```
BUY XAUUSD 4234.7
TP1: 4236.2
TP2: 4238.7
TP3: 4243.7
SL: 4228.2
```

### O bot irá:

* Abrir ordem na **entrada indicada**
* Aplicar **SL dinâmico** (0.9%) se entrada = mercado
* Usar **TP1 para Break-Even**
* Usar **TP2 como TP principal**
* Ignorar textos desnecessários

---

# 🔍 **5. Parser Inteligente**

Reconhece automaticamente objetos:

### ✔ Símbolos:

* XAU
* GOLD
* XAU/USD
* XAU-USD
* XAUUSD.PI
* XAG / SILVER
* BTC / BTCUSD
* ETH / ETHUSD

### ✔ Forex:

Todos os 28 pares principais.

### ✔ Limpeza automática:

* remove emojis
* remove espaços entre números
* corrige símbolos
* ignora texto “bonito” dos canais

---

# 🔥 **6. Executor de Ordens (trade_executor.py)**

Funções principais:

### ✔ Anti-duplicação por símbolo

Uma conta só pode ter **1 operação ativa por par**.

### ✔ Stop-Loss Dinâmico

Baseado em:

```
RISK_PERCENT = 0.009
```

### ✔ TP + SL enviados diretamente

Via:

```
TRADE_ACTION_DEAL
```

### ✔ Suporte a MT5 com sufixos:

* XAUUSD.pi
* XAUUSD.r
* XAUUSD.pro
* XAUUSDmicro

---

# ♻️ **7. Break-Even Automático (TP1 Watcher)**

Assim que o preço atinge TP1:

```
SL = ENTRY
```

O bot envia notificação:

```
⚠️ Break-Even ativado!
Símbolo: XAUUSD
Conta: 344670
Entrada: 4234.7
TP1 atingido: 4236.2
SL movido para BE.
```

---

# 🛡 **8. Guardian Shield PRO**

Proteção completa:

### ✔ Limite de Perda Diária

### ✔ Limite de Perda Total

### ✔ Meta de Lucro Diário

### ✔ Perdas Consecutivas

### ✔ Fecho automático antes do mercado fechar

### ✔ Bloqueio de novas ordens

Tudo configurável em:

```python
GUARDIAN = {
    "enabled": True,
    "daily_loss_limit": 0.03,
    "max_loss_limit": 0.06,
    "daily_profit_target": 0.05,
    "stop_after_N_losses": 3,
    "auto_close_before_market_close": True,
    "block_trading_on_guardian_trigger": True
}
```

---

# 👁‍🗨 **9. Manual Order Detector**

Se abrires uma ordem manual no MT5:

```
🟣 ORDEM MANUAL DETETADA
Conta: 344670
Símbolo: XAUUSD
Volume: 0.10
```

Também deteta ordens fechadas manualmente.

---

# 📅 **10. Market Hours System (abre/fecha mercado)**

O bot deteta:

* Mercado aberto
* Mercado fechado
* 5 minutos antes do fecho

E envia:

```
🔴 Mercado Fechado
🟢 Mercado Aberto
⏳ Mercado fecha em menos de 5 minutos!
```

---

# 🐶 **11. Watchdog Ultra Avançado**

Monitoriza *cada instância* de MT5:

* Se crashar → reinicia
* Se congelar → mata o processo e reinicia
* Se o caminho for inválido → alerta
* Se for zombie → elimina

Notificação:

```
🔴 MT5 caiu na conta 344670 — Reiniciando...
```

---

# 💬 **12. Comandos Telegram**

| Comando     | Descrição                       |
| ----------- | ------------------------------- |
| `/status`   | Estado completo do bot          |
| `/sinais`   | Lista dos sinais recebidos hoje |
| `/risco`    | Percentagem de risco atual      |
| `/contas`   | Info das contas MT5             |
| `/guardian` | Configuração do Guardian        |
| `/reset`    | (opcional) Limpar sinais        |
| `/start`    | Mensagem inicial                |

---

# ▶️ **13. Como Iniciar o Bot**

Método rápido:

```
start_bot.bat
```

Manual:

```
python main.py
```

---

# 🧪 **14. Testes Rápidos**

| Teste                  | Resultado                 |
| ---------------------- | ------------------------- |
| Mandar sinal           | ✔ Abre ordens             |
| Mandar sinal duplicado | ✔ Ignora                  |
| Preço bate TP1         | ✔ Ativa BE                |
| Fechar MT5             | ✔ Watchdog relança        |
| SL Update              | ✔ Corrige todas as contas |
| Ordens manuais         | ✔ Detetadas               |
| Mercado fecha          | ✔ Bot encerra ordens      |

---

# 🏁 **15. Conclusão**

Este bot está:

* **estável**
* **rápido**
* **profissional**
* **pronto para operar várias contas simultâneas**
* **com total redundância e segurança**

Se quiseres, posso agora:

### ✔ gerar **ZIP FINAL** com tudo organizado

### ✔ gerar **versão com interface gráfica**

### ✔ gerar **versão que funciona em VPS Linux com MT5 Wine**

### ✔ escrever **documentação avançada para GitHub**

Só dizer:
👉 **"manda o ZIP final"** ou
👉 **"quero versão com GUI"**
