import streamlit as st

DEFAULT_PASSWORDS = {"062711.M", "062711.m"}

def valid_passwords():
    pwds = set(DEFAULT_PASSWORDS)
    try:
        secret_pwd = st.secrets["security"]["password"]
        if secret_pwd:
            pwds.add(secret_pwd)
    except Exception:
        pass
    return pwds

def login_gate():
    if "auth_ok" not in st.session_state:
        st.session_state.auth_ok = False
    if st.session_state.auth_ok:
        return True

    st.markdown("## 🔐 Panel de Seguridad")
    pwd = st.text_input("Contraseña", type="password")
    if st.button("Entrar al Bunker"):
        if pwd in valid_passwords():
            st.session_state.auth_ok = True
            st.success("Acceso concedido")
            st.rerun()
        else:
            st.error("Contraseña incorrecta")
    st.stop()
