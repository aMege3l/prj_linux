import pandas as pd
import yfinance as yf


def fetch_ohlc_yahoo(
    symbol: str,
    start_date: str,
    end_date: str,
    interval: str = "1d",
) -> pd.DataFrame:
    """
    Fetch OHLCV data from Yahoo Finance for a single asset.

    symbol      : e.g. 'AAPL', 'MSFT', 'EURUSD=X', 'GC=F', 'BTC-USD'
    start_date  : 'YYYY-MM-DD'
    end_date    : 'YYYY-MM-DD'
    interval    : '1d','1h','30m','15m','5m','1m' (depends on Yahoo limits)
    """

    df = yf.download(
        symbol,
        start=start_date,
        end=end_date,
        interval=interval,
        auto_adjust=False,  # keep raw OHLC
        progress=False,
    )

    if df.empty:
        return df  

    df = df.rename(
        columns={
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Adj Close": "adj_close",
            "Volume": "volume",
        }
    )

    # Ensure we have a DatetimeIndex
    df.index.name = "time"

    return df
