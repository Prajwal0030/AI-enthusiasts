import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import requests
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
import os
from datetime import datetime

# -------------------------
# CONFIG
# -------------------------
st.set_page_config(page_title="AI Financial Platform", layout="wide")

GROQ_API_KEY = os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY") or st.secrets.get("NEWS_API_KEY")

llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)

# -------------------------
# SESSION STATE
# -------------------------
if "watchlist" not in st.session_state:
    st.session_state.watchlist = []

if "current_symbol" not in st.session_state:
    st.session_state.current_symbol = ""

# -------------------------
# CALLBACKS
# -------------------------
def add_to_watchlist():
    symbol = st.session_state.current_symbol
    if symbol and symbol not in st.session_state.watchlist:
        st.session_state.watchlist.append(symbol)

def load_from_watchlist(symbol):
    st.session_state.current_symbol = symbol.replace(".NS", "")
    st.rerun()

# -------------------------
# DATA
# -------------------------
@st.cache_data(ttl=600)
def get_chart(symbol):
    data = yf.Ticker(symbol).history(period="30d")
    data["SMA"] = data["Close"].rolling(14).mean()
    data["EMA"] = data["Close"].ewm(span=14).mean()
    return data

@st.cache_data(ttl=600)
def get_indicators(symbol):
    data = yf.Ticker(symbol).history(period="1mo")
    data["SMA"] = data["Close"].rolling(14).mean()
    data["EMA"] = data["Close"].ewm(span=14).mean()

    delta = data["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    rs = gain.rolling(14).mean() / loss.rolling(14).mean()
    data["RSI"] = 100 - (100 / (1 + rs))

    return {
        "SMA": round(data["SMA"].iloc[-1], 2),
        "EMA": round(data["EMA"].iloc[-1], 2),
        "RSI": round(data["RSI"].iloc[-1], 2)
    }

@st.cache_data(ttl=600)
def get_stock(symbol):
    data = yf.Ticker(symbol).history(period="7d")
    if data.empty:
        return None
    return {
        "price": round(data["Close"].iloc[-1], 2),
        "volume": int(data["Volume"].iloc[-1])
    }

@st.cache_data(ttl=600)
def get_news(symbol):
    try:
        url = f"https://newsapi.org/v2/everything?q={symbol.replace('.NS','')}&pageSize=3&apiKey={NEWS_API_KEY}"
        res = requests.get(url).json()
        return [a["title"] for a in res.get("articles", [])[:3]]
    except:
        return []

# -------------------------
# HELPERS
# -------------------------
def llm_call(prompt):
    try:
        return llm.invoke([HumanMessage(content=prompt)]).content
    except:
        return "AI unavailable"

def risk_engine(rsi):
    if rsi > 70: return "High Risk"
    elif rsi < 30: return "Low Risk"
    return "Moderate Risk"

# -------------------------
# UI
# -------------------------
st.title("📊 AI Financial Intelligence Platform")

symbol_input = st.text_input("Stock (e.g. RELIANCE)", value=st.session_state.current_symbol)
compare_input = st.text_input("Compare Stock")
portfolio_input = st.text_input("Portfolio (comma separated)")

# Validation
if not symbol_input:
    st.warning("Please enter a stock symbol")

# -------------------------
# MAIN
# -------------------------
if st.button("Analyze") and symbol_input:

    symbol = symbol_input.upper()
    if not symbol.endswith(".NS"):
        symbol += ".NS"

    st.session_state.current_symbol = symbol_input.upper()

    stock = get_stock(symbol)
    if not stock:
        st.error("Invalid stock symbol")
        st.stop()

    chart = get_chart(symbol)
    indicators = get_indicators(symbol)
    news = get_news(symbol)

    summary = llm_call(f"Analyze {symbol}")
    bull = llm_call(f"Bull case for {symbol}")
    bear = llm_call(f"Bear case for {symbol}")

    st.button("⭐ Add to Watchlist", on_click=add_to_watchlist)

    tabs = st.tabs([
        "Dashboard","Summary","Debate","Comparison",
        "Portfolio","Indicators","Market","Watchlist"
    ])

    # ---------------- DASHBOARD
    with tabs[0]:
        st.metric("Price", f"₹{stock['price']}")
        st.metric("Volume", stock["volume"])

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=chart.index, y=chart["Close"], name="Price"))
        fig.add_trace(go.Scatter(x=chart.index, y=chart["SMA"], name="SMA"))
        fig.add_trace(go.Scatter(x=chart.index, y=chart["EMA"], name="EMA"))
        st.plotly_chart(fig, use_container_width=True)

    # ---------------- SUMMARY + SENTIMENT + EXPORT
    with tabs[1]:
        st.write(summary)

        st.subheader("📰 Sentiment")
        if any("gain" in n.lower() or "rise" in n.lower() for n in news):
            st.success("Bullish Sentiment")
        else:
            st.warning("Neutral / Bearish")

        for n in news:
            st.write("-", n)

        report = f"{summary}\n\nNews:\n" + "\n".join(news)
        st.download_button("Download Report", report)

    # ---------------- DEBATE
    with tabs[2]:
        col1, col2 = st.columns(2)
        col1.success(bull)
        col2.error(bear)

    # ---------------- COMPARISON (FIXED)
    with tabs[3]:
        if compare_input:
            s2 = compare_input.upper()
            if not s2.endswith(".NS"):
                s2 += ".NS"

            chart2 = get_chart(s2)

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=chart.index, y=chart["Close"], name=symbol))
            fig.add_trace(go.Scatter(x=chart2.index, y=chart2["Close"], name=s2))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Enter stock in compare field")

    # ---------------- PORTFOLIO (CARDS)
    with tabs[4]:
        if portfolio_input:
            symbols = [s.strip().upper() for s in portfolio_input.split(",")]
            cols = st.columns(len(symbols))

            for i, s in enumerate(symbols):
                tech = get_indicators(s+".NS")
                risk = risk_engine(tech["RSI"])

                cols[i].metric(s, f"RSI: {tech['RSI']}")
                cols[i].write(f"Risk: {risk}")

    # ---------------- INDICATORS
    with tabs[5]:
        st.metric("SMA", indicators["SMA"])
        st.metric("EMA", indicators["EMA"])
        st.metric("RSI", indicators["RSI"])

        if indicators["RSI"] > 70:
            st.error("SELL SIGNAL")
        elif indicators["RSI"] < 30:
            st.success("BUY SIGNAL")
        else:
            st.info("Neutral")

    # ---------------- MARKET
    with tabs[6]:
        hour = datetime.now().hour
        if 9 <= hour <= 15:
            st.success("Market Open")
        else:
            st.warning("Market Closed")

    # ---------------- WATCHLIST
    with tabs[7]:
        if st.session_state.watchlist:
            for s in st.session_state.watchlist:
                if st.button(s):
                    load_from_watchlist(s)
        else:
            st.info("Empty watchlist")
