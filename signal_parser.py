import re

from logger import log


# ============================================================
#   NORMALIZAÇÃO DE SÍMBOLOS (SUPORTE COMPLETO)
# ============================================================

ALIASES = {
    "GOLD": "XAUUSD",
    "XAU": "XAUUSD",
    "XAU/USD": "XAUUSD",
    "XAU-USD": "XAUUSD",
    "GOLD/USD": "XAUUSD",
}

# sufixos comuns de corretoras
SUFIXOS = [".p", ".pi", ".r", ".rp", ".var", ".m", ".i"]


def normalize_symbol(text):
    """
    Converte qualquer variação de XAUUSD para o formato correto.
    Remove sufixos (.pi, .p, .r…)
    """

    text = text.upper().strip()

    # Remover sufixos
    for s in SUFIXOS:
        if text.endswith(s.upper()):
            text = text[: -len(s)]

    # Aplicar aliases
    if text in ALIASES:
        return ALIASES[text]

    return text


# ============================================================
#   LIMPAR NÚMEROS COM ESPAÇOS
# ============================================================

def clean_number(n):
    if not n:
        return None

    n = n.replace(" ", "")
    n = n.replace(",", ".")  # caso apareça vírgula
    try:
        return float(n)
    except Exception:
        return None


# ============================================================
#   PARSER PRINCIPAL DE SINAIS
# ============================================================

def parse_signal(raw):
    try:
        text = raw.upper()

        # --------------------------------------------
        # DIREÇÃO (BUY / SELL)
        # --------------------------------------------
        direction = None
        if "BUY" in text and "SELL" in text:
            # prefer the first occurrence to evitar conflitos
            direction = "BUY" if text.index("BUY") < text.index("SELL") else "SELL"
        elif "BUY" in text:
            direction = "BUY"
        elif "SELL" in text:
            direction = "SELL"

        if not direction:
            return None

        # --------------------------------------------
        # SÍMBOLO (XAUUSD / XAUUSD.p / GOLD / etc)
        # --------------------------------------------
        symbol_match = re.search(r"(XAUUSD\w*|GOLD|XAU|[A-Z]{3,10}\w*)", text)
        if not symbol_match:
            return None

        symbol = normalize_symbol(symbol_match.group(1))

        # --------------------------------------------
        # ENTRY NUMÉRICO
        # --------------------------------------------
        entry_match = re.search(r"ENTRY[: ]+([0-9\.\, ]+)", text)
        entry = clean_number(entry_match.group(1)) if entry_match else None

        # ENTRY market
        if "ENTRY" in text and "MARKET" in text:
            entry = "market"

        # Caso o sinal seja no formato:
        # BUY XAUUSD 4234.5
        if entry is None:
            inline = re.search(r"(BUY|SELL)\s+\w+\s+([0-9\.\, ]+)", text)
            if inline:
                entry = clean_number(inline.group(2))

        # --------------------------------------------
        # TAKE PROFITS
        # --------------------------------------------
        def find_tp(label):
            m = re.search(label + r"[: ]+([0-9\.\, ]+)", text)
            return clean_number(m.group(1)) if m else None

        tp1 = find_tp("TP1")
        tp2 = find_tp("TP2")
        tp3 = find_tp("TP3")

        # Formatos alternativos
        if not tp1:
            alt = re.search(r"TAKE PROFIT\s*1[: ]+([0-9\.\, ]+)", text)
            if alt:
                tp1 = clean_number(alt.group(1))

        # --------------------------------------------
        # STOP LOSS
        # --------------------------------------------
        sl_match = re.search(r"SL[: ]+([0-9\.\, ]+)", text)
        sl = clean_number(sl_match.group(1)) if sl_match else None

        # Formatos alternativos
        if not sl:
            alt = re.search(r"STOP LOSS[: ]+([0-9\.\, ]+)", text)
            if alt:
                sl = clean_number(alt.group(1))

        # --------------------------------------------
        # RESULTADO FINAL
        # --------------------------------------------
        result = {
            "symbol": symbol,
            "direction": direction,
            "entry": entry,
            "tp1": tp1,
            "tp2": tp2,
            "tp3": tp3,
            "sl": sl,
            "type": "ENTRY"  # único tipo tratado por enquanto
        }

        log.info(
            f"[PARSER] OK → {symbol} {direction} @ {entry} | SL={sl} | TP1={tp1}"
        )
        return result

    except Exception as e:
        log.error(f"[PARSER ERROR] {e}")
        return None
