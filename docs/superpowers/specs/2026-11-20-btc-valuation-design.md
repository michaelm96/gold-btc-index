# BTC valuation score — short design

## Intent
Same job as the gold score: one 0–100 "how cheap or expensive is BTC" number with the same labels, the same year-range slider and the same charts, so BTC can be read next to gold.

## Approaches (user picked C)
- A. Copy the five gold indicators with BTC in place of gold. Rejected: BTC/CPI, BTC/S&P and BTC/M2 score the Nov 2022 low at 62–64, so they measure how close BTC is to its all-time high.
- B. BTC-specific: MVRV + 200-week moving-average multiple.
- **C. B plus BTC/gold. Chosen.**

## Indicators (all monthly, last value of the month)
| Indicator | Definition | Weight |
|---|---|---|
| `mvrv` | CoinMetrics CapMVRVCur: market value ÷ the average price holders paid | 50 |
| `ma_multiple` | BTC ÷ its 46-month (≈200-week) average, the same calculation as gold's | 25 |
| `btc_gold` | (BTC ÷ gold) ÷ its own 46-month average | 25 |

**Assistant's call: BTC/gold is trend-adjusted.** The raw ratio has the same long-climb problem. It scores the 2022 low at 63.5 and the Dec 2017 top at 65. Divided by its own 46-month average, it scores the lows at 4–26 and the tops at 85–100.

**Assistant's call: the weights.** `ma_multiple` and `btc_gold` move together: their scores correlate at 0.94, so together they are close to one signal. Giving them 25 each means that signal and MVRV count equally. Equal thirds would count it twice.

## Scoring
- Each month is ranked against every month in the chosen year range, as on the gold dashboard. It reuses `percentile_against` and `score_against`. Labels and thresholds are the same as gold's.
- The composite starts in Apr 2014, because the 46-month averages need data from July 2010 onward. MVRV alone goes back to 2010.
- **No rolling score for BTC.** Gold's 30-year rolling window needs 10 years of history before it starts, so it would only begin around 2024. The CLI prints the latest score ranked against the full history, and says so.

## Sanity check, not evidence
The check ranks each month against the full period, which includes later months, and covers only 3 lows.

| Month | Score (equal thirds) |
|---|---|
| Low, Jan 2015 | 13 |
| Low, Dec 2018 | 16.5 |
| Low, Nov 2022 | 4 |
| Top, Dec 2017 | 96 |
| Top, Mar 2021 | 95 |
| Top, Nov 2021 | 83 |
| Top, Mar 2024 | 70.5 |
| Now (Nov 2026) | 10 |

## Build
- **Data:**
  - CoinMetrics community API: keyless, daily PriceUSD and CapMVRVCur from July 2010, one request with `page_size=10000`. Raise an error if the response asks for another page.
  - Gold: `get_long_gold()` plus the Yahoo GC=F fallback. Not `build_data()`, because BTC needs no FRED or S&P data.
  - Refuse interior gaps, as for gold.
  - shortcut: BTC/gold divides BTC's month-end price by gold's World Bank *monthly average*. This only matters in volatile months.
- **Code:**
  - `add_scores` and `score_against` take the columns, weights and inverted columns as arguments, with gold's values as defaults. Gold's output must stay identical: rerun the 610-row regression.
  - A new `btc_indicator.py` holds `build_btc_data()` and a print-only CLI.
- **Dashboard:**
  - A second Streamlit page for BTC with the same slider, metrics, composite, price chart, three indicator charts and data table. It shares the chart helper.
  - The gold page is unchanged.
- **Tests:** add a BTC AppTest (default range, a narrowed range, Refresh) and a unit check of one BTC percentile.

## Non-goals
- No rolling or backtestable BTC history.
- No PNG export.
- No change to the gold indicators or the open real-yield question.
- No commit unless asked.
