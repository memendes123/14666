# ============================================================
#   NOTIFICADOR TELEGRAM (SÍNCRONO — 100% ESTÁVEL)
# ============================================================

from telethon import TelegramClient
from telethon.errors import RPCError
import threading
import time

from config import API_ID, API_HASH, BOT_TOKEN, NOTIFY_CHAT
from logger import log

# Cliente Telegram (sessão separada)
client = TelegramClient("NotifierSync", API_ID, API_HASH)

telegram_ready = False

# Queue de mensagens (para evitar enviar em paralelo)
_queue = []
_lock = threading.Lock()


# ============================================================
#   INICIAR O NOTIFIER (login do bot)
# ============================================================

def init_notifier():
    global telegram_ready

    try:
        client.start(bot_token=BOT_TOKEN)
        telegram_ready = True
        log.info("[NOTIFIER] Sistema de notificações Telegram PRONTO.")
    except Exception as e:
        log.error(f"[NOTIFIER ERROR] Falha ao iniciar notifier: {e}")
        telegram_ready = False


# ============================================================
#   ENVIO DIRETO (não deve ser usado pelas threads)
# ============================================================

def _send_now(msg):
    """Envia mensagem diretamente ao Telegram (bloco síncrono)."""
    try:
        client.send_message(NOTIFY_CHAT, msg)
    except RPCError as e:
        log.error(f"[NOTIFIER] RPC Error: {e}")
    except Exception as e:
        log.error(f"[NOTIFIER] Erro inesperado: {e}")


# ============================================================
#   notify() — usado pelas threads TODAS (SEGURO)
# ============================================================

def notify(msg):
    """
    Adiciona mensagem à fila de envio.
    Seguro para qualquer thread:
        watchdog_mt5
        guardian
        price_watcher
        executor
        parser
        handler
    """
    if not telegram_ready:
        log.warning("[NOTIFIER] Telegram não está pronto ainda.")
        return

    with _lock:
        _queue.append(msg)


# ============================================================
#   LOOP DESPACHADOR (síncrono)
# ============================================================

def dispatcher_loop():
    """Corre numa thread separada e envia 1 msg de cada vez."""
    while True:

        if telegram_ready:
            with _lock:
                if _queue:
                    msg = _queue.pop(0)
                else:
                    msg = None

            if msg:
                _send_now(msg)

        time.sleep(0.3)  # evita spam


# ============================================================
#   START
# ============================================================

def start_notifier():
    """Inicia login + dispatcher thread."""
    init_notifier()

    t = threading.Thread(target=dispatcher_loop, daemon=True)
    t.start()

    log.info("[NOTIFIER] Dispatcher sincronizado iniciado.")
