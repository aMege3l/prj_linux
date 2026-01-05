import datetime as dt
import pandas as pd
import streamlit as st

from data_loader import fetch_ohlc_yahoo
from strategies_portfolio import (
    build_price_panel,
    parse_weights,
    simulate_portfolio_rebalanced,
)
from metrics_portfolio import (
    compute_portfolio_metrics,
    correlation_matrix,
)
from streamlit_autorefresh import st_autorefresh

@st.cache_data(ttl=300)
def load_prices(
    tickers,
    start_date,
    end_date,
    interval,
):
    """
    Load and cache multi-asset price data for 5 minutes to avoid
    unnecessary API calls during auto-refresh.
    """
    return build_price_panel(
        tickers=tickers,
        start_date=start_date,
        end_date=end_date,
        interval=interval,
        fetcher=fetch_ohlc_yahoo,
    )

st.set_page_config(page_title="Quant B – Multi-Asset Portfolio", layout="wide")
st_autorefresh(interval=5 * 60 * 1000, key="auto_refresh")
st.title("Quant B – Multi-Asset Portfolio")

st.markdown("""
This dashboard lets you:
- Select **3+ assets**
- Download price data (Yahoo Finance)
- Build a portfolio (Equal Weight or Custom Weights)
- Apply **rebalancing** (None/Daily/Weekly/Monthly)
- View charts and portfolio performance metrics
""")

# --- SIDEBAR ---
st.sidebar.header("Parameters")

tickers_raw = st.sidebar.text_input(
    "Yahoo Tickers (comma-separated)",
    value="AAPL,MSFT,GLD",
)

today = dt.date.today()
default_start = today - dt.timedelta(days=365)

start_date = st.sidebar.date_input("Start date", value=default_start)
end_date = st.sidebar.date_input("End date", value=today)

interval = st.sidebar.selectbox(
    "Interval (periodicity)",
    ["1d", "1h", "30m", "15m", "5m", "1m"],
    index=0
)

weights_mode = st.sidebar.selectbox("Weights mode", ["Equal weight", "Custom weights"])

weights_raw = st.sidebar.text_input(
    "Custom weights (if selected)",
    value="AAPL:0.4,MSFT:0.4,GLD:0.2",
    help="Format: TICKER:weight, e.g., AAPL:0.4,MSFT:0.4,GLD:0.2"
)

rebalance = st.sidebar.selectbox(
    "Rebalancing frequency",
    ["None", "Daily", "Weekly", "Monthly"],
    index=2
)

initial_capital = st.sidebar.number_input("Initial capital", 100.0, 1_000_000.0, 10000.0)

if "run_backtest" not in st.session_state:
    st.session_state.run_backtest = False

if st.sidebar.button("Run Portfolio Backtest"):
    st.session_state.run_backtest = True

run = st.session_state.run_backtest



def _clean_tickers(s: str) -> list[str]:
    tickers = [t.strip() for t in s.split(",") if t.strip()]
    # remove duplicates while preserving order
    seen = set()
    out = []
    for t in tickers:
        if t not in seen:
            out.append(t)
            seen.add(t)
    return out


# --- MAIN ---
if run:
    try:
        tickers = _clean_tickers(tickers_raw)

        if len(tickers) < 3:
            st.error("Quant B requires at least 3 assets. Please provide 3+ tickers.")
            st.stop()

        st.info("Fetching data from Yahoo Finance…")

        prices = load_prices(
            tickers=tickers,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            interval=interval,
        )

        if prices.empty:
            st.error("No data found or not enough common timestamps across assets.")
            st.stop()

        st.success(f"Downloaded aligned close prices: {prices.shape[0]} rows × {prices.shape[1]} assets.")

        # weights
        if weights_mode == "Equal weight":
            weights = {t: 1.0 / len(tickers) for t in tickers}
        else:
            weights = parse_weights(weights_raw, tickers)

        equity, details = simulate_portfolio_rebalanced(
            prices=prices,
            weights=weights,
            initial_capital=initial_capital,
            rebalance=rebalance,
        )

        metrics = compute_portfolio_metrics(equity)

        # --- Current values (Condition 3) ---
        st.subheader("Current Values")

        cols = st.columns(len(prices.columns) + 1)

        # Portfolio
        cols[0].metric(
            label="Portfolio Value",
            value=f"{equity.iloc[-1]:,.2f}",
        )

        # Assets (latest close) + change if available
        for i, t in enumerate(prices.columns, start=1):
            last_price = float(prices[t].iloc[-1])
            if len(prices) >= 2:
                prev_price = float(prices[t].iloc[-2])
                delta = last_price - prev_price
                delta_pct = (delta / prev_price) if prev_price != 0 else 0.0
                cols[i].metric(
                    label=f"{t} Last Price",
                    value=f"{last_price:,.2f}",
                    delta=f"{delta:,.2f} ({delta_pct:.2%})",
                )
            else:
                cols[i].metric(
                    label=f"{t} Last Price",
                    value=f"{last_price:,.2f}",
                )


        # --- CHART: assets + portfolio equity (normalized) ---
        st.subheader("Assets vs Portfolio (normalized)")
        norm_assets = prices / prices.iloc[0]
        norm_equity = equity / equity.iloc[0]

        combined = norm_assets.copy()
        combined["PORTFOLIO"] = norm_equity
        st.line_chart(combined)

        # --- Correlation matrix ---
        st.subheader("Correlation Matrix (returns)")
        corr = correlation_matrix(prices)
        if corr.empty:
            st.warning("Not enough data to compute correlation matrix.")
        else:
            st.dataframe(corr.style.format("{:.2f}"))

        # --- Metrics ---
        st.subheader("Portfolio Performance Metrics")
        st.json(metrics)

        # --- Details ---
        with st.expander("Show portfolio details (prices, weights, values, returns)"):
            st.dataframe(details)

    except Exception as e:
        st.exception(e)

else:
    st.info("Configure parameters in the sidebar and click **Run Portfolio Backtest**.")
