import psutil
import subprocess
import time
import os
from config import ACCOUNTS
from telegram_notifier import notify
from logger import log

# Indica ao bot quando pode enviar notificações
TELEGRAM_READY = False

# Histórico para evitar spam
ONLINE_STATUS = {}  # {login: True/False}


# ============================================================
#   SINALIZAR TELEGRAM PRONTO
# ============================================================

def telegram_is_ready():
    """
    Chamado pelo telegram_handler quando o bot arranca.
    Permite ao Watchdog enviar notificações de forma segura.
    """
    global TELEGRAM_READY
    TELEGRAM_READY = True
    log.info("[WATCHDOG] Telegram confirmado como READY.")


# ============================================================
#   VERIFICAR SE INSTÂNCIA EXATA DO TERMINAL ESTÁ ATIVA
# ============================================================

def is_running(path):
    """
    Valida se a instância EXATA do terminal está aberta.
    Evita confusão quando há vários MT5 instalados.
    """
    for proc in psutil.process_iter(attrs=["exe"]):
        try:
            exe = proc.info.get("exe")
            if exe and exe.lower() == path.lower():
                return True
        except Exception:
            pass
    return False


# ============================================================
#   LIMPAR PROCESSOS ZUMBIS
# ============================================================

def kill_zombies():
    """
    Elimina instâncias travadas do terminal64.exe.
    Evita processos mortos acumulados.
    """
    for proc in psutil.process_iter(attrs=["pid", "name", "status"]):
        try:
            if proc.info["name"] and "terminal64.exe" in proc.info["name"].lower():
                if proc.info["status"] in ("zombie", "stopped", "dead"):
                    proc.kill()
                    log.warning(f"[WATCHDOG] Processo zombie eliminado (PID {proc.info['pid']})")
        except Exception:
            pass


# ============================================================
#   INICIAR TERMINAL
# ============================================================

def start_terminal(path, login=None):
    """
    Abre o terminal MT5 indicado. Não bloqueia o loop.
    """
    try:
        subprocess.Popen([path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        log.info(f"[WATCHDOG] ▶ MT5 iniciado → {path}")

        if TELEGRAM_READY and login:
            notify(f"🟢 *MT5 iniciado (Conta {login})*")

        time.sleep(2)

    except Exception as e:
        msg = f"[WATCHDOG] ❌ ERRO a iniciar MT5 ({path}): {e}"
        log.error(msg)
        if TELEGRAM_READY:
            notify(msg)


# ============================================================
#   LOOP PRINCIPAL DO WATCHDOG
# ============================================================

def watchdog_loop():
    log.info("[WATCHDOG] Iniciado (multi-instância ativa).")

    if TELEGRAM_READY:
        notify("🟡 *Watchdog ativo e a monitorizar MT5*")

    # Iniciar com todos offline
    for acc in ACCOUNTS:
        ONLINE_STATUS[acc["login"]] = False

    while True:
        kill_zombies()

        for acc in ACCOUNTS:
            path = acc["path"]
            login = acc["login"]

            # Caminho inválido
            if not os.path.exists(path):
                msg = f"[WATCHDOG] ❌ Caminho MT5 inválido: {path}"
                log.error(msg)
                if TELEGRAM_READY:
                    notify(msg)
                continue

            running = is_running(path)

            # ==========================
            # SE ESTÁ DESLIGADO
            # ==========================
            if not running:

                # Apenas notificar quando realmente caiu
                if ONLINE_STATUS[login]:
                    if TELEGRAM_READY:
                        notify(
                            f"🔴 *MT5 caiu / fechou*\n"
                            f"Conta: {login}\n"
                            f"A reiniciar o terminal..."
                        )

                ONLINE_STATUS[login] = False
                log.warning(f"[WATCHDOG] ⚠ MT5 OFFLINE (Conta {login}) → Reiniciar...")

                start_terminal(path, login)

            # ==========================
            # SE ESTÁ LIGADO
            # ==========================
            else:
                # Apenas notificar quando recuperar
                if not ONLINE_STATUS[login]:
                    log.info(f"[WATCHDOG] ✔ MT5 ONLINE (Conta {login})")
                    if TELEGRAM_READY:
                        notify(f"🟢 *MT5 ONLINE*\nConta: {login}")

                ONLINE_STATUS[login] = True

            # Pequena pausa entre contas
            time.sleep(0.3)

        # Pausa geral entre ciclos
        time.sleep(1.5)


# ============================================================
#   THREAD DO WATCHDOG
# ============================================================

def start_watchdog():
    import threading
    t = threading.Thread(target=watchdog_loop, daemon=True)
    t.start()
    log.info("[WATCHDOG] Thread iniciada.")
