import time
from datetime import datetime, timedelta, timezone

from logger import log
from telegram_notifier import notify

# FLAGS
sent_close_msg = False
sent_open_msg = False
sent_closing_soon = False


# ============================================================
# HORÁRIOS DO MERCADO (FOREX)
# ============================================================

"""
Mercado Forex:
    • Abre domingo 22:00 UTC
    • Fecha sexta 21:00 UTC
    • De segunda a quinta está sempre aberto
"""

def is_market_open():
    now = datetime.now(timezone.utc)
    wd = now.weekday()
    hour = now.hour

    # Sábado → fechado
    if wd == 5:
        return False

    # Domingo → fechado até 22h
    if wd == 6 and hour < 22:
        return False

    # Sexta → fecha às 21:00 UTC
    if wd == 4 and hour >= 21:
        return False

    return True


def minutes_until_close():
    """Minutos até o fecho REAL do mercado."""
    now = datetime.now(timezone.utc)
    wd = now.weekday()

    # Segunda a quinta: não fecha
    if wd in (0, 1, 2, 3):
        return None

    # Sexta → fecha às 21:00 UTC
    if wd == 4:
        close_dt = now.replace(hour=21, minute=0, second=0, microsecond=0)
        return (close_dt - now).total_seconds() / 60

    return None


# ============================================================
# LOOP PRINCIPAL
# ============================================================

def market_hours_loop():
    global sent_close_msg, sent_open_msg, sent_closing_soon

    log.info("[MARKET HOURS] Sistema iniciado.")

    while True:
        now_open = is_market_open()
        minutes_left = minutes_until_close()

        # ====================================================
        # MERCADO FECHADO
        # ====================================================
        if not now_open:
            if not sent_close_msg:
                notify("🔴 *Mercado Fechado*\nSinais e execuções pausadas.")
                log.info("[MARKET HOURS] Mercado FECHADO.")
                sent_close_msg = True
                sent_open_msg = False
                sent_closing_soon = False

            time.sleep(30)
            continue

        # ====================================================
        # MERCADO ABERTO
        # ====================================================
        if now_open and not sent_open_msg:
            notify("🟢 *Mercado Aberto*\nSistema reativado.")
            log.info("[MARKET HOURS] Mercado ABERTO.")
            sent_open_msg = True
            sent_close_msg = False
            sent_closing_soon = False

        # ====================================================
        # FECHO EM <5 MIN
        # ====================================================
        if minutes_left is not None and minutes_left <= 5:
            if not sent_closing_soon:
                notify("⏳ *Mercado fecha em menos de 5 minutos!*")
                log.warning("[MARKET HOURS] Fecho em <5min.")
                sent_closing_soon = True

        time.sleep(10)


# ============================================================
# THREAD LAUNCHER
# ============================================================

def start_market_hours_loop():
    import threading
    t = threading.Thread(target=market_hours_loop, daemon=True)
    t.start()
    log.info("[MARKET HOURS] Thread iniciada.")
