def apply_user_indicator(df):
    out = df.copy()
    out["sniper_user"] = out["close"].rolling(10).mean()
    out["user_fast"] = out["close"].rolling(5).mean()
    return out
