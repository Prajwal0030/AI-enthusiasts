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
st.set_page_config(page_title="Multi-Agent Financial Research AI", layout="wide")

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
# DATA FUNCTIONS
# -------------------------
@st.cache_data(ttl=600)
def get_stock_data(symbol):
    try:
        data = yf.Ticker(symbol).history(period="7d")
        if data.empty:
            return None
        return {
            "price": round(data["Close"].iloc[-1], 2),
            "volume": int(data["Volume"].iloc[-1])
        }
    except:
        return None

@st.cache_data(ttl=600)
def get_chart(symbol):
    data = yf.Ticker(symbol).history(period="30d")
    data["SMA"] = data["Close"].rolling(14).mean()
    data["EMA"] = data["Close"].ewm(span=14).mean()
    return data

@st.cache_data(ttl=600)
def get_fundamentals(symbol):
    try:
        info = yf.Ticker(symbol).info or {}
        return {
            "PE": info.get("trailingPE") or "N/A",
            "ROE": info.get("returnOnEquity") or "N/A",
            "Debt": info.get("debtToEquity") or "N/A",
            "Growth": info.get("revenueGrowth") or "N/A"
        }
    except:
        return {"PE":"N/A","ROE":"N/A","Debt":"N/A","Growth":"N/A"}

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
def get_news(symbol):
    try:
        url = f"https://newsapi.org/v2/everything?q={symbol.replace('.NS','')}&pageSize=3&apiKey={NEWS_API_KEY}"
        res = requests.get(url).json()
        return "\n".join([a["title"] for a in res.get("articles", [])[:3]])
    except:
        return "No news"

# -------------------------
# LLM
# -------------------------
def llm_call(prompt):
    try:
        return llm.invoke([HumanMessage(content=prompt)]).content
    except:
        return "AI unavailable"

# -------------------------
# HELPERS
# -------------------------
def portfolio_score(symbols):
    score, total = 0, 0
    for s in symbols:
        tech = get_indicators(s+".NS")
        if tech["RSI"] < 70: score += 1
        if tech["RSI"] > 30: score += 1
        total += 2
    return round((score/total)*100,2) if total else 0

def risk_engine(rsi):
    if rsi > 70: return "High Risk"
    elif rsi < 30: return "Low Risk"
    return "Moderate Risk"

# -------------------------
# UI
# -------------------------
st.title("📊 AI Financial Intelligence Platform")

symbol_input = st.text_input("Stock (e.g. RELIANCE)", value=st.session_state.current_symbol)
symbol2_input = st.text_input("Compare (optional)")
portfolio_input = st.text_input("Portfolio (comma separated)")

# Validation
if not symbol_input:
    st.warning("Enter a stock symbol")

# -------------------------
# MAIN
# -------------------------
if st.button("Analyze") and symbol_input:

    symbol = symbol_input.upper()
    if not symbol.endswith(".NS"):
        symbol += ".NS"

    st.session_state.current_symbol = symbol_input.upper()

    stock = get_stock_data(symbol)
    if not stock:
        st.error("Invalid stock")
        st.stop()

    chart = get_chart(symbol)
    indicators = get_indicators(symbol)
    fundamentals = get_fundamentals(symbol)
    news = get_news(symbol)

    summary = llm_call(f"Analyze {symbol}")
    bull = llm_call(f"Bullish case for {symbol}")
    bear = llm_call(f"Bearish case for {symbol}")
    judge = llm_call("Final decision")

    st.button("⭐ Add to Watchlist", on_click=add_to_watchlist)

    tabs = st.tabs([
        "Dashboard","Summary","Debate","Comparison",
        "Portfolio","Indicators","Market","Watchlist",
        "Fundamentals","Sector","Assets"
    ])

    # DASHBOARD
    with tabs[0]:
        col1, col2 = st.columns(2)
        col1.metric("Price", f"₹{stock['price']}")
        col2.metric("Volume", stock["volume"])

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=chart.index, y=chart["Close"], name="Price"))
        fig.add_trace(go.Scatter(x=chart.index, y=chart["SMA"], name="SMA"))
        fig.add_trace(go.Scatter(x=chart.index, y=chart["EMA"], name="EMA"))
        st.plotly_chart(fig, use_container_width=True)

    # SUMMARY
    with tabs[1]:
        st.subheader("AI Summary")
        st.write(summary)

        st.subheader("News Sentiment")
        if "rise" in news.lower():
            st.success("Bullish News")
        else:
            st.warning("Neutral/Bearish News")
        st.write(news)

        st.download_button("Download Report", summary)

    # DEBATE
    with tabs[2]:
        col1, col2 = st.columns(2)
        col1.success(bull)
        col2.error(bear)
        st.info(judge)

    # PORTFOLIO (CARDS)
    with tabs[4]:
        if portfolio_input:
            symbols = [s.strip().upper() for s in portfolio_input.split(",")]
            score = portfolio_score(symbols)

            st.metric("Portfolio Score", f"{score}/100")

            cols = st.columns(len(symbols))
            for i, s in enumerate(symbols):
                tech = get_indicators(s+".NS")
                cols[i].metric(s, f"RSI: {tech['RSI']}")

    # INDICATORS
    with tabs[5]:
        st.metric("SMA", indicators["SMA"])
        st.metric("EMA", indicators["EMA"])
        st.metric("RSI", indicators["RSI"])

        risk = risk_engine(indicators["RSI"])
        st.write(f"Risk: {risk}")

    # MARKET
    with tabs[6]:
        hour = datetime.now().hour
        if 9 <= hour <= 15:
            st.success("Market Open")
        else:
            st.warning("Market Closed - Data may be delayed")

    # WATCHLIST
    with tabs[7]:
        for s in st.session_state.watchlist:
            if st.button(s):
                load_from_watchlist(s)

    # FUNDAMENTALS
    with tabs[8]:
        st.write(f"P/E: {fundamentals['PE']}")
        st.write(f"ROE: {fundamentals['ROE']}")
        st.write(f"Debt: {fundamentals['Debt']}")

    # SECTOR (FIXED)
    with tabs[9]:
        peers = ["TCS.NS","INFY.NS","WIPRO.NS"]
        for p in peers:
            f = get_fundamentals(p)
            st.write(f"{p} → PE: {f['PE']} | ROE: {f['ROE']}")

    # ASSETS
    with tabs[10]:
        st.metric("Gold", get_stock_data("GC=F")["price"])
        st.metric("USD/INR", get_stock_data("INR=X")["price"])
        st.metric("BTC", get_stock_data("BTC-USD")["price"])
