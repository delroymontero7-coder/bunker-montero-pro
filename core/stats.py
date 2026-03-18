import pandas as pd
def compute_stats(journal):
    if not journal: return {}
    df = pd.DataFrame(journal)
    stats = {"total_signals": len(df)}
    if "side" in df.columns:
        stats["buy_count"] = int((df["side"] == "BUY").sum())
        stats["sell_count"] = int((df["side"] == "SELL").sum())
        stats["no_trade_count"] = int((df["side"] == "NO_TRADE").sum())
    for col in ["tech_score","inst_score","flow_score","final_score"]:
        if col in df.columns:
            stats[f"avg_{col}"] = round(float(pd.to_numeric(df[col], errors="coerce").mean()), 2)
    if "session" in df.columns:
        stats["top_sessions"] = df["session"].value_counts().to_dict()
    if "symbol" in df.columns:
        stats["top_symbols"] = df["symbol"].value_counts().head(5).to_dict()
    return stats
