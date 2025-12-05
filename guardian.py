import time
import MetaTrader5 as mt5
from datetime import datetime
from config import GUARDIAN, ACCOUNTS
from logger import log
from telegram_notifier import notify


# ============================================================
#   ESTADO INTERNO DO GUARDIAN
# ============================================================

guardian_state = {}


# ============================================================
#   LOGIN ISOLADO — EVITA CONFLITOS COM OUTRAS THREADS
# ============================================================

def _isolated_login(acc_details):
    """
    Inicia uma sessão MT5 completamente isolada.
    Evita interferir com executor, watchdog, etc.
    """
    mt5.shutdown()

    if not mt5.initialize(acc_details["path"]):
        return False, None

    if not mt5.login(acc_details["login"], acc_details["password"], acc_details["server"]):
        mt5.shutdown()
        return False, None

    acc_info = mt5.account_info()
    if not acc_info:
        mt5.shutdown()
        return False, None

    return True, acc_info


# ============================================================
#   INICIALIZAR ESTADO DE UMA CONTA
# ============================================================

def init_account(login):

    if login in guardian_state:
        return True  # já existe

    acc = next((a for a in ACCOUNTS if a["login"] == login), None)
    if not acc:
        log.error(f"[GUARDIAN INIT] Conta {login} não encontrada no config!")
        return False

    # 5 tentativas porque o MT5 pode ainda estar a abrir
    for attempt in range(5):
        success, acc_info = _isolated_login(acc)
        if success:
            eq = float(acc_info.equity)

            guardian_state[login] = {
                "start_equity": eq,
                "daily_start": eq,
                "max_equity": eq,
                "min_equity": eq,
                "loss_streak": 0,
                "blocked": False,
                "blocked_reason": ""
            }

            log.info(f"[GUARDIAN INIT] Conta {login} iniciada | Equity={eq}")
            mt5.shutdown()
            return True

        time.sleep(1)

    log.error(f"[GUARDIAN INIT] Falha ao logar conta {login} após várias tentativas.")
    return False


# ============================================================
#   BLOQUEIO
# ============================================================

def _block(login, reason):

    # garante inicialização
    if login not in guardian_state:
        if not init_account(login):
            return

    guardian_state[login]["blocked"] = True
    guardian_state[login]["blocked_reason"] = reason

    notify(
        f"🛑 *GUARDIAN SHIELD — BLOQUEIO*\n"
        f"Conta: {login}\nMotivo: {reason}"
    )

    log.warning(f"[GUARDIAN BLOCK] {login} → {reason}")


# ============================================================
#   DESBLOQUEAR
# ============================================================

def unblock(login):
    if login not in guardian_state:
        return

    guardian_state[login]["blocked"] = False
    guardian_state[login]["blocked_reason"] = ""

    notify(f"🟢 Guardian: Conta {login} desbloqueada.")
    log.info(f"[GUARDIAN] Conta {login} desbloqueada.")


# ============================================================
#   CHECK DE SEGURANÇA
# ============================================================

def guardian_check(login):

    # garantir que estado existe
    if login not in guardian_state:
        if not init_account(login):
            return True  # não bloqueia, apenas ignora até MT5 ficar OK

    st = guardian_state.get(login)
    if not st:
        return True

    # conta bloqueada → não deixa abrir ordens
    if st["blocked"]:
        return False

    acc = next((a for a in ACCOUNTS if a["login"] == login), None)
    if not acc:
        return True

    success, acc_info = _isolated_login(acc)
    if not success:
        log.warning(f"[GUARDIAN] Falha login isolado p/ checar conta {login}.")
        return True

    eq = float(acc_info.equity)
    mt5.shutdown()

    st["max_equity"] = max(st["max_equity"], eq)
    st["min_equity"] = min(st["min_equity"], eq)

    # --------------------------------------
    #   REGRA 1 — Perda diária
    # --------------------------------------
    daily_limit = st["daily_start"] * GUARDIAN["daily_loss_limit"]

    if eq <= st["daily_start"] - daily_limit:
        _block(login, f"Perda diária > {GUARDIAN['daily_loss_limit']*100}%")
        return False

    # --------------------------------------
    #   REGRA 2 — Perda total
    # --------------------------------------
    max_total = st["start_equity"] * GUARDIAN["max_loss_limit"]

    if eq <= st["start_equity"] - max_total:
        _block(login, f"Perda total > {GUARDIAN['max_loss_limit']*100}%")
        return False

    # --------------------------------------
    #   REGRA 3 — Meta diária atingida
    # --------------------------------------
    target = st["daily_start"] * GUARDIAN["daily_profit_target"]

    if eq >= st["daily_start"] + target:
        _block(login, f"Meta diária atingida ({GUARDIAN['daily_profit_target']*100}%)")
        return False

    return True


# ============================================================
#   LOOP PRINCIPAL
# ============================================================

def guardian_loop():

    log.info("[GUARDIAN] Guardian Shield PRO ativo.")

    while True:

        if not GUARDIAN["enabled"]:
            time.sleep(2)
            continue

        for acc in ACCOUNTS:
            login = acc["login"]

            # garantir inicialização SEM CRASHAR
            if login not in guardian_state:
                init_account(login)
                continue

            # se bloqueada, não executa mais nada
            if guardian_state[login]["blocked"]:
                continue

            # se violou regra → emergência
            if not guardian_check(login):
                emergency_close(login)

        time.sleep(2)


# ============================================================
#   FECHO DE EMERGÊNCIA
# ============================================================

def emergency_close(login):

    acc = next((a for a in ACCOUNTS if a["login"] == login), None)
    if not acc:
        return

    success, _ = _isolated_login(acc)
    if not success:
        notify(f"🚨 Guardian ALERTA: Falha ao logar em {login} p/ fecho!")
        return

    positions = mt5.positions_get()
    closed = 0

    for pos in positions:
        close_type = (
            mt5.ORDER_TYPE_SELL if pos.type == mt5.ORDER_TYPE_BUY
            else mt5.ORDER_TYPE_BUY
        )

        tick = mt5.symbol_info_tick(pos.symbol)
        if not tick:
            continue

        price = tick.bid if close_type == mt5.ORDER_TYPE_SELL else tick.ask

        req = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": pos.symbol,
            "volume": pos.volume,
            "type": close_type,
            "price": price,
            "magic": pos.magic,
            "deviation": 30,
            "comment": "GUARDIAN_EMERGENCY"
        }

        result = mt5.order_send(req)
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            closed += 1

    mt5.shutdown()

    notify(f"🚨 *Guardian:* {closed} posições fechadas na conta {login}")
    log.warning(f"[GUARDIAN] {closed} posições fechadas na conta {login}")


# ============================================================
#   START
# ============================================================

def start_guardian_loop():
    import threading
    t = threading.Thread(target=guardian_loop, daemon=True)
    t.start()
    log.info("[GUARDIAN] Thread iniciada.")
