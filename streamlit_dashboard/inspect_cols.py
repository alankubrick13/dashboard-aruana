import streamlit as st
import sys
sys.path.append("/home/alankubrick/Documentos/BASE DE DADOS PROJETO/streamlit_dashboard")
import app

# Mock streamlit session state to avoid errors
class DummySessionState(dict):
    def __getattr__(self, key):
        if key == "filtro_ano": return "2024"
        return self.get(key)
st.session_state = DummySessionState()
st.session_state["filtro_ano"] = "2024"

try:
    df = app.get_filtered_data()
    print("COLUMNS: ", list(df.columns))
except Exception as e:
    print("ERROR:", e)
