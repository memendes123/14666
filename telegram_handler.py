import asyncio
import threading
import time
from datetime import date, datetime

from telethon import TelegramClient, events

from config import (
    ACCOUNTS,
    API_HASH,
    API_ID,
    BOT_TOKEN,
    GUARDIAN,
    NOTIFY_CHAT,
    RISK_PERCENT,
    TELEGRAM_CHANNEL,
)
from logger import log
from market_hours import is_market_open, minutes_until_close
from price_watcher import ACTIVE_TRADES
from signal_parser import parse_signal
from telegram_notifier import notify
from trade_executor import execute_trade
from watchdog_mt5 import telegram_is_ready


# ============================================================
#   CLIENTE TELEGRAM PRINCIPAL
# ============================================================

client = TelegramClient("StreamZonePRO_MAX", API_ID, API_HASH)

SIGNALS_TODAY = []
LAST_SIGNAL = None
LAST_DATE = date.today()
ALLOWED_COMMAND_CHATS = {NOTIFY_CHAT}


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

    # dispatcher do notifier (síncrono)
    from telegram_notifier import start_notifier
    start_notifier()

    telegram_is_ready()

    notify("🤖 *Bot Telegram iniciado*")


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
#   HANDLERS DE COMANDO (TELEGRAM)
# ============================================================


def _command_chat(event):
    return event.chat_id in ALLOWED_COMMAND_CHATS


def _format_signals_history(limit: int = 10):
    if not SIGNALS_TODAY:
        return "Nenhum sinal recebido hoje."

    lines = []
    start_index = max(0, len(SIGNALS_TODAY) - limit)
    for idx, signal in enumerate(SIGNALS_TODAY[start_index:], start=start_index + 1):
        lines.append(f"{idx}. {signal}")

    if len(SIGNALS_TODAY) > limit:
        lines.append(f"... (total: {len(SIGNALS_TODAY)} sinais)")

    return "\n".join(lines)


@client.on(events.NewMessage(pattern=r"^/start$"))
async def command_start(event):
    if not _command_chat(event):
        return

    await event.respond(
        "🤖 *StreamZone Bot ativo!*\n\n"
        "Comandos disponíveis:\n"
        "/status — resumo rápido do estado\n"
        "/sinais — lista de sinais de hoje\n"
        "/risco — percentagem de risco configurada\n"
        "/contas — contas MT5 carregadas\n"
        "/guardian — estado e limites do Guardian\n"
        "/reset — limpar histórico de sinais do dia"
    )


@client.on(events.NewMessage(pattern=r"^/status$"))
async def command_status(event):
    if not _command_chat(event):
        return

    check_reset_daily()

    open_trades = sum(len(v) for v in ACTIVE_TRADES.values())
    market_state = "Aberto" if is_market_open() else "Fechado"
    minutes_left = minutes_until_close()

    closing_note = ""
    if minutes_left is not None:
        closing_note = f" (fecha em ~{int(minutes_left)} min)"

    await event.respond(
        "📊 *Status geral*\n"
        f"Mercado: {market_state}{closing_note}\n"
        f"Guardian: {'Ativo' if GUARDIAN.get('enabled', True) else 'Desativado'}\n"
        f"Sinais hoje: {len(SIGNALS_TODAY)}\n"
        f"Último sinal: {LAST_SIGNAL or 'nenhum'}\n"
        f"Trades ativos (tracking): {open_trades}"
    )


@client.on(events.NewMessage(pattern=r"^/sinais$"))
async def command_sinais(event):
    if not _command_chat(event):
        return

    check_reset_daily()
    await event.respond("📝 *Sinais do dia*\n" + _format_signals_history())


@client.on(events.NewMessage(pattern=r"^/risco$"))
async def command_risco(event):
    if not _command_chat(event):
        return

    await event.respond(f"⚖️ *Risco por trade:* {RISK_PERCENT * 100:.2f}%")


@client.on(events.NewMessage(pattern=r"^/contas$"))
async def command_contas(event):
    if not _command_chat(event):
        return

    lines = [
        f"{acc['name']} — login {acc['login']} ({acc['server']})"
        for acc in ACCOUNTS
    ]
    await event.respond("💼 *Contas MT5 carregadas*\n" + "\n".join(lines))


@client.on(events.NewMessage(pattern=r"^/guardian$"))
async def command_guardian(event):
    if not _command_chat(event):
        return

    g = GUARDIAN
    await event.respond(
        "🛡 *Guardian Shield*\n"
        f"Ativo: {'Sim' if g.get('enabled', True) else 'Não'}\n"
        f"Perda diária: {g.get('daily_loss_limit', 0)*100:.1f}%\n"
        f"Perda total: {g.get('max_loss_limit', 0)*100:.1f}%\n"
        f"Meta diária: {g.get('daily_profit_target', 0)*100:.1f}%\n"
        f"Auto close antes fecho: {'Sim' if g.get('auto_close_before_market_close', True) else 'Não'}"
    )


@client.on(events.NewMessage(pattern=r"^/reset$"))
async def command_reset(event):
    global SIGNALS_TODAY, LAST_SIGNAL, LAST_DATE

    if not _command_chat(event):
        return

    SIGNALS_TODAY = []
    LAST_SIGNAL = None
    LAST_DATE = date.today()

    await event.respond("🔄 Histórico de sinais do dia foi limpo.")


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
