import time

import MetaTrader5 as mt5

from config import ACCOUNTS, MAGIC_NUMBER
from guardian import guardian_check
from logger import log
from price_watcher import register_trade


# ============================================================
#   RESOLVER SÍMBOLO (REMOVE .PI, .P, .R, ETC)
# ============================================================

def resolve_symbol(symbol: str):
    symbol = symbol.upper()
    for suf in [".P", ".PI", ".R", ".RP", ".VAR", ".I", ".M"]:
        if symbol.endswith(suf):
            symbol = symbol.replace(suf, "")
    return symbol


# ============================================================
#   LOGIN ISOLADO (SEGURO)
# ============================================================

def isolated_login(acc):
    """Inicia sessão MT5 sem interferir com outras contas."""
    mt5.shutdown()

    if not mt5.initialize(acc["path"]):
        return False

    if not mt5.login(acc["login"], acc["password"], acc["server"]):
        mt5.shutdown()
        return False

    return True


# ============================================================
#   EXECUÇÃO POR CONTA (INTERNO)
# ============================================================

def _execute_for_account(acc, signal):

    login = acc["login"]
    direction = signal["direction"]
    symbol = resolve_symbol(signal["symbol"])
    entry = signal["entry"]
    sl = signal["sl"]
    tp1 = signal["tp1"]

    # 1) Guardian
    if not guardian_check(login):
        log.warning(f"[{login}] Guardian bloqueou ordem para {symbol}.")
        return

    # 2) Isolated login
    if not isolated_login(acc):
        log.error(f"[{login}] Falha login isolado MT5.")
        return

    # 3) Se ENTRY é market ou None → usar preço atual
    tick = mt5.symbol_info_tick(symbol)
    if not tick:
        log.error(f"[{login}] Tick não encontrado para {symbol}.")
        mt5.shutdown()
        return

    if entry is None or entry == "market":
        entry = tick.ask if direction == "BUY" else tick.bid

    # 4) Tipo de ordem
    order_type = mt5.ORDER_TYPE_BUY if direction == "BUY" else mt5.ORDER_TYPE_SELL
    price = tick.ask if direction == "BUY" else tick.bid

    # 5) Preparar requisição
    req = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": acc["lot"],
        "type": order_type,
        "price": price,
        "sl": sl,
        "tp": tp1,
        "magic": MAGIC_NUMBER,
        "comment": "StreamZoneBot",
        "deviation": 30,
    }

    # 6) Enviar ordem
    result = mt5.order_send(req)

    if result.retcode == mt5.TRADE_RETCODE_DONE:
        log.info(f"[{login}] ✔ ORDEM ABERTA {direction} {symbol} @ {price}")

        # Registrar trade para BE
        register_trade(symbol, login, entry, tp1)

    else:
        log.error(f"[{login}] ❌ ERRO AO ABRIR ORDEM → {result.retcode} | {result.comment}")

    mt5.shutdown()


# ============================================================
#   EXECUÇÃO GLOBAL (TODAS AS CONTAS)
# ============================================================

def execute_trade(signal):

    symbol = resolve_symbol(signal["symbol"])
    log.info("===========================================")
    log.info(f"[EXECUTOR] Iniciar execução para {symbol}")
    log.info("===========================================")

    for acc in ACCOUNTS:
        _execute_for_account(acc, signal)
        time.sleep(0.2)  # Evitar overload MT5

    log.info("[EXECUTOR] Execução finalizada.")
