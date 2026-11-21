# BTC valuation page

Spec: `docs/superpowers/specs/2026-11-20-btc-valuation-design.md` (approved 2026-11-21)

- [x] 1. `gold_indicator.py`: `add_scores` / `score_against` take `columns`, `weights`, `inverted`, `name`, with gold's values as defaults. Extract the gap check into `refuse_gaps(data, spans)`. Gold output must stay identical: compare against `pre_btc_gold_indicator.py` on all historical rows.
- [x] 2. `btc_indicator.py`:
  - `get_coinmetrics()`: one page; raise if `next_page_url` is present.
  - `build_btc_data()`: btc, mvrv and gold monthly; refuse gaps; ffill; `ma_multiple` and `btc_gold`, each over a 46-month average.
  - `score_btc(data, from_year, to_year)`: weights 50/25/25, composite `btc_score`.
  - CLI: print the latest score against the full history.
- [x] 3. Dashboard:
  - Move `line_chart` and `SCORE_SCALE` to `charts.py`.
  - Move the gold page from `app.py` to `gold_page.py` unchanged.
  - `app.py` becomes the router: `st.navigation` with Gold (default) and BTC.
  - New `btc_page.py` mirrors the gold page.
- [x] 4. Tests:
  - `test_app.py` still passes through the router.
  - New `test_btc.py`: unit percentile check; AppTest for the default range (5 charts), a narrowed range (score changes), 2010–2012 (warning) and Refresh.
- [x] 5. Restart the server and check both pages in the browser.

## Review
- Gold output unchanged: 610 finished months identical (rolling) and 3 fixed ranges identical on the same data, compared against the pre-change module.
- BTC per-indicator scores match the separate design-time calculation (MVRV 18.8, 200-week 4.6, BTC/gold 6.6). Composite 12.2 = 0.5·18.8 + 0.25·4.6 + 0.25·6.6.
- `test_app.py` and `test_btc.py` pass; the BTC AppTest goes through the router.
- Browser: both pages render and the sidebar shows Gold and BTC, with no console errors.
- Not covered: the `next_page_url` guard has no test (one line, raises).
