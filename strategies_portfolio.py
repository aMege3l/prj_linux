from __future__ import annotations

from typing import Callable, Dict, Tuple

import numpy as np
import pandas as pd


def build_price_panel(
    tickers: list[str],
    start_date: str,
    end_date: str,
    interval: str,
    fetcher: Callable[..., pd.DataFrame],
):
    """
    Download and align close prices for multiple assets.

    Parameters
    ----------
    tickers : list[str]
        List of Yahoo tickers.
    start_date, end_date : str
        'YYYY-MM-DD'
    interval : str
        Yahoo interval.
    fetcher : callable
        Function like fetch_ohlc_yahoo(symbol, start_date, end_date, interval) -> DataFrame.

    Returns
    -------
    pd.DataFrame
        DataFrame of aligned close prices.
        Rows: timestamps, Columns: tickers.
        NaNs are removed by requiring common timestamps across all assets.
    """
    series_list: list[pd.Series] = []

    for t in tickers:
        df = fetcher(symbol=t, start_date=start_date, end_date=end_date, interval=interval)
        if df is None or df.empty or "close" not in df.columns:
            continue

        s = df["close"].dropna()
        if isinstance(s, pd.DataFrame):
            s = s.iloc[:, 0]
        s = pd.Series(s).dropna()

        if not s.empty:
            s.name = t
            series_list.append(s)

    if not series_list:
        return pd.DataFrame()

    prices = pd.concat(series_list, axis=1).sort_index()
    # Intraday timestamps are not perfectly aligned across assets
    if interval != "1d":
        prices = prices.ffill()

    prices = prices.dropna(how="any")  # common intersection
    return prices


def parse_weights(
    weights_raw: str,
    tickers: list[str],
    long_only: bool = True,
):
    """
    Parse custom weights from a string like: "AAPL:0.4,MSFT:0.4,GLD:0.2".

    Notes
    -----
    - Missing tickers default to 0.
    - If weights do not sum to 1, they are normalized.
    - By default, negative weights are rejected (long-only).

    Returns
    -------
    dict[str, float]
        Normalized weights for the provided tickers.
    """
    w: Dict[str, float] = {t: 0.0 for t in tickers}

    if weights_raw.strip():
        parts = [p.strip() for p in weights_raw.split(",") if p.strip()]
        for p in parts:
            if ":" not in p:
                continue
            k, v = p.split(":", 1)
            k = k.strip()
            v = v.strip()
            if k in w:
                w[k] = float(v)

    if long_only and any(val < 0 for val in w.values()):
        raise ValueError("Negative weights detected. This portfolio is long-only by default.")

    s = float(sum(w.values()))
    if s <= 0:
        raise ValueError("Weights sum to 0. Provide valid weights (positive numbers).")

    return {k: v / s for k, v in w.items()}


def _rebalance_dates(index: pd.DatetimeIndex, rebalance: str):
    """
    Internal helper: compute rebalancing timestamps from index.
    """
    if rebalance == "None":
        return pd.DatetimeIndex([index[0]])
    if rebalance == "Daily":
        return index
    if rebalance == "Weekly":
        # Mondays in the available index
        return index[index.to_series().dt.weekday == 0]
    if rebalance == "Monthly":
        s = index.to_series()
        first = s.groupby([s.dt.year, s.dt.month]).head(1).index
    	return index[index.isin(first)]
    raise ValueError(f"Unknown rebalance frequency: {rebalance}")


def simulate_portfolio_rebalanced(
    prices: pd.DataFrame,
    weights: Dict[str, float],
    initial_capital: float = 10_000.0,
    rebalance: str = "Weekly",
):
    """
    Long-only multi-asset portfolio simulation with optional rebalancing.

    Assumptions
    -----------
    - No transaction costs, no slippage.
    - Fully invested (weights sum to 1).
    - Rebalancing sets holdings to target weights at the close of rebalance timestamp.

    Parameters
    ----------
    prices : pd.DataFrame
        Close prices aligned across assets. Columns = tickers.
    weights : dict[str, float]
        Target weights.
    initial_capital : float
        Starting portfolio value.
    rebalance : str
        'None', 'Daily', 'Weekly', 'Monthly'

    Returns
    -------
    (equity, details) : (pd.Series, pd.DataFrame)
        equity: portfolio value over time.
        details: includes prices, realized weights, per-asset values, and portfolio returns.
    """
    if prices is None or prices.empty:
        return pd.Series(dtype=float), pd.DataFrame()

    prices = prices.copy().dropna(how="any").sort_index()
    tickers = list(prices.columns)

    # Normalize provided weights to the available tickers
    w = {t: float(weights.get(t, 0.0)) for t in tickers}
    s = float(sum(w.values()))
    if s <= 0:
        raise ValueError("Provided weights sum to 0 for the available tickers.")
    w = {k: v / s for k, v in w.items()}

    rebal = set(_rebalance_dates(prices.index, rebalance))

    shares = pd.Series(0.0, index=tickers)
    current_value = float(initial_capital)

    equity_list: list[float] = []
    weights_list: list[pd.Series] = []
    values_list: list[pd.Series] = []

    for i, ts in enumerate(prices.index):
        px = prices.loc[ts]

        # Rebalance on first timestamp and whenever scheduled
        if i == 0 or ts in rebal:
            target_values = pd.Series({t: current_value * w[t] for t in tickers})
            shares = target_values / px

        values = shares * px
        current_value = float(values.sum())

        realized_w = (values / values.sum()).replace([np.inf, -np.inf], np.nan).fillna(0.0)

        equity_list.append(current_value)
        weights_list.append(realized_w)
        values_list.append(values)

    equity = pd.Series(equity_list, index=prices.index, name="Portfolio Equity")

    weights_df = pd.DataFrame(weights_list, index=prices.index)
    weights_df.columns = [f"w_{c}" for c in weights_df.columns]

    values_df = pd.DataFrame(values_list, index=prices.index)
    values_df.columns = [f"val_{c}" for c in values_df.columns]

    details = pd.concat([prices, weights_df, values_df], axis=1)
    details["portfolio_return"] = equity.pct_change().fillna(0.0)

    return equity, details
