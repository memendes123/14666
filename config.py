BOT_TOKEN = "8184769812:AAG9P5oC7_Nu9XDQ6oFfx5eOzd9dP95QVlc"

API_ID = 34300872
API_HASH = "dcbf4a91e6c179f5e9659d296ac061fd"

# Onde o bot lê os sinais:
TELEGRAM_CHANNEL = -1003044918824

# Onde envia notificações:
NOTIFY_CHAT = -1003386889181


# ======================================================
#                     CONTAS MT5
# ======================================================

ACCOUNTS = [
    {
        "name": "ACC1",
        "login": 344670,
        "password": "4)GqcUyThf",
        "server": "BlueGuardian-Server",
        "lot": 0.01,
        "path": r"C:\Users\helde\Desktop\Forex\MetaTrader\MetaTrader_5_1\terminal64.exe"
    },
    {
        "name": "ACC2",
        "login": 344669,
        "password": "xi!6KmOM2x",
        "server": "BlueGuardian-Server",
        "lot": 0.01,
        "path": r"C:\Users\helde\Desktop\Forex\MetaTrader\MetaTrader_5_2\terminal64.exe"
    },
    {
        "name": "ACC3",
        "login": 897705,
        "password": "!y4oXZSFH6",
        "server": "BlueberryMarkets-Demo02",
        "lot": 0.01,
        "path": r"C:\Users\helde\Desktop\Forex\MetaTrader\MetaTrader_5_4_Copy\terminal64.exe"
    },
    {
        "name": "ACC4",
        "login": 344706,
        "password": "Z1Eh2^MH)U",
        "server": "BlueGuardian-Server",
        "lot": 0.01,
        "path": r"C:\Users\helde\Desktop\Forex\MetaTrader\MetaTrader_5_4\terminal64.exe"
    }
]


# ======================================================
#                     DEFINIÇÕES DE TRADING
# ======================================================

MAGIC_NUMBER = 123456

RISK_PERCENT = 0.009   # 0.9% por trade


# ======================================================
#                 GUARDIAN SHIELD PRO
# ======================================================

GUARDIAN = {
    "enabled": True,

    "daily_loss_limit": 0.03,       # 3%
    "max_loss_limit": 0.06,         # 6%
    "daily_profit_target": 0.05,    # 5%

    "stop_after_N_losses": 3,

    "auto_close_before_market_close": True,
    "block_trading_on_guardian_trigger": True
}
