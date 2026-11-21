# Smoke test against live data (needs network). Run: .venv/bin/python test_btc.py
from streamlit.testing.v1 import AppTest

import btc_indicator as b

# Scoring: a fixed-period rank checked by a second method.
data = b.build_btc_data()
s = b.score_btc(data, 2015, 2026)
x, ref = data["mvrv"].iloc[-1], data.loc["2015":"2026", "mvrv"]
assert abs(s["score_mvrv"].iloc[-1] - (ref <= x).mean() * 100) < 1e-9
assert s["btc_score"].first_valid_index().year == 2014  # 46-month averages from July 2010 data
assert not data[["btc", "mvrv", "gold"]].isna().any().any()


def score(at):
    label = next(m for m in at.metric if m.label.startswith("Valuation score"))
    return float(label.value.split("/")[0])


at = AppTest.from_file("app.py", default_timeout=180).run()
at.switch_page("btc_page.py").run()  # through the router, so a wrong page path fails here
assert not at.exception, at.exception
assert not at.error, [e.value for e in at.error]
metrics = {m.label: m.value for m in at.metric}
assert {"Classification", "BTC price (USD)", "mvrv", "ma_multiple", "btc_gold"} <= set(metrics), metrics
full = score(at)
assert 0 <= full <= 100, full
assert len(at.get("vega_lite_chart")) == 5  # composite, price, 3 indicators

at.slider[0].set_value((2018, 2026)).run()  # the year range changes the calculation
assert not at.exception, at.exception
assert score(at) != full, (score(at), full)

at.slider[0].set_value((2010, 2012)).run()  # 46-month measures start in 2014: warning instead of scores
assert not at.exception, at.exception
assert at.warning, "expected a no-composite warning"

at.slider[0].set_value((2010, 2026)).run()
at.button[0].click().run()  # Refresh clears the cache and reloads
assert not at.exception, at.exception

print("OK", metrics)
