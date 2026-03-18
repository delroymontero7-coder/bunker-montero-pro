from typing import Optional, List, Dict, Any
import pandas as pd
import yfinance as yf
from .liquidity import equal_highs_lows, detect_sweep
from .orderflow_proxy import orderflow_proxy
from .sessions import session_name
from .storage import load_orderflow_state

def download_symbol(symbol: str) -> Optional[pd.DataFrame]:
    try:
        df = yf.download(symbol, interval="5m", period="1d", progress=False, auto_adjust=False, threads=False)
        if df is None or df.empty:
            return None
        df = df.reset_index()
        df.columns = [str(c[0]).lower() if isinstance(c, tuple) else str(c).lower() for c in df.columns]
        if "datetime" not in df.columns and "date" in df.columns:
            df = df.rename(columns={"date": "datetime"})
        required = ["datetime","open","high","low","close","volume"]
        if not all(c in df.columns for c in required):
            return None
        out = df[required].dropna().copy()
        out["ema_20"] = out["close"].ewm(span=20).mean()
        out["ema_50"] = out["close"].ewm(span=50).mean()
        out["ema_200"] = out["close"].ewm(span=200).mean()
        delta = out["close"].diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        rs = gain / loss.replace(0, pd.NA)
        out["rsi_14"] = 100 - (100 / (1 + rs.astype(float)))
        tr1 = out["high"] - out["low"]
        tr2 = (out["high"] - out["close"].shift(1)).abs()
        tr3 = (out["low"] - out["close"].shift(1)).abs()
        out["atr_14"] = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1).rolling(14).mean()
        out["vol_avg_20"] = out["volume"].rolling(20).mean()
        out["vol_intensity"] = out["volume"] / out["vol_avg_20"]
        return out
    except Exception:
        return None

def _flow_bonus(symbol: str):
    state = load_orderflow_state()
    if not state:
        return {"book_bias": 0.0, "trade_delta": 0.0}
    top_book = state.get("top_book", {})
    trades = state.get("trades", {})
    book = top_book.get(symbol, {})
    bids = book.get("bids", [])
    asks = book.get("asks", [])
    bid_sz = sum(float(x[1]) for x in bids) if bids else 0.0
    ask_sz = sum(float(x[1]) for x in asks) if asks else 0.0
    trade_delta = 0.0
    for t in trades.get(symbol, []):
        side = str(t.get("side","")).lower()
        size = float(t.get("size", 0) or 0)
        trade_delta += size if side == "buy" else -size
    return {"book_bias": bid_sz - ask_sz, "trade_delta": trade_delta}

def evaluate_symbol(symbol: str) -> Optional[Dict[str, Any]]:
    df = download_symbol(symbol)
    if df is None or len(df) < 60:
        return None

    last = df.iloc[-1]
    price = float(last["close"])
    tech_score = 0
    inst_score = 0
    flow_score = 0
    reasons = []

    if price > float(last["ema_20"]):
        tech_score += 15; reasons.append("close>ema20")
    if price > float(last["ema_50"]):
        tech_score += 20; reasons.append("close>ema50")
    if price > float(last["ema_200"]):
        tech_score += 25; reasons.append("close>ema200")
    if float(last["ema_20"]) > float(last["ema_50"]):
        tech_score += 15; reasons.append("ema20>ema50")
    rsi = float(last["rsi_14"]) if pd.notna(last["rsi_14"]) else 50
    if 45 <= rsi <= 70:
        tech_score += 15; reasons.append("rsi_ok")
    if float(df["close"].iloc[-1]) > float(df["close"].iloc[-3]):
        tech_score += 10; reasons.append("momentum")

    liq = equal_highs_lows(df)
    sweep = detect_sweep(df)
    flow = orderflow_proxy(df)
    vol_int = float(last["vol_intensity"]) if pd.notna(last["vol_intensity"]) else 1.0

    if vol_int >= 1.5:
        inst_score += 25; reasons.append("high_volume")
    if flow["delta_proxy"] > 0:
        inst_score += 15; reasons.append("delta+")
    if flow["absorption"] > 0:
        inst_score += 15; reasons.append("absorption")
    if liq["equal_highs"] or liq["equal_lows"]:
        inst_score += 15; reasons.append("visible_liquidity")
    if sweep != "none":
        inst_score += 15; reasons.append(sweep)

    fb = _flow_bonus(symbol)
    if fb["book_bias"] > 0:
        flow_score += 20; reasons.append("book_bid_bias")
    elif fb["book_bias"] < 0:
        flow_score += 8; reasons.append("book_ask_pressure")
    if fb["trade_delta"] > 0:
        flow_score += 20; reasons.append("trade_delta+")
    elif fb["trade_delta"] < 0:
        flow_score += 8; reasons.append("trade_delta-")

    final_score = tech_score + inst_score + flow_score
    if tech_score < 70 or inst_score < 50 or final_score < 140:
        return {
            "symbol": symbol, "side": "NO_TRADE", "entry": round(price,4), "sl": None, "tp": None,
            "tech_score": round(tech_score,2), "inst_score": round(inst_score,2), "flow_score": round(flow_score,2),
            "final_score": round(final_score,2), "session": session_name(),
            "reasons": " | ".join(reasons + ["no_trade_filter"])
        }

    side = "BUY" if price >= float(last["ema_50"]) else "SELL"
    atr = float(last["atr_14"]) if pd.notna(last["atr_14"]) and last["atr_14"] > 0 else price * 0.01
    recent_hi = float(df["high"].tail(20).max())
    recent_lo = float(df["low"].tail(20).min())
    if side == "BUY":
        sl = min(recent_lo, price - atr * 1.2)
        tp = price + (price - sl) * 2
    else:
        sl = max(recent_hi, price + atr * 1.2)
        tp = price - (sl - price) * 2

    return {
        "symbol": symbol, "side": side, "entry": round(price,4), "sl": round(sl,4), "tp": round(tp,4),
        "tech_score": round(tech_score,2), "inst_score": round(inst_score,2), "flow_score": round(flow_score,2),
        "final_score": round(final_score,2), "session": session_name(), "reasons": " | ".join(reasons)
    }

def run_scan(symbols: List[str]):
    out = []
    for s in symbols:
        sig = evaluate_symbol(s)
        if sig is not None:
            out.append(sig)
    return out
