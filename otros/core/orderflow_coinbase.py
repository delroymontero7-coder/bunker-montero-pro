import asyncio, json
from collections import defaultdict
import websockets
from core.storage import save_orderflow_state
WS_URL = "wss://advanced-trade-ws.coinbase.com"
PRODUCT_IDS = ["BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD"]
state = {"last_trades": defaultdict(list), "bids": defaultdict(dict), "asks": defaultdict(dict)}
def compact_state():
    out = {"trades": {}, "top_book": {}}
    for product, trades in state["last_trades"].items():
        out["trades"][product] = trades[-50:]
    for product in PRODUCT_IDS:
        bids = state["bids"].get(product, {})
        asks = state["asks"].get(product, {})
        out["top_book"][product] = {
            "bids": sorted([(float(px), float(sz)) for px, sz in bids.items()], reverse=True)[:12],
            "asks": sorted([(float(px), float(sz)) for px, sz in asks.items()])[:12],
        }
    return out
async def stream():
    async with websockets.connect(WS_URL, ping_interval=20, ping_timeout=20) as ws:
        await ws.send(json.dumps({"type":"subscribe","channel":"market_trades","product_ids":PRODUCT_IDS}))
        await ws.send(json.dumps({"type":"subscribe","channel":"level2","product_ids":PRODUCT_IDS}))
        while True:
            raw = await ws.recv()
            msg = json.loads(raw)
            channel = msg.get("channel")
            events = msg.get("events", [])
            if channel == "market_trades":
                for ev in events:
                    for tr in ev.get("trades", []):
                        product = tr.get("product_id")
                        if not product: continue
                        state["last_trades"][product].append({"price": tr.get("price"), "size": tr.get("size"), "side": tr.get("side"), "time": tr.get("time")})
                        state["last_trades"][product] = state["last_trades"][product][-200:]
            if channel == "level2":
                for ev in events:
                    product = ev.get("product_id")
                    if not product: continue
                    for up in ev.get("updates", []):
                        side = up.get("side"); px = up.get("price_level"); qty = up.get("new_quantity")
                        if side == "bid":
                            if qty == "0": state["bids"][product].pop(px, None)
                            else: state["bids"][product][px] = qty
                        elif side == "offer":
                            if qty == "0": state["asks"][product].pop(px, None)
                            else: state["asks"][product][px] = qty
            save_orderflow_state(compact_state())
if __name__ == "__main__":
    asyncio.run(stream())
