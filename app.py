import streamlit as st

st.set_page_config(page_title="Valuation", layout="wide")
st.navigation([
    st.Page("gold_page.py", title="Gold", default=True),
    st.Page("btc_page.py", title="BTC"),
]).run()
