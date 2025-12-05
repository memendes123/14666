import time
from logger import log

# Módulos principais
from watchdog_mt5 import start_watchdog
from price_watcher import start_price_watcher
from guardian import start_guardian_loop
from manual_detector import start_manual_detector
from market_hours import start_market_hours_loop
from telegram_handler import start_telegram_thread


# ============================================================
#   ARRANQUE PRINCIPAL DO BOT
# ============================================================

def main():

    log.info("==============================================")
    log.info("           Starting BOT...")
    log.info("==============================================")

    # ========================================================
    # 1) Iniciar WATCHDOG (MT5)
    # ========================================================
    start_watchdog()
    log.info("[MAIN] Watchdog iniciado.")
    time.sleep(1)

    # ========================================================
    # 2) Price Watcher (TP1 → Break Even)
    # ========================================================
    start_price_watcher()
    log.info("[MAIN] Price Watcher iniciado.")
    time.sleep(1)

    # ========================================================
    # 3) Guardian Shield PRO
    # ========================================================
    start_guardian_loop()
    log.info("[MAIN] Guardian iniciado.")
    time.sleep(1)

    # ========================================================
    # 4) Market Hours (abre/fecha mercado)
    # ========================================================
    start_market_hours_loop()
    log.info("[MAIN] Market Hours iniciado.")
    time.sleep(1)

    # ========================================================
    # 5) Detector de ordens manuais
    # ========================================================
    start_manual_detector()
    log.info("[MAIN] Manual Detector iniciado.")
    time.sleep(1)

    # ========================================================
    # 6) Telegram Handler (último a iniciar)
    # ========================================================
    log.info("[MAIN] A iniciar Telegram no thread principal...")
    start_telegram_thread()


# ============================================================
#   ARRANQUE DIRETO
# ============================================================

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log.warning("==============================================")
        log.warning(" BOT ENCERRADO MANUALMENTE ")
        log.warning("==============================================")
    except Exception as e:
        print("\n==============================================")
        print("BOT stopped or crashed.")
        print("==============================================")
        print(e)
        log.error(f"[MAIN CRASH] {e}")
