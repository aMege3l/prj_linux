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
    Parameters
    ----------
    symbol : str
        e.g. 'AAPL', 'MSFT', 'EURUSD=X', 'GC=F', 'BTC-USD'
    start_date : str
        'YYYY-MM-DD'
    end_date : str
        'YYYY-MM-DD'
    interval : str
        '1d','1h','30m','15m','5m','1m'

    Returns
    -------
    pd.DataFrame
        Indexed by time (DatetimeIndex). Columns:
        open, high, low, close, adj_close, volume (when available).
    """
    df = yf.download(
        symbol,
        start=start_date,
        end=end_date,
        interval=interval,
        auto_adjust=False,
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

    df.index.name = "time"
    return df
