# Gold & BTC Valuation Index

**Live dashboard:** https://gold-btc-index-acehilm.streamlit.app/

A 0–100 score for how cheap or expensive gold and bitcoin are against their own history. 0 is the cheapest the asset has been in the years you compare against; 100 is the most expensive. Each asset has its own page in the sidebar.

| Score | Label |
|---|---|
| 0–25 | Extremely cheap |
| 25–40 | Cheap |
| 40–60 | Fair value |
| 60–75 | Expensive |
| 75–100 | Extremely expensive |

## How the score works

Each indicator is turned into a percentile: the share of months, within the years you pick, where the indicator was at or below its current value. The composite is a weighted average of those percentiles.

The **"Score against years"** slider sets those years, which is how you change the baseline. Ranking gold against 2004–2026 gives a different answer than ranking it against 1976–2026, because "cheap" is always relative to some period.

## Gold

| Indicator | What it measures | Weight |
|---|---|---|
| `real_gold` | Gold ÷ US CPI (inflation-adjusted price) | 25 |
| `gold_sp500` | Gold ÷ S&P 500 | 20 |
| `gold_m2` | Gold ÷ US M2 money supply | 15 |
| `real_yield` | 10-year real Treasury yield, inverted (high real yields count as cheap) | 20 |
| `ma_deviation` | Gold's % distance from its 46-month (≈200-week) average | 20 |

Gold prices start in 1976. The composite starts in 1982, when real-yield data begins.

## Bitcoin

| Indicator | What it measures | Weight |
|---|---|---|
| `mvrv` | Market value ÷ the average price holders paid for their coins | 50 |
| `ma_multiple` | BTC ÷ its 46-month (≈200-week) average | 25 |
| `btc_gold` | BTC/gold ratio ÷ its own 46-month average | 25 |

BTC data starts in July 2010. The composite starts in 2014, because the 46-month averages need about four years of data first.

Why the gold indicators aren't reused: bitcoin went from cents to tens of thousands of dollars, so ratios like BTC ÷ CPI mostly measure that climb. On those ratios the November 2022 low scored about 63, which reads as "expensive". The BTC indicators compare the price to bitcoin's own recent history instead.

`ma_multiple` and `btc_gold` move almost together, so their combined weight equals MVRV's.

## Read this before using it for decisions

- **It describes; it doesn't forecast.** In a check from 1992 to 2026, months with a higher rolling gold score were followed by *higher* 12-month gold returns, not lower. The score has behaved more like momentum than a valuation signal.
- **Past values on the charts use hindsight.** Each past month is ranked against the whole period you pick, including the years after it. The charts show where a month sits in that period, not what the score would have said at the time. Today's score has no hindsight, because no later months exist yet.
- **Bitcoin's history is short.** About three full boom-and-bust cycles fit in 2010–2026.
- **Open question:** whether high real yields should count as cheap or expensive for gold. The gold page shows the score both ways.
- Not financial advice.

## Data sources

No API keys are needed.

| Data | Source |
|---|---|
| Gold, monthly from 1976 | World Bank monthly averages, via the [datasets/gold-prices](https://github.com/datasets/gold-prices) mirror. Yahoo Finance (`GC=F`) fills months not yet published. |
| S&P 500 | Yahoo Finance (`^GSPC`) |
| CPI, M2, real yields | FRED CSV downloads: `CPIAUCSL`, `M2SL`, `DFII10` (10-year TIPS, 2003 onward). For 1982–2002, `GS10` minus `EXPINF10YR`. |
| BTC price, MVRV | [CoinMetrics community API](https://docs.coinmetrics.io/api/v4/) |

The dashboard caches downloads for an hour. The **Refresh data** button fetches them again.

## Run it locally

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/streamlit run app.py
```

Command-line versions:

- `.venv/bin/python gold_indicator.py` prints today's gold score and saves `gold_valuation_dashboard.png` and `gold_valuation_history.csv`. It ranks each month against the 30 years before it, so its history has no hindsight.
- `.venv/bin/python btc_indicator.py` prints today's BTC score, ranked against all of 2010 to today.

Tests use live data, so they need a network connection:

```bash
.venv/bin/python test_app.py
.venv/bin/python test_btc.py
```

## Files

| File | Contents |
|---|---|
| `app.py` | Page switcher: Gold and BTC |
| `gold_page.py`, `btc_page.py` | The two dashboard pages |
| `gold_indicator.py` | Gold data, indicators, the shared scoring functions, and the gold command-line script |
| `btc_indicator.py` | BTC data, indicators, and the BTC command-line script |
| `charts.py` | Shared chart helper |
