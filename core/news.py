import json
from pathlib import Path
NEWS_FILE = Path("data/news_feed.json")
def load_news():
    if not NEWS_FILE.exists(): return []
    try: return json.loads(NEWS_FILE.read_text(encoding="utf-8"))
    except Exception: return []
def trading_lock_from_news(news_items):
    return [n for n in news_items if n.get("bloquear_trading")]
