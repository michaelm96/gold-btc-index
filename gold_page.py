import altair as alt
import streamlit as st

from charts import SCORE_SCALE, line_chart
from gold_indicator import build_data, classify, score_against, score_columns


@st.cache_data(ttl=3600, show_spinner="Downloading market and FRED data...")
def load():
    return build_data()


st.title("Gold Valuation")

if st.button("Refresh data"):
    load.clear()

try:
    data = load()
except Exception as e:  # failures are never cached, so Refresh retries
    st.error(f"Data download failed: {e}")
    st.stop()

first_year, last_year = data.index[0].year, data.index[-1].year
from_year, to_year = st.slider(
    "Score against years", first_year, last_year, (first_year, last_year),
    help="Every score ranks a month against all months in these years. Narrow it to compare against a specific era.",
)
period = f"{from_year}–{to_year}"
data = score_against(data, from_year, to_year)
scored = data.dropna(subset=["gold_score"])
if scored.empty:
    st.warning("No composite score for these years: real-yield data starts in 1982. Pick a range that ends in 1982 or later.")
    st.stop()
latest = scored.iloc[-1]
view = data.loc[str(from_year):str(to_year)]
view_scored = view.dropna(subset=["gold_score"])

c1, c2, c3 = st.columns(3)
c1.metric(f"Valuation score (vs {period})", f"{latest['gold_score']:.1f} / 100")
c2.metric("Classification", classify(latest["gold_score"]))
c3.metric("Gold price (USD/oz)", f"${latest['gold']:,.2f}")

flipped = latest["gold_score"] + 0.2 * (100 - 2 * latest["score_real_yield"])
st.caption(
    f"As of {latest.name:%b %Y} (current month is partial; CPI and M2 carried forward from the last release). "
    f"Each month is ranked against all {len(view)} months from {period}, including months after it, so the charts "
    f"show where each month sits within the period, not what the score said at the time. "
    f"Unresolved: the real-yield indicator is inverted, so high real yields count as cheap. "
    f"Without that inversion the score would be {flipped:.1f}."
)

cols = st.columns(len(score_columns))
for col, (key, column) in zip(cols, score_columns.items()):
    col.metric(key, f"{latest[column]:.1f}")

line_chart(view_scored["gold_score"], "Composite valuation score (25 / 50 / 75 bands)", "Score", SCORE_SCALE, rules=(25, 50, 75))
line_chart(view["gold"], "Gold price (log scale)", "USD/oz", alt.Scale(type="log"))

st.subheader("Indicator scores")
for key, column in score_columns.items():
    line_chart(view_scored[column], key, "Score", SCORE_SCALE)

st.caption(
    "Sources: gold uses World Bank monthly averages from 1976, plus Yahoo month-to-date for months not yet published. "
    "S&P 500 is from Yahoo; CPI, M2 and real yields are from FRED. Real yield is the 10y TIPS yield from 2003, and for "
    "1982–2002 the 10y Treasury minus Cleveland Fed expected inflation. There is no composite before 1982 because "
    "real-yield data starts then. The command-line script (gold_indicator.py) instead ranks each month against "
    "the 30 years before it."
)

with st.expander("Data table"):
    st.dataframe(view.sort_index(ascending=False))
    st.download_button("Download CSV", view.to_csv(), "gold_valuation_history.csv", "text/csv")
