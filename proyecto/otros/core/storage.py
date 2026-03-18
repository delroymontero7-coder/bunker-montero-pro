import json
from pathlib import Path

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
JOURNAL = DATA_DIR / "journal.jsonl"
MELI = DATA_DIR / "meli_memory.jsonl"
ORDERFLOW = DATA_DIR / "orderflow_state.json"
ALERTS = DATA_DIR / "alerts_sent.json"

def append_jsonl(path: Path, item: dict):
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")

def read_jsonl(path: Path):
    if not path.exists():
        return []
    out = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                pass
    return out

def save_signal(item: dict): append_jsonl(JOURNAL, item)
def load_journal(): return read_jsonl(JOURNAL)
def save_meli_message(item: dict): append_jsonl(MELI, item)
def load_meli_memory(): return read_jsonl(MELI)

def load_orderflow_state():
    if not ORDERFLOW.exists():
        return {}
    try:
        return json.loads(ORDERFLOW.read_text(encoding="utf-8"))
    except Exception:
        return {}

def load_alerts_sent():
    if not ALERTS.exists():
        return set()
    try:
        return set(json.loads(ALERTS.read_text(encoding="utf-8")))
    except Exception:
        return set()

def save_alerts_sent(items):
    ALERTS.write_text(json.dumps(sorted(list(items)), ensure_ascii=False, indent=2), encoding="utf-8")
