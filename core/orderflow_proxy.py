def orderflow_proxy(df):
    recent = df.tail(20)
    up_vol = float(recent.loc[recent["close"] >= recent["open"], "volume"].sum())
    down_vol = float(recent.loc[recent["close"] < recent["open"], "volume"].sum())
    delta_proxy = up_vol - down_vol
    last = recent.iloc[-1]
    upper_wick = float(last["high"] - max(last["open"], last["close"]))
    lower_wick = float(min(last["open"], last["close"]) - last["low"])
    body = abs(float(last["close"] - last["open"]))
    absorption = 1.0 if max(upper_wick, lower_wick) / max(body, 1e-9) >= 2.5 and float(last["volume"]) > float(recent["volume"].mean()) else 0.0
    return {"delta_proxy": delta_proxy, "absorption": absorption}
