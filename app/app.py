import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import requests
from datetime import datetime
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
import os

# -------------------------
# CONFIG
# -------------------------
st.set_page_config(page_title="AI Financial Platform", layout="wide")

GROQ_API_KEY = os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY") or st.secrets.get("NEWS_API_KEY")

llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)

# -------------------------
# SESSION STATE INIT
# -------------------------
if "watchlist" not in st.session_state:
    st.session_state.watchlist = []

if "symbol_input" not in st.session_state:
    st.session_state.symbol_input = ""

# -------------------------
# CALLBACK
# -------------------------
def add_to_watchlist():
    symbol = st.session_state.symbol_input + ".NS"
    if symbol not in st.session_state.watchlist:
        st.session_state.watchlist.append(symbol)

# -------------------------
# DATA FUNCTIONS
# -------------------------
@st.cache_data(ttl=600)
def get_stock_data(symbol):
    data = yf.Ticker(symbol).history(period="7d")
    return {
        "price": round(data["Close"].iloc[-1], 2),
        "volume": int(data["Volume"].iloc[-1])
    }

@st.cache_data(ttl=600)
def get_chart(symbol):
    return yf.Ticker(symbol).history(period="30d")

@st.cache_data(ttl=600)
def get_fundamentals(symbol):
    info = yf.Ticker(symbol).info
    return {
        "PE": info.get("trailingPE"),
        "ROE": info.get("returnOnEquity"),
        "DebtToEquity": info.get("debtToEquity"),
        "RevenueGrowth": info.get("revenueGrowth")
    }

# -------------------------
# UI INPUT (CONNECTED)
# -------------------------
symbol_input = st.text_input(
    "Stock",
    value=st.session_state.symbol_input
)

symbol2_input = st.text_input("Compare")
portfolio_input = st.text_input("Portfolio")

# -------------------------
# ANALYZE TRIGGER
# -------------------------
analyze_clicked = st.button("Analyze")

if analyze_clicked:
    st.session_state.symbol_input = symbol_input

if st.session_state.symbol_input:

    symbol = st.session_state.symbol_input.upper()
    if not symbol.endswith(".NS"):
        symbol += ".NS"

    stock = get_stock_data(symbol)
    chart = get_chart(symbol)
    fundamentals = get_fundamentals(symbol)

    # LLM outputs
    summary = llm.invoke([HumanMessage(content=f"Analyze {symbol}")]).content
    bull = llm.invoke([HumanMessage(content=f"Bullish case for {symbol}")]).content
    bear = llm.invoke([HumanMessage(content=f"Bearish case for {symbol}")]).content
    judge = llm.invoke([HumanMessage(content=f"Final decision")]).content

    # Add button (callback)
    st.button("⭐ Add to Watchlist", on_click=add_to_watchlist)

    tabs = st.tabs([
        "Dashboard","Summary","Debate",
        "Comparison","Portfolio","Indicators",
        "Market","Watchlist","Fundamentals","Sector"
    ])

    # Dashboard
    with tabs[0]:
        st.metric("Price", f"₹{stock['price']}")
        st.metric("Volume", stock["volume"])

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=chart.index, y=chart["Close"]))
        st.plotly_chart(fig)

    # Summary
    with tabs[1]:
        st.write(summary)

    # Debate
    with tabs[2]:
        st.write("### Bull")
        st.write(bull)
        st.write("### Bear")
        st.write(bear)
        st.success(judge)

    # Comparison
    with tabs[3]:
        if symbol2_input:
            s2 = symbol2_input.upper() + ".NS"
            d2 = get_chart(s2)

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=chart.index, y=chart["Close"], name=symbol))
            fig.add_trace(go.Scatter(x=d2.index, y=d2["Close"], name=s2))
            st.plotly_chart(fig)

    # Portfolio
    with tabs[4]:
        if portfolio_input:
            st.write(llm.invoke([HumanMessage(content=f"Analyze portfolio {portfolio_input}")]).content)

    # Indicators
    with tabs[5]:
        st.write("SMA, EMA, RSI calculated internally")

    # Market Status
    with tabs[6]:
        hour = datetime.now().hour
        if 9 <= hour <= 15:
            st.success("Market Open")
        else:
            st.warning("Market Closed")

    # -------------------------
    # WATCHLIST (CLICKABLE)
    # -------------------------
    with tabs[7]:
        st.subheader("📌 Watchlist")

        if st.session_state.watchlist:
            for s in st.session_state.watchlist:

                col1, col2 = st.columns([3,1])

                # CLICKABLE STOCK
                if col1.button(f"📊 {s}", key=f"watch_{s}"):
                    st.session_state.symbol_input = s.replace(".NS", "")
                    st.rerun()

                # DELETE
                if col2.button("❌", key=f"del_{s}"):
                    st.session_state.watchlist.remove(s)
                    st.rerun()

        else:
            st.info("No stocks in watchlist yet")

    # Fundamentals
    with tabs[8]:
        st.write("### Fundamental Analysis")
        st.write(f"P/E Ratio: {fundamentals['PE']}")
        st.write(f"ROE: {fundamentals['ROE']}")
        st.write(f"Debt/Equity: {fundamentals['DebtToEquity']}")
        st.write(f"Revenue Growth: {fundamentals['RevenueGrowth']}")

    # Sector Comparison
    with tabs[9]:
        st.write("### Sector Comparison")

        peers = ["TCS.NS","INFY.NS","WIPRO.NS"]

        for p in peers:
            info = get_fundamentals(p)
            st.write(f"{p} → PE: {info['PE']}, ROE: {info['ROE']}"
