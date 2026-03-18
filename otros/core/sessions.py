from datetime import datetime, timezone
def session_name():
    h = datetime.now(timezone.utc).hour
    if 0 <= h < 8: return "ASIA"
    if 8 <= h < 13: return "LONDON"
    if 13 <= h <= 20: return "NEW_YORK"
    return "AFTER_HOURS"
