from telethon import TelegramClient, events
import threading
import asyncio
import time
from datetime import datetime, date

from config import API_ID, API_HASH, BOT_TOKEN, TELEGRAM_CHANNEL
from trade_executor import execute_trade
from signal_parser import parse_signal
from telegram_notifier import notify
from logger import log


# ============================================================
#   CLIENTE TELEGRAM PRINCIPAL
# ============================================================

client = TelegramClient("StreamZonePRO_MAX", API_ID, API_HASH)

SIGNALS_TODAY = []
LAST_SIGNAL = None
LAST_DATE = date.today()


# ============================================================
#   RESET DIÁRIO
# ============================================================

def check_reset_daily():
    global SIGNALS_TODAY, LAST_DATE
    if date.today() != LAST_DATE:
        SIGNALS_TODAY = []
        LAST_DATE = date.today()
        log.info("[TELEGRAM] Reset diário aplicado.")
        notify("🕛 *Novo dia — lista de sinais limpa.*")


# ============================================================
#   ARRANQUE DO BOT TELEGRAM
# ============================================================

async def start_bot():

    await client.start(bot_token=BOT_TOKEN)
    log.info("[BOOT] Telegram iniciado com sucesso.")
    notify("🤖 *Bot Telegram iniciado*")

    # dispatcher do notifier (síncrono)
    from telegram_notifier import start_notifier
    start_notifier()


# ============================================================
#   HANDLER PRINCIPAL (RECEBE SINAIS)
# ============================================================

@client.on(events.NewMessage(chats=TELEGRAM_CHANNEL))
async def handler(event):
    global LAST_SIGNAL

    msg = event.raw_text.strip()
    if not msg:
        return

    check_reset_daily()

    # Evitar duplicados
    if msg == LAST_SIGNAL:
        log.warning("[HANDLER] Sinal duplicado ignorado.")
        return

    LAST_SIGNAL = msg
    SIGNALS_TODAY.append(msg)

    log.info(f"[SIGNAL RECEIVED] {msg}")
    notify(f"📩 *Novo sinal recebido:*\n\n{msg}")

    # ====================================================
    # PARSE DO SINAL
    # ====================================================
    signal = parse_signal(msg)
    if not signal:
        log.warning("[HANDLER] Parser devolveu None → ignorado.")
        return

    log.info(f"[DEBUG] Tipo de sinal = {signal['type']}")

    # Apenas ENTRY por agora
    if signal["type"] == "ENTRY":

        notify(
            f"🚀 *Entrada Detetada*\n"
            f"Símbolo: {signal['symbol']}\n"
            f"Direção: {signal['direction']}\n"
            f"Entrada: {signal['entry']}\n"
            f"TP1: {signal['tp1']}"
        )

        execute_trade(signal)


# ============================================================
#   LOOP THREAD PARA TELEGRAM
# ============================================================

def start_telegram_thread():
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        loop.run_until_complete(start_bot())
        loop.run_forever()

    except Exception as e:
        log.error(f"[TELEGRAM BOT ERROR] {e}")
        notify(f"❌ ERRO no BOT TELEGRAM:\n{e}")
        time.sleep(2)
