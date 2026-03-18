def equal_highs_lows(df, window=5, tolerance_ratio=0.0015):
    recent = df.tail(window)
    highs = recent["high"].tolist()
    lows = recent["low"].tolist()
    eq_high = False
    eq_low = False
    if highs:
        mh = max(highs)
        if mh:
            eq_high = sum(abs(h - mh) / mh <= tolerance_ratio for h in highs) >= 2
    if lows:
        ml = min(lows)
        if ml:
            eq_low = sum(abs(l - ml) / ml <= tolerance_ratio for l in lows) >= 2
    return {"equal_highs": eq_high, "equal_lows": eq_low}

def detect_sweep(df):
    if len(df) < 6: return "none"
    last = df.iloc[-1]
    prev = df.iloc[-2]
    recent = df.iloc[-6:-1]
    if float(last["low"]) < float(recent["low"].min()) and float(last["close"]) > float(prev["low"]):
        return "buy_sweep"
    if float(last["high"]) > float(recent["high"].max()) and float(last["close"]) < float(prev["high"]):
        return "sell_sweep"
    return "none"
