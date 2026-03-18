import base64
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go

from core.style import inject_style
from core.security import login_gate
from core.scanner import run_scan, download_symbol
from core.storage import load_journal, save_signal, load_meli_memory, save_meli_message, load_orderflow_state, load_alerts_sent, save_alerts_sent
from core.meli_agent import answer_meli, build_end_of_day_summary, format_telegram_summary, load_reading_list
from core.news import load_news, trading_lock_from_news
from core.sessions import session_name
from core.telegram_notify import send_telegram_message
from core.stats import compute_stats
from plugins.user_indicator import apply_user_indicator

st.set_page_config(page_title="Bunker Elite V12", layout="wide")
inject_style(st)
login_gate()

st.markdown('<div class="main-title">BUNKER ELITE · MELI · NASA MODE 12/10</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Meli del Ro · Deploy Ready · Auto Alert · No Operar · Stats</div>', unsafe_allow_html=True)

symbols = ["BTC-USD","ETH-USD","SOL-USD","BNB-USD","XRP-USD","ADA-USD","DOGE-USD","AVAX-USD","DOT-USD","LTC-USD"]
journal = load_journal()
critical_news = trading_lock_from_news(load_news())
of = load_orderflow_state()
stats = compute_stats(journal)

c1, c2, c3, c4, c5, c6 = st.columns(6)
with c1: st.markdown(f'<div class="metric-box"><div>Sesión</div><div class="neon">{session_name()}</div></div>', unsafe_allow_html=True)
with c2: st.markdown(f'<div class="metric-box"><div>Mercados</div><div class="neon">{len(symbols)}</div></div>', unsafe_allow_html=True)
with c3: st.markdown(f'<div class="metric-box"><div>Journal</div><div class="neon">{len(journal)}</div></div>', unsafe_allow_html=True)
with c4:
    state = "LOCK" if critical_news else "OK"
    css = "warn" if critical_news else "neon"
    st.markdown(f'<div class="metric-box"><div>Noticias</div><div class="{css}">{state}</div></div>', unsafe_allow_html=True)
with c5: st.markdown(f'<div class="metric-box"><div>Order Flow</div><div class="neon">{"ON" if of else "OFF"}</div></div>', unsafe_allow_html=True)
with c6: st.markdown(f'<div class="metric-box"><div>Stats</div><div class="neon">{stats.get("total_signals",0)}</div></div>', unsafe_allow_html=True)

tabs = st.tabs(["Scanner","Noticias","Biblioteca","MELI","Journal","Visual","Telegram","Order Flow","Stats"])

with tabs[0]:
    st.subheader("Multi Scanner")
    selected = st.multiselect("Selecciona mercados", symbols, default=symbols[:5])
    send_alerts = st.checkbox("Mandar señales a Telegram", value=False)
    if st.button("Escanear ahora"):
        results = run_scan(selected)
        alerts_sent = load_alerts_sent()
        if not results:
            st.info("Sin señales en este ciclo.")
        for signal in results:
            save_signal(signal)
            marker = "🚫" if signal["side"] == "NO_TRADE" else "✅"
            st.success(f"{marker} {signal['symbol']} {signal['side']} | {signal['session']}")
            st.json(signal)
            unique_key = f"{signal['symbol']}|{signal['side']}|{signal.get('entry')}|{signal.get('final_score')}"
            if send_alerts and unique_key not in alerts_sent and signal["side"] != "NO_TRADE":
                msg = (
                    f"SNIPER SIGNAL\n{signal['symbol']} {signal['side']}\n"
                    f"Entrada: {signal['entry']}\nSL: {signal['sl']}\nTP: {signal['tp']}\n"
                    f"Tech: {signal['tech_score']} | Inst: {signal['inst_score']} | Flow: {signal.get('flow_score',0)}\n"
                    f"Final: {signal.get('final_score',0)}\n"
                    f"{signal['reasons']}\nMeli del Ro"
                )
                st.write(send_telegram_message(msg, st=st))
                alerts_sent.add(unique_key)
        save_alerts_sent(alerts_sent)

    st.subheader("Panel rápido por símbolo")
    one = st.selectbox("Ver símbolo", symbols, index=0)
    df = download_symbol(one)
    if df is not None:
        df = apply_user_indicator(df)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df["datetime"].tail(120), y=df["close"].tail(120), mode="lines", name="Close"))
        fig.add_trace(go.Scatter(x=df["datetime"].tail(120), y=df["sniper_user"].tail(120), mode="lines", name="Indicador"))
        fig.add_trace(go.Scatter(x=df["datetime"].tail(120), y=df["user_fast"].tail(120), mode="lines", name="Fast"))
        recent_signals = [j for j in journal if j.get("symbol") == one and j.get("side") in ("BUY","SELL")][-5:]
        for s in recent_signals:
            fig.add_hline(y=float(s["entry"]), line_dash="dot", annotation_text=f"{s['side']} ENTRY")
            if s.get("sl") is not None: fig.add_hline(y=float(s["sl"]), line_dash="dash", annotation_text="SL")
            if s.get("tp") is not None: fig.add_hline(y=float(s["tp"]), line_dash="dash", annotation_text="TP")
        fig.update_layout(height=500, template="plotly_dark", title=f"{one} · Meli del Ro")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Sin datos para ese activo.")

with tabs[1]:
    st.subheader("Radar de Noticias")
    news = load_news()
    if not news: st.info("No hay feed cargado.")
    else:
        for n in news:
            with st.container(border=True):
                st.markdown(f"**{n['titulo']}**")
                st.write(f"Impacto: {n['impacto']} | Hora UTC: {n['hora_utc']}")
                st.write(n["detalle"])
                if n.get("bloquear_trading"): st.warning("Bloquea trading")

with tabs[2]:
    st.subheader("Biblioteca")
    reading = load_reading_list()
    if reading: st.dataframe(pd.DataFrame(reading), use_container_width=True)
    books_dir = Path("books")
    pdfs = sorted(books_dir.glob("*.pdf"))
    if not pdfs:
        st.info("Pon tus PDFs dentro de /books para abrirlos aquí.")
    else:
        names = [p.name for p in pdfs]
        choice = st.selectbox("Libro PDF", names)
        pdf_path = books_dir / choice
        pdf_bytes = pdf_path.read_bytes()
        st.download_button("Descargar PDF", data=pdf_bytes, file_name=choice, mime="application/pdf")
        b64 = base64.b64encode(pdf_bytes).decode("utf-8")
        st.markdown(f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="700" type="application/pdf"></iframe>', unsafe_allow_html=True)

with tabs[3]:
    st.subheader("Hablar con MELI")
    memory = load_meli_memory()
    for item in memory[-10:]:
        st.write(f"**{item.get('role','MELI')}**: {item.get('content','')}")
    prompt = st.text_input("Pregúntale a MELI")
    if st.button("Enviar a MELI"):
        save_meli_message({"role":"USER","content":prompt})
        ans = answer_meli(prompt, load_journal())
        save_meli_message({"role":"MELI","content":str(ans)})
        st.success("Respuesta guardada")
        st.write(ans)
    st.subheader("Panel NO OPERAR")
    no_trade = [j for j in journal if j.get("side") == "NO_TRADE"][-10:]
    if no_trade: st.dataframe(pd.DataFrame(no_trade), use_container_width=True)
    else: st.info("Sin señales NO_TRADE todavía.")

with tabs[4]:
    st.subheader("Journal")
    if journal:
        st.dataframe(pd.DataFrame(journal), use_container_width=True)
        st.subheader("Resumen fin de día")
        st.json(build_end_of_day_summary(journal))
    else:
        st.info("Sin señales todavía.")

with tabs[5]:
    st.subheader("Visual integrado")
    html_path = Path("visual/tradingview_like_template.html")
    if html_path.exists(): components.html(html_path.read_text(encoding="utf-8"), height=760, scrolling=True)
    else: st.warning("No se encontró la plantilla visual.")

with tabs[6]:
    st.subheader("Telegram")
    test_msg = st.text_input("Mensaje de prueba", "Bunker Elite online · Meli del Ro")
    if st.button("Enviar prueba Telegram"): st.write(send_telegram_message(test_msg, st=st))
    if st.button("Mandar resumen del día a Telegram"):
        summary = build_end_of_day_summary(load_journal())
        st.write(send_telegram_message(format_telegram_summary(summary), st=st))

with tabs[7]:
    st.subheader("Order Flow")
    state = load_orderflow_state()
    if not state: st.info("No hay order flow cargado todavía. Ejecuta `python core/orderflow_coinbase.py`.")
    else: st.json(state)

with tabs[8]:
    st.subheader("Stats")
    if stats:
        st.json(stats)
        if "top_symbols" in stats:
            df_stats = pd.DataFrame(list(stats["top_symbols"].items()), columns=["symbol","count"])
            st.bar_chart(df_stats.set_index("symbol"))
        if "top_sessions" in stats:
            df_sess = pd.DataFrame(list(stats["top_sessions"].items()), columns=["session","count"])
            st.bar_chart(df_sess.set_index("session"))
    else:
        st.info("Aún no hay stats.")
