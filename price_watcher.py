import time
import threading
import MetaTrader5 as mt5
from logger import log
from telegram_notifier import notify
from config import ACCOUNTS, MAGIC_NUMBER, GUARDIAN

# ============================================================
#   ESTRUTURA DE TRADES ABERTOS (NOVO FORMATO)
# ============================================================

ACTIVE_TRADES = {}  
# Ex:
# ACTIVE_TRADES[symbol] = [
#     { "login": 344670, "entry": 4198.5, "tp1": 4204.0, "be": False }
# ]


# ============================================================
#   REGISTAR TRADE
# ============================================================

def register_trade(symbol, login, entry_price, tp1):
    if symbol not in ACTIVE_TRADES:
        ACTIVE_TRADES[symbol] = []

    ACTIVE_TRADES[symbol].append({
        "login": login,
        "entry": entry_price,
        "tp1": tp1,
        "be": False
    })

    log.info(f"[TP1-REGISTER] {symbol} / Conta {login} | Entry={entry_price} | TP1={tp1}")


# ============================================================
#   VERIFICAR HORA DO FECHO DE MERCADO
# ============================================================

def market_closing_soon():
    # Fecho Forex: 21:00 UTC
    from datetime import datetime, timezone, timedelta
    now = datetime.now(timezone.utc)
    close = now.replace(hour=21, minute=0, second=0, microsecond=0)
    return (close - now) <= timedelta(minutes=5)


# ============================================================
#   AUTO CLOSE (SEM shutdown)
# ============================================================

def auto_close_positions(acc, symbol):
    if not mt5.initialize(acc["path"]):
        return

    if not mt5.login(acc["login"], acc["password"], acc["server"]):
        return

    positions = mt5.positions_get(symbol=symbol)
    if not positions:
        return

    for pos in positions:

        if pos.magic != MAGIC_NUMBER:
            continue

        close_type = (
            mt5.ORDER_TYPE_SELL if pos.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
        )

        tick = mt5.symbol_info_tick(symbol)
        if not tick:
            continue

        price = tick.bid if close_type == mt5.ORDER_TYPE_SELL else tick.ask

        req = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": pos.volume,
            "type": close_type,
            "price": price,
            "deviation": 50,
            "magic": MAGIC_NUMBER,
            "comment": "AUTO_CLOSE_BEFORE_MARKET_CLOSE"
        }

        result = mt5.order_send(req)

        if result.retcode == mt5.TRADE_RETCODE_DONE:
            notify(
                f"⏳ *Fecho automático — mercado prestes a fechar*\n"
                f"Conta: {acc['login']}\n"
                f"Símbolo: {symbol}"
            )
            log.info(f"[AUTO CLOSE] {symbol} fechado automaticamente conta {acc['login']}")
        else:
            log.error(f"[AUTO CLOSE ERROR] {result}")


# ============================================================
#   CHECK DE TP1 → BE (POR CONTA)
# ============================================================

def check_tp1_for_account(acc):
    login = acc["login"]

    if not mt5.initialize(acc["path"]):
        return

    if not mt5.login(acc["login"], acc["password"], acc["server"]):
        return

    for symbol, trades in ACTIVE_TRADES.items():

        for trade in trades:
            if trade["login"] != login:
                continue
            if trade["be"]:
                continue

            entry = trade["entry"]
            tp1 = trade["tp1"]

            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                continue

            # BUY usa ASK para TP1; SELL usa BID para TP1
            if entry < tp1:
                price = tick.ask
                hit = price >= tp1
            else:
                price = tick.bid
                hit = price <= tp1

            if not hit:
                continue

            # ----- TP1 ACIONADO -----
            log.info(f"[TP1 HIT] {symbol} | Conta {login} | BE ativado.")

            positions = mt5.positions_get(symbol=symbol)
            if not positions:
                continue

            for pos in positions:
                if pos.magic != MAGIC_NUMBER:
                    continue

                req = {
                    "action": mt5.TRADE_ACTION_SLTP,
                    "position": pos.ticket,
                    "sl": entry,
                    "tp": pos.tp
                }

                result = mt5.order_send(req)

                if result.retcode == mt5.TRADE_RETCODE_DONE:
                    notify(
                        f"⚠️ *Break Even ativado*\n"
                        f"Conta: {login}\n"
                        f"Símbolo: {symbol}"
                    )
                    log.info(f"[BE SET] SL movido para entrada ({symbol}) conta {login}")
                else:
                    notify(f"❌ Erro ao aplicar BE ({login}, {symbol})")
                    log.error(f"[BE ERROR] {result}")

            trade["be"] = True


# ============================================================
#   THREAD DE MONITOR POR CONTA
# ============================================================

def _monitor_account(acc):
    login = acc["login"]
    log.info(f"[TP1_WATCH] Monitor a correr para conta {login}")

    while True:

        # 1) AUTO FECHAR AO FECHAR MERCADO
        if GUARDIAN.get("auto_close_before_market_close", True):
            if market_closing_soon():
                for symbol in list(ACTIVE_TRADES.keys()):
                    auto_close_positions(acc, symbol)
                time.sleep(2)
                continue

        # 2) CHECK TP1
        try:
            check_tp1_for_account(acc)
        except Exception as e:
            log.error(f"[TP1_WATCH ERROR] Conta {login}: {e}")

        time.sleep(0.4)


# ============================================================
#   INICIAR WATCHER
# ============================================================

def start_price_watcher():
    log.info("[TP1_WATCH] Price Watcher iniciado.")

    for acc in ACCOUNTS:
        t = threading.Thread(target=_monitor_account, args=(acc,), daemon=True)
        t.start()

    log.info("[TP1_WATCH] Ativo para todas as contas.")
