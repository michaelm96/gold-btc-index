import requests
import pandas as pd

from gold_indicator import classify, get_long_gold, get_market_data, monthly, refuse_gaps, score_against

# MVRV and the two trend multiples; the multiples correlate ~0.94, so together they weigh the same as MVRV.
WEIGHTS = {"mvrv": 50, "ma_multiple": 25, "btc_gold": 25}

score_columns = {
    "mvrv": "score_mvrv",
    "ma_multiple": "score_ma",
    "btc_gold": "score_btc_gold"
}


def get_coinmetrics():
    # Free, keyless CoinMetrics community API: daily BTC price and MVRV from July 2010.
    response = requests.get(
        "https://community-api.coinmetrics.io/v4/timeseries/asset-metrics",
        params={"assets": "btc", "metrics": "PriceUSD,CapMVRVCur", "frequency": "1d", "page_size": 10000},
        timeout=60
    )
    response.raise_for_status()
    body = response.json()

    # shortcut: one page holds ~27 years of daily rows; follow next_page_url once this raises.
    if "next_page_url" in body:
        raise ValueError("CoinMetrics returned more than one page")

    df = pd.DataFrame(body["data"])
    if df.empty:
        raise ValueError("No data from CoinMetrics")

    df.index = pd.to_datetime(df.pop("time")).dt.tz_localize(None)
    return df.drop(columns="asset").apply(pd.to_numeric)


def build_btc_data():
    print("Downloading BTC and gold data...")

    cm = get_coinmetrics()
    gold = monthly(get_long_gold()).combine_first(monthly(get_market_data("GC=F")))

    data = pd.concat({
        "btc": monthly(cm["PriceUSD"]),
        "mvrv": monthly(cm["CapMVRVCur"]),
        "gold": gold
    }, axis=1, sort=True).loc[cm.index[0]:]

    start = data.index[0]
    refuse_gaps(data, (("btc", start), ("mvrv", start), ("gold", start)))
    data = data.ffill()

    # Same 46-month (~200-week) average as gold's MA indicator.
    data["ma_multiple"] = data["btc"] / data["btc"].rolling(46, min_periods=46).mean()

    # Raw BTC/gold trends up with adoption, so measure it against its own 46-month average.
    # shortcut: BTC month-end close / gold World Bank monthly average; only matters in volatile months.
    ratio = data["btc"] / data["gold"]
    data["btc_gold"] = ratio / ratio.rolling(46, min_periods=46).mean()

    return data


def score_btc(data, from_year, to_year):
    return score_against(
        data, from_year, to_year,
        columns=score_columns, weights=WEIGHTS, inverted=(), name="btc_score"
    )


if __name__ == "__main__":
    data = build_btc_data()
    first, last = data.index[0].year, data.index[-1].year
    latest = score_btc(data, first, last).iloc[-1]

    print("\n========== BTC VALUATION ==========")
    print(f"Date: {latest.name.date()} (current month is partial)")
    print(f"BTC price: ${latest['btc']:,.0f}")
    print(f"Valuation score vs {first}-{last}: {latest['btc_score']:.1f}/100")
    print(f"Classification: {classify(latest['btc_score'])}")
    print("(Ranked against every month in that range: about 3 past cycles. Cheap vs its own history is not a forecast.)")

    print("\nIndividual indicators:")
    for key, column in score_columns.items():
        print(f"{key:20s}: {latest[column]:.1f}/100  (raw {latest[key]:.2f})")
