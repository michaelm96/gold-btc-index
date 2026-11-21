import io
import requests
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ==========================================
# CONFIGURATION
# ==========================================

START_DATE = "1976-01-01"  # ~50 years of gold history
LOOKBACK_MONTHS = 360  # 30 years where data exists

WEIGHTS = {
    "real_gold": 25,
    "gold_sp500": 20,
    "gold_m2": 15,
    "real_yield": 20,
    "ma_deviation": 20
}

score_columns = {
    "real_gold": "score_real_gold",
    "gold_sp500": "score_gold_sp500",
    "gold_m2": "score_gold_m2",
    "real_yield": "score_real_yield",
    "ma_deviation": "score_ma"
}

# ==========================================
# DATA SOURCES
# ==========================================

def get_csv_series(url, params=None):
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()

    series = pd.read_csv(
        io.StringIO(response.text),
        index_col=0,
        parse_dates=True
    ).iloc[:, 0]

    # FRED marks missing values with "."
    series = pd.to_numeric(series, errors="coerce").dropna()

    if series.empty:
        raise ValueError(f"No data from {url} {params or ''}")

    return series.loc[START_DATE:]


def get_fred(series_id):
    # shortcut: keyless chart-download CSV, not the official API; switch back to api.stlouisfed.org if FRED changes this URL.
    return get_csv_series("https://fred.stlouisfed.org/graph/fredgraph.csv", {"id": series_id})


def get_long_gold():
    # World Bank Pink Sheet monthly averages (1960+), mirrored by the datasets/gold-prices GitHub repo.
    # shortcut: third-party mirror; if it stops updating, recent months fall back to Yahoo in build_data.
    return get_csv_series("https://raw.githubusercontent.com/datasets/gold-prices/main/data/monthly.csv")


# Daily bars: Yahoo's monthly GC=F bars skip ~15% of months.
def get_market_data(ticker, interval="1d"):
    df = yf.download(
        ticker,
        start=START_DATE,
        interval=interval,
        auto_adjust=True,
        progress=False
    )

    if df.empty:
        raise ValueError(f"No market data for {ticker}")

    if isinstance(df.columns, pd.MultiIndex):
        df = df.xs(
            "Close",
            axis=1,
            level=0
        )
        if isinstance(df, pd.DataFrame):
            df = df.iloc[:, 0]
    else:
        df = df["Close"]

    return df.dropna()


def monthly(series):
    return series.resample("ME").last()


# ==========================================
# HISTORICAL PERCENTILE
# ==========================================

def rolling_percentile(series):
    return series.rolling(
        window=LOOKBACK_MONTHS,
        min_periods=120
    ).apply(
        lambda x: pd.Series(x).rank(pct=True).iloc[-1] * 100,
        raw=False
    )


def percentile_against(series, reference):
    # Share of reference months at or below each value, 0-100.
    ref = np.sort(reference.dropna().to_numpy())
    if len(ref) == 0:
        return pd.Series(np.nan, index=series.index)
    pct = np.searchsorted(ref, series.to_numpy(), side="right") / len(ref) * 100
    return pd.Series(pct, index=series.index).where(series.notna())


def add_scores(data, percentile, columns=score_columns, weights=WEIGHTS, inverted=("real_yield",), name="gold_score"):
    # Higher values mean more expensive. Defaults are gold's indicator set.
    for key, column in columns.items():
        score = percentile(data[key])
        # Low real yields generally favor gold.
        # Therefore invert the yield percentile.
        data[column] = 100 - score if key in inverted else score

    # Require all indicators to be available.
    data[name] = sum(
        data[column] * weights[key] / 100
        for key, column in columns.items()
    )
    return data


def score_against(data, from_year, to_year, **model):
    """Rank every month against all months from from_year to to_year (inclusive)."""
    return add_scores(
        data.copy(),
        lambda series: percentile_against(series, series.loc[str(from_year):str(to_year)]),
        **model
    )


def refuse_gaps(data, spans):
    # Interior gaps would be forward-filled into stale values, so refuse them.
    for column, start in spans:
        span = data[column].loc[start:data[column].last_valid_index()]
        if span.isna().any():
            raise ValueError(f"{column}: {span.isna().sum()} missing months")


# ==========================================
# CLASSIFICATION
# ==========================================

def classify(score):
    if score <= 25:
        return "EXTREMELY CHEAP"
    elif score <= 40:
        return "CHEAP"
    elif score <= 60:
        return "FAIR VALUE"
    elif score <= 75:
        return "EXPENSIVE"
    else:
        return "EXTREMELY EXPENSIVE"


def build_data():
    # ==========================================
    # FETCH DATA
    # ==========================================

    print("Downloading market data...")

    # World Bank monthly averages for history; Yahoo daily closes fill months the World Bank hasn't published yet.
    gold = monthly(get_long_gold()).combine_first(monthly(get_market_data("GC=F")))
    sp500 = get_market_data("^GSPC")

    print("Downloading FRED data...")

    cpi = get_fred("CPIAUCSL")
    m2 = get_fred("M2SL")
    # 10y TIPS yield from 2003; before that, 10y Treasury minus Cleveland Fed 10y expected inflation
    # (starts 1982; corr 0.94 with TIPS over 2003-2026).
    real_yield = monthly(get_fred("DFII10")).combine_first(
        monthly(get_fred("GS10")) - monthly(get_fred("EXPINF10YR"))
    )

    # ==========================================
    # RESAMPLE TO MONTHLY
    # ==========================================

    data = pd.concat({
        "gold": monthly(gold),
        "sp500": monthly(sp500),
        "cpi": monthly(cpi),
        "m2": monthly(m2),
        "real_yield": monthly(real_yield)
    }, axis=1)

    refuse_gaps(data, (("gold", START_DATE), ("sp500", START_DATE), ("real_yield", "1982")))

    # Forward-fill lower-frequency macro data into the latest month.
    # No dropna: each indicator is ranked against its own available history.
    data = data.ffill()

    # ==========================================
    # INDICATOR 1: REAL GOLD PRICE
    # ==========================================

    data["real_gold"] = (
        data["gold"] / data["cpi"] * 100
    )

    # ==========================================
    # INDICATOR 2: GOLD / S&P 500
    # ==========================================

    data["gold_sp500"] = (
        data["gold"] / data["sp500"]
    )

    # ==========================================
    # INDICATOR 3: GOLD / M2
    # ==========================================

    data["gold_m2"] = (
        data["gold"] / data["m2"]
    )

    # ==========================================
    # INDICATOR 4: REAL YIELD
    # ==========================================

    data["real_yield"] = data["real_yield"]

    # ==========================================
    # INDICATOR 5: 200-WEEK (46-MONTH) MA DEVIATION
    # ==========================================

    # 46 months ~ 200 weeks. Monthly so it reaches back before weekly data exists
    # (corr 0.99 with the weekly version over 2004-2026).
    monthly_ma = data["gold"].rolling(
        window=46,
        min_periods=46
    ).mean()

    data["ma_deviation"] = (
        data["gold"] / monthly_ma - 1
    ) * 100

    # Each month ranked against up to the 30 years before it.
    return add_scores(data, rolling_percentile)


if __name__ == "__main__":
    data = build_data()

    latest = data.dropna(subset=["gold_score"]).iloc[-1]

    print("\n========== GOLD VALUATION ==========")
    print(f"Date: {latest.name.date()}")
    print(f"Gold price: ${latest['gold']:,.2f}")
    print(f"Valuation score: {latest['gold_score']:.1f}/100")
    print(f"Classification: {classify(latest['gold_score'])}")

    print("\nIndividual indicators:")

    for key, column in score_columns.items():
        print(
            f"{key:20s}: {latest[column]:.1f}/100"
        )

    # ==========================================
    # PLOT DASHBOARD
    # ==========================================

    fig, axes = plt.subplots(
        3, 1,
        figsize=(15, 12),
        sharex=True
    )

    axes[0].plot(data.index, data["gold"])
    axes[0].set_title("Gold Price (USD/oz)")
    axes[0].set_ylabel("USD")
    axes[0].grid(True)

    axes[1].plot(
        data.index,
        data["gold_score"],
        label="Gold Valuation Score"
    )

    axes[1].axhline(25, linestyle="--")
    axes[1].axhline(50, linestyle=":")
    axes[1].axhline(75, linestyle="--")

    axes[1].set_ylim(0, 100)
    axes[1].set_title("Long-Term Gold Valuation")
    axes[1].set_ylabel("Score")
    axes[1].legend()
    axes[1].grid(True)

    for key, column in score_columns.items():
        axes[2].plot(
            data.index,
            data[column],
            label=key
        )

    axes[2].set_ylim(0, 100)
    axes[2].set_title("Individual Indicator Scores")
    axes[2].legend(ncol=3)
    axes[2].grid(True)

    plt.tight_layout()
    plt.savefig("gold_valuation_dashboard.png", dpi=150)
    plt.show()

    # ==========================================
    # EXPORT DATA
    # ==========================================

    data.to_csv("gold_valuation_history.csv")

    print("\nExported:")
    print("- gold_valuation_dashboard.png")
    print("- gold_valuation_history.csv")
