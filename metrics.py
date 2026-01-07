import pandas as pd
import numpy as np


def compute_performance_metrics(equity_curve: pd.Series,
                                risk_free_rate: float = 0.0,
                                periods_per_year: int = 252) -> dict:

    if isinstance(equity_curve, pd.DataFrame):
        equity_curve = equity_curve.iloc[:, 0]
    equity_curve = pd.Series(equity_curve).dropna()

    returns = equity_curve.pct_change().dropna()
    if returns.empty:
        return {}

    total_return = equity_curve.iloc[-1] / equity_curve.iloc[0] - 1
    n = len(returns)
    ann_return = (1 + total_return) ** (periods_per_year / n) - 1

    ann_vol = float(returns.std() * np.sqrt(periods_per_year))
    sharpe = (float(ann_return) - risk_free_rate) / ann_vol if ann_vol != 0 else np.nan

    running_max = equity_curve.cummax()
    drawdown = equity_curve / running_max - 1
    max_dd = float(drawdown.min())

    return {
        "Total return": float(total_return),
        "Annualized return": float(ann_return),
        "Annualized volatility": float(ann_vol),
        "Sharpe ratio": float(sharpe),
        "Max drawdown": float(max_dd),
    }
