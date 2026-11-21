# Smoke test against live data (needs network). Run: .venv/bin/python test_app.py
from streamlit.testing.v1 import AppTest

import gold_indicator as g

# Scoring: fixed-period ranks are checked by a second method.
data = g.build_data()
s = g.score_against(data, 2004, 2026)
x, ref = data["real_gold"].iloc[-1], data.loc["2004":"2026", "real_gold"]
assert abs(s["score_real_gold"].iloc[-1] - (ref <= x).mean() * 100) < 1e-9
# 1997-2026 is almost the rolling 30-year window, so the latest composite should nearly match.
assert abs(g.score_against(data, 1997, 2026)["gold_score"].iloc[-1] - data["gold_score"].dropna().iloc[-1]) < 2


def score(at):
    label = next(m for m in at.metric if m.label.startswith("Valuation score"))
    return float(label.value.split("/")[0])


at = AppTest.from_file("app.py", default_timeout=180).run()
assert not at.exception, at.exception
assert not at.error, [e.value for e in at.error]
metrics = {m.label: m.value for m in at.metric}
assert {"Classification", "Gold price (USD/oz)", "real_gold", "ma_deviation"} <= set(metrics), metrics
full = score(at)
assert 0 <= full <= 100, full
assert len(at.get("vega_lite_chart")) == 7  # composite, price, 5 indicators

at.slider[0].set_value((2004, 2026)).run()  # the year range changes the calculation, not just the view
assert not at.exception, at.exception
assert score(at) != full, (score(at), full)
assert len(at.get("vega_lite_chart")) == 7

at.slider[0].set_value((1976, 1980)).run()  # no real-yield data before 1982: warning instead of scores
assert not at.exception, at.exception
assert at.warning, "expected a no-composite warning"

at.slider[0].set_value((1976, 2026)).run()
at.button[0].click().run()  # Refresh clears the cache and reloads
assert not at.exception, at.exception

print("OK", metrics)
