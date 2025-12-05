import logging
import os
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler

# ============================================================
#   PASTAS DOS LOGS
# ============================================================

BASE_DIR = "logs"
ERROR_DIR = os.path.join(BASE_DIR, "errors")
SPECIAL_DIR = os.path.join(BASE_DIR, "special")

os.makedirs(BASE_DIR, exist_ok=True)
os.makedirs(ERROR_DIR, exist_ok=True)
os.makedirs(SPECIAL_DIR, exist_ok=True)

# ============================================================
#   FORMATOS
# ============================================================

FILE_FORMAT = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s",
    "%Y-%m-%d %H:%M:%S"
)

ERROR_FORMAT = logging.Formatter(
    "%(asctime)s - [ERROR] - %(message)s\n",
    "%Y-%m-%d %H:%M:%S"
)

CONSOLE_FORMAT = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(message)s",
    "%H:%M:%S"
)

# ============================================================
#   LOGGER PRINCIPAL
# ============================================================

log = logging.getLogger("StreamZoneBot")
log.setLevel(logging.INFO)

# Impedir multiplicação de handlers
if log.handlers:
    log.handlers.clear()

# ============================================================
#   LOG DIÁRIO (FICHEIRO)
# ============================================================

daily_log = TimedRotatingFileHandler(
    os.path.join(BASE_DIR, "bot.log"),
    when="midnight",
    interval=1,
    backupCount=14,
    encoding="utf-8",
    utc=False
)
daily_log.setFormatter(FILE_FORMAT)
daily_log.setLevel(logging.INFO)

log.addHandler(daily_log)

# ============================================================
#   LOG DE ERROS (DIÁRIO)
# ============================================================

error_log = TimedRotatingFileHandler(
    os.path.join(ERROR_DIR, "errors.log"),
    when="midnight",
    interval=1,
    backupCount=30,
    encoding="utf-8"
)
error_log.setFormatter(ERROR_FORMAT)
error_log.setLevel(logging.ERROR)

log.addHandler(error_log)

# ============================================================
#   LOG PARA O TERMINAL
# ============================================================

console = logging.StreamHandler()
console.setFormatter(CONSOLE_FORMAT)
console.setLevel(logging.INFO)

log.addHandler(console)

# ============================================================
#   LOGS ESPECIAIS (GUARDIAN, TRADES, WATCHDOG, TELEGRAM)
# ============================================================

def _special_log(filename, msg):
    """Escreve logs dedicados com timestamp automático."""
    try:
        os.makedirs(SPECIAL_DIR, exist_ok=True)
        path = os.path.join(SPECIAL_DIR, filename)

        with open(path, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {msg}\n")

    except Exception as e:
        log.error(f"[LOGGER SPECIAL ERROR] {e}")


def log_trade(msg):
    _special_log("trades.log", msg)


def log_guardian(msg):
    _special_log("guardian.log", msg)


def log_watchdog(msg):
    _special_log("watchdog.log", msg)


def log_telegram(msg):
    _special_log("telegram.log", msg)


# ============================================================
#   MENSAGEM DE ARRANQUE
# ============================================================

log.info("📄 LOGGER carregado — rotação diária ativa.")
