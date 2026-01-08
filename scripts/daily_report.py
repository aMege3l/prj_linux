import os
import sys

# Ensure project root is in PYTHONPATH when running via cron or direct call
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import json
import datetime as dt

import numpy as np
import pandas as pd

from data_loader import fetch_ohlc_yahoo


# Configuration
TICKERS = ["AAPL", "MSFT", "GLD"]
INTERVAL = "1d"
LOOKBACK_DAYS = 252  # ~1 year for drawdown calculation

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS_DIR = os.path.join(BASE_DIR, "reports")

os.makedirs(REPORTS_DIR, exist_ok=True)


# Helper functions
def compute_daily_metrics(df: pd.DataFrame) -> dict:
    """
    Compute daily metrics from OHLC data.

    Metrics
    -------
    - open price
    - close price
    - daily volatility (abs return)
    - max drawdown over lookback period
    """
    close = df["close"].dropna()
    open_series = df["open"].dropna()

    if close.empty or open_series.empty:
        return {"error": "Not enough data"}
    
    open_price = float(open_series.iloc[-1].item())
    close_price = float(close.iloc[-1].item())

    returns = close.pct_change().dropna()
    daily_vol = float(abs(returns.iloc[-1].item())) if not returns.empty else 0.0

    running_max = close.cummax()
    drawdown = close / running_max - 1
    max_dd =  float(drawdown.min().item())

    return {
        "open": float(open_price),
        "close": float(close_price),
        "daily_volatility": float(daily_vol),
        "max_drawdown": float(max_dd),
    }


# Main routine
def main() -> None:
    today = dt.date.today()
    start_date = today - dt.timedelta(days=LOOKBACK_DAYS)

    report = {
        "date": today.isoformat(),
        "generated_at": dt.datetime.now(dt.UTC).isoformat(),
        "assets": {},
    }

    for ticker in TICKERS:
        df = fetch_ohlc_yahoo(
            symbol=ticker,
            start_date=start_date.isoformat(),
            end_date=today.isoformat(),
            interval=INTERVAL,
        )

        if df.empty:
            report["assets"][ticker] = {"error": "No data returned"}
            continue

        metrics = compute_daily_metrics(df)
        report["assets"][ticker] = metrics

    # Write report to disk
    filename = f"{today.isoformat()}_report.json"
    path = os.path.join(REPORTS_DIR, filename)

    with open(path, "w") as f:
        json.dump(report, f, indent=4)

    print(f"[OK] Daily report written to {path}")


if __name__ == "__main__":
    main()
