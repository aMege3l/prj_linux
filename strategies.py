import pandas as pd
import numpy as np


def buy_and_hold(prices: pd.Series, initial_capital: float = 1000.0) -> pd.Series:
    """
    Simple Buy & Hold strategy:
    Invest 100% at t0 and hold through the entire period.
    Returns an equity curve (portfolio value over time).
    """
    returns = prices.pct_change().fillna(0.0)
    equity = (1 + returns).cumprod() * initial_capital
    equity.name = "Buy & Hold"
    return equity


def moving_average_crossover(prices: pd.Series, short_window: int = 20, long_window: int = 50,
                             initial_capital: float = 1000.0):

    if isinstance(prices, pd.DataFrame):
        prices = prices.iloc[:, 0]
    prices = pd.Series(prices).dropna()
    df = pd.DataFrame({"price": prices})
    df["ma_short"] = df["price"].rolling(short_window).mean()
    df["ma_long"] = df["price"].rolling(long_window).mean()

    # trading signal: 1 long, -1 short, 0 flat
    df["signal"] = 0
    df.loc[df["ma_short"] > df["ma_long"], "signal"] = 1
    df.loc[df["ma_short"] < df["ma_long"], "signal"] = -1

    # use yesterday's signal
    df["position"] = df["signal"].shift(1).fillna(0)

    # returns of the asset
    df["returns"] = df["price"].pct_change().fillna(0.0)

    # strategy returns
    df["strategy_returns"] = df["position"] * df["returns"]

    # equity curve
    equity_curve = (1 + df["strategy_returns"]).cumprod() * initial_capital
    equity_curve.name = "MA Crossover"

    return equity_curve, df
