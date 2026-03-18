import os, requests
def get_telegram_creds(st=None):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if st is not None:
        try:
            token = token or st.secrets["telegram"]["bot_token"]
            chat_id = chat_id or st.secrets["telegram"]["chat_id"]
        except Exception:
            pass
    return token, chat_id
def send_telegram_message(text: str, st=None):
    token, chat_id = get_telegram_creds(st=st)
    if not token or not chat_id: return {"ok": False, "error": "Telegram no configurado"}
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    r = requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=20)
    try: return r.json()
    except Exception: return {"ok": False, "error": r.text}
