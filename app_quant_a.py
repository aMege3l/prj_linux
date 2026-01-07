import datetime as dt
import pandas as pd
import streamlit as st
import os

from streamlit_autorefresh import st_autorefresh
st_autorefresh(interval=5 * 60 * 1000, key="refresh")

# Force SSL cert path (Windows + curl issue with accents in user folder)
os.environ["SSL_CERT_FILE"] = r"C:\certs\cacert.pem"
os.environ["REQUESTS_CA_BUNDLE"] = r"C:\certs\cacert.pem"
os.environ["CURL_CA_BUNDLE"] = r"C:\certs\cacert.pem"

from data_loader import fetch_ohlc_yahoo
from strategies import buy_and_hold, moving_average_crossover
from metrics import compute_performance_metrics


# Streamlit page config
st.set_page_config(page_title="Quant A – Single Asset Analysis", layout="wide")

st.title("Quant A – Single Asset Analysis")

st.markdown("""
This dashboard lets you:
- Select a single financial asset
- Download price data (Yahoo Finance)
- Run **two strategies**: Buy & Hold and Moving Average Crossover
- View interactive charts and performance metrics
""")

# --- SIDEBAR ---
st.sidebar.header("Parameters")

symbol = st.sidebar.text_input("Yahoo Ticker", value="AAPL")

today = dt.date.today()
default_start = today - dt.timedelta(days=365)

start_date = st.sidebar.date_input("Start date", value=default_start)
end_date = st.sidebar.date_input("End date", value=today)
today = dt.date.today()
if end_date > today:
    st.sidebar.warning("End date is in the future. Adjusted to today.")
    end_date = today
if start_date >= end_date:
    st.sidebar.error("Start date must be before end date.")
    st.stop()

interval_label = st.sidebar.selectbox(
    "Interval (periodicity)",
    ["1 Day", "1 Week", "1 Month"],
    index=0
)

interval_map = {
    "1 Day": "1d",
    "1 Week": "1wk",
    "1 Month": "1mo"
}

interval = interval_map[interval_label]

strategy_choice = st.sidebar.selectbox(
    "Strategy",
    ["Buy & Hold", "MA Crossover"]
)

short_window = st.sidebar.slider("Short MA window", 5, 50, 20)
long_window = st.sidebar.slider("Long MA window", 20, 200, 50)

initial_capital = st.sidebar.number_input("Initial capital", 100.0, 1_000_000.0, 1000.0)

run = st.sidebar.button("Run Backtest")

# --- MAIN ---
if run:
    try:
        st.info("Fetching data from Yahoo Finance…")
        if interval == "1mo" and (end_date - start_date).days < 90:
            st.warning("Monthly interval needs a longer date range (>= ~3 months).")
            st.stop()

        df = fetch_ohlc_yahoo(
            symbol=symbol,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            interval=interval
        )

        if df.empty:
            st.error("No data found for this asset. Try another ticker.")
            st.stop()

        st.success(f"Downloaded {len(df)} rows of data.")

        # Close prices
        close = df["close"].dropna()
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]
            close = close.dropna()

        if close.empty:
            st.error("Price series is empty after dropping NaNs.")
            st.stop()

        # --- Run selected strategy ---
        if strategy_choice == "Buy & Hold":
            equity = buy_and_hold(close, initial_capital)
            equity = equity.loc[close.index]  # align index
            periods_map = {
                "1d": 252,
                "1wk": 52,
                "1mo": 12,
            }
            periods_per_year = periods_map.get(interval, 252)

            metrics_dict = compute_performance_metrics(
                equity,
                periods_per_year=int(periods_per_year)
            )

            st.subheader("Price + Strategy Performance")
            combined = pd.DataFrame(
                {
                    "Price": close,
                    "Strategy (equity, norm)": equity / equity.iloc[0] * close.iloc[0],
                },
                index=close.index
            )
            st.line_chart(combined)

            st.subheader("Performance Metrics")
            st.json(metrics_dict)

        else:
            equity, details = moving_average_crossover(
                close,
                short_window,
                long_window,
                initial_capital
            )
            equity = equity.loc[close.index]  # align index
            metrics_dict = compute_performance_metrics(equity)

            st.subheader("Price + Strategy Performance")
            combined = pd.DataFrame(
                {
                    "Price": close,
                    "Strategy (equity, norm)": equity / equity.iloc[0] * close.iloc[0],
                },
                index=close.index
            )
            st.line_chart(combined)

            st.subheader("Performance Metrics")
            st.json(metrics_dict)

            with st.expander("Show detailed MA crossover dataframe"):
                st.dataframe(details)

    except Exception as e:
        st.exception(e)

else:
    st.info("Configure parameters in the sidebar and click **Run Backtest**.")
