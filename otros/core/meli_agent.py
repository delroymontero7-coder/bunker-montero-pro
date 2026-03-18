import json
from collections import Counter
from pathlib import Path
from .stats import compute_stats
READING = Path("data/reading_list.json")

def load_reading_list():
    if not READING.exists(): return []
    try: return json.loads(READING.read_text(encoding="utf-8"))
    except Exception: return []

def answer_meli(prompt: str, journal: list):
    p = prompt.lower()
    if "90" in p or "alta" in p:
        high_q = [j for j in journal if float(j.get("final_score",0)) >= 160]
        return f"Detecté {len(high_q)} setups de alta calidad."
    if "resumen" in p or "dia" in p:
        return build_end_of_day_summary(journal)
    if "no operar" in p:
        no_trades = [j for j in journal if j.get("side") == "NO_TRADE"][-10:]
        return {"no_trade_count": len(no_trades), "detalle": no_trades}
    if "libro" in p or "mentalidad" in p or "millonario" in p:
        return {"recomendados": load_reading_list()[:5]}
    if "por que" in p:
        if not journal: return "No hay journal todavía."
        last = journal[-1]
        return f"La última evaluación fue {last.get('symbol')} {last.get('side')} por {last.get('reasons')}"
    return "Puedo resumir el día, explicar no-trades, revisar el journal y recomendar lecturas."

def build_end_of_day_summary(journal):
    if not journal:
        return {"resumen": "No hubo señales guardadas hoy.", "top_symbols": [], "why_no_trade": "No hubo setups suficientes."}
    total = len(journal)
    buys = sum(1 for j in journal if j.get("side") == "BUY")
    sells = sum(1 for j in journal if j.get("side") == "SELL")
    no_trades = sum(1 for j in journal if j.get("side") == "NO_TRADE")
    top_symbols = Counter(j.get("symbol") for j in journal).most_common(5)
    high_quality = [j for j in journal if float(j.get("final_score",0)) >= 160]
    return {
        "resumen": f"Se guardaron {total} eventos. BUY={buys}, SELL={sells}, NO_TRADE={no_trades}.",
        "top_symbols": top_symbols,
        "high_quality_count": len(high_quality),
        "stats": compute_stats(journal),
        "observacion": "MELI resume el día aunque no operes."
    }

def format_telegram_summary(summary):
    if isinstance(summary, dict):
        return f"Resumen del día\n{summary.get('resumen')}\nTop símbolos: {summary.get('top_symbols')}\nSeñales altas: {summary.get('high_quality_count', 0)}\nMeli del Ro"
    return str(summary)
