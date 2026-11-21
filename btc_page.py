import altair as alt
import streamlit as st

from btc_indicator import build_btc_data, score_btc, score_columns
from charts import SCORE_SCALE, line_chart
from gold_indicator import classify


@st.cache_data(ttl=3600, show_spinner="Downloading BTC and gold data...")
def load_btc():
    return build_btc_data()


st.title("BTC Valuation")

if st.button("Refresh data"):
    load_btc.clear()

try:
    data = load_btc()
except Exception as e:  # failures are never cached, so Refresh retries
    st.error(f"Data download failed: {e}")
    st.stop()

first_year, last_year = data.index[0].year, data.index[-1].year
from_year, to_year = st.slider(
    "Score against years", first_year, last_year, (first_year, last_year),
    help="Every score ranks a month against all months in these years. Narrow it to compare against a specific era.",
)
period = f"{from_year}–{to_year}"
data = score_btc(data, from_year, to_year)
scored = data.dropna(subset=["btc_score"])
if scored.empty:
    st.warning("No composite score for these years: the 200-week measures start in 2014. Pick a range that ends in 2014 or later.")
    st.stop()
latest = scored.iloc[-1]
view = data.loc[str(from_year):str(to_year)]
view_scored = view.dropna(subset=["btc_score"])

c1, c2, c3 = st.columns(3)
c1.metric(f"Valuation score (vs {period})", f"{latest['btc_score']:.1f} / 100")
c2.metric("Classification", classify(latest["btc_score"]))
c3.metric("BTC price (USD)", f"${latest['btc']:,.0f}")

st.caption(
    f"As of {latest.name:%b %Y} (current month is partial). "
    f"Each month is ranked against all {len(view)} months from {period}, including months after it, so the charts "
    f"show where each month sits within the period, not what the score said at the time. "
    f"Weights: MVRV 50, 200-week multiple 25, BTC/gold 25. The last two move almost together, so together they count as much as MVRV."
)

cols = st.columns(len(score_columns))
for col, (key, column) in zip(cols, score_columns.items()):
    col.metric(key, f"{latest[column]:.1f}")

line_chart(view_scored["btc_score"], "Composite valuation score (25 / 50 / 75 bands)", "Score", SCORE_SCALE, rules=(25, 50, 75))
line_chart(view["btc"], "BTC price (log scale)", "USD", alt.Scale(type="log"))

st.subheader("Indicator scores")
for key, column in score_columns.items():
    line_chart(view_scored[column], key, "Score", SCORE_SCALE)

st.caption(
    "Sources: BTC price and MVRV (market value ÷ the average price holders paid) are daily from the CoinMetrics "
    "community API, from July 2010. ma_multiple is BTC ÷ its 46-month (≈200-week) average. btc_gold is the "
    "BTC/gold ratio ÷ its own 46-month average; gold is the same series as the Gold page. The composite starts "
    "in 2014 because the 46-month averages need four years of data."
)

with st.expander("Data table"):
    st.dataframe(view.sort_index(ascending=False))
    st.download_button("Download CSV", view.to_csv(), "btc_valuation_history.csv", "text/csv")
