def inject_style(st):
    st.markdown('''
    <style>
    .stApp {background: radial-gradient(circle at top, #0b1020 0%, #05070d 60%, #010203 100%); color:#d7f7ff;}
    .main-title {font-size:2.4rem;font-weight:800;letter-spacing:1px;color:#91f2ff;text-shadow:0 0 14px rgba(145,242,255,.35);}
    .sub-title {color:#9fc7df;font-size:.95rem;margin-top:-8px;margin-bottom:12px}
    .metric-box {padding:14px;border-radius:16px;border:1px solid rgba(0,255,200,.15);background:linear-gradient(180deg, rgba(15,22,36,.82), rgba(7,11,18,.96));box-shadow:0 0 18px rgba(0,255,200,.08);}
    .neon {color:#37ffc8;font-weight:700;text-shadow:0 0 8px rgba(55,255,200,.3);}
    .warn {color:#ffcc66;font-weight:700;}
    .watermark {position: fixed; right: 16px; bottom: 12px; z-index: 9999; color: rgba(145,242,255,.25); font-weight: 800; font-size: 18px; pointer-events:none; user-select:none;}
    </style>
    <div class="watermark">Meli del Ro</div>
    ''', unsafe_allow_html=True)
