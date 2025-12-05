import time
import MetaTrader5 as mt5
from config import ACCOUNTS, MAGIC_NUMBER
from telegram_notifier import notify
from logger import log

# Memória de posições detectadas
KNOWN_POSITIONS = {}
LAST_ALERT = {}


# ============================================================
# SESSÃO MT5 ISOLADA (SEM DAR SHUTDOWN GLOBAL)
# ============================================================

def isolated_init(acc):
    mt5.initialize(acc["path"])
    if not mt5.login(acc["login"], acc["password"], acc["server"]):
        return False
    return True


# ============================================================
# SCAN DA CONTA (ISOLADO)
# ============================================================

def scan_account(acc):
    """Deteta ordens manuais novas e fechadas."""
    login = acc["login"]

    if not isolated_init(acc):
        return

    positions = mt5.positions_get()
    mt5.shutdown()

    if positions is None:
        return

    # Criar memória
    if login not in KNOWN_POSITIONS:
        KNOWN_POSITIONS[login] = {}

    current = {}

    for pos in positions:
        current[pos.ticket] = True

        # Nova posição → verificar se é manual
        if pos.ticket not in KNOWN_POSITIONS[login]:
            is_bot = (pos.magic == MAGIC_NUMBER)
            direction = "BUY" if pos.type == mt5.ORDER_TYPE_BUY else "SELL"

            if not is_bot:
                # Anti spam
                if LAST_ALERT.get(pos.ticket) != "open":
                    notify(
                        f"🟣 *Ordem manual detetada*\n"
                        f"Conta: {login}\n"
                        f"Símbolo: {pos.symbol}\n"
                        f"Direção: {direction}\n"
                        f"Volume: {pos.volume}\n"
                        f"Preço: {pos.price_open}"
                    )
                    LAST_ALERT[pos.ticket] = "open"

        KNOWN_POSITIONS[login][pos.ticket] = True

    # Verificar se alguma foi fechada
    for ticket in list(KNOWN_POSITIONS[login].keys()):
        if ticket not in current:
            if LAST_ALERT.get(ticket) != "close":
                notify(
                    f"🔵 *Ordem manual fechada*\n"
                    f"Conta: {login}\n"
                    f"Ticket: {ticket}"
                )
                LAST_ALERT[ticket] = "close"

            del KNOWN_POSITIONS[login][ticket]


# ============================================================
# LOOP PRINCIPAL DO DETECTOR
# ============================================================

def manual_monitor_loop():
    log.info("[MANUAL] Detector de ordens manuais iniciado.")

    while True:
        for acc in ACCOUNTS:
            try:
                scan_account(acc)
            except Exception as e:
                log.error(f"[MANUAL ERROR] {e}")

        time.sleep(1.5)


# ============================================================
# THREAD LAUNCHER
# ============================================================

def start_manual_detector():
    import threading
    t = threading.Thread(target=manual_monitor_loop, daemon=True)
    t.start()
    log.info("[MANUAL] Thread iniciada.")
