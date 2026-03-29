import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import requests
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
# STEP 2: SESSION INIT (TOP)
# -------------------------
if "watchlist" not in st.session_state:
    st.session_state.watchlist = []

if "current_symbol" not in st.session_state:
    st.session_state.current_symbol = None

# -------------------------
# STEP 1: CALLBACK FUNCTION
# -------------------------
def handle_add_watchlist():
    if st.session_state.current_symbol:
        symbol = st.session_state.current_symbol
        if symbol not in st.session_state.watchlist:
            st.session_state.watchlist.append(symbol)

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
    return yf.Ticker(symbol).history(period="30d")

@st.cache_data(ttl=600)
def get_news(symbol):
    try:
        query = symbol.replace(".NS", "")
        url = f"https://newsapi.org/v2/everything?q={query}&pageSize=3&apiKey={NEWS_API_KEY}"
        res = requests.get(url).json()
        return "\n".join([a["title"] for a in res.get("articles", [])[:3]])
    except:
        return "No news"

@st.cache_data(ttl=600)
def get_technical_indicators(symbol):
    data = yf.Ticker(symbol).history(period="1mo")
    data["SMA"] = data["Close"].rolling(14).mean()
    data["EMA"] = data["Close"].ewm(span=14).mean()

    delta = data["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    rs = gain.rolling(14).mean() / loss.rolling(14).mean()
    data["RSI"] = 100 - (100 / (1 + rs))

    return {
        "sma": round(data["SMA"].iloc[-1], 2),
        "ema": round(data["EMA"].iloc[-1], 2),
        "rsi": round(data["RSI"].iloc[-1], 2)
    }

# -------------------------
# LLM
# -------------------------
def llm_call(prompt):
    return llm.invoke([HumanMessage(content=prompt)]).content

# -------------------------
# UI
# -------------------------
st.title("📊 AI Financial Intelligence Platform")

symbol_input = st.text_input("Stock (e.g. RELIANCE)")
symbol2_input = st.text_input("Compare (optional)")
portfolio_input = st.text_input("Portfolio (comma separated)")

# -------------------------
# MAIN FLOW
# -------------------------
if st.button("Analyze") and symbol_input:

    symbol = symbol_input.upper().strip()
    if not symbol.endswith(".NS"):
        symbol += ".NS"

    # -------------------------
    # STEP 3: STORE SYMBOL
    # -------------------------
    st.session_state.current_symbol = symbol

    stock = get_stock_data(symbol)
    if not stock:
        st.error("Stock fetch failed")
        st.stop()

    tech = get_technical_indicators(symbol)
    news = get_news(symbol)

    summary = llm_call(f"Analyze {symbol}. No code.")
    bull = llm_call(f"Bullish case for {symbol}.")
    bear = llm_call(f"Bearish case for {symbol}.")
    judge = llm_call("Final decision.")

    # -------------------------
    # STEP 4: FIX BUTTON (CALLBACK)
    # -------------------------
    st.button("⭐ Add to Watchlist", on_click=handle_add_watchlist)

    tabs = st.tabs([
        "Dashboard",
        "Summary",
        "Debate",
        "Comparison",
        "Portfolio",
        "Indicators",
        "Market",
        "Watchlist"
    ])

    # Dashboard
    with tabs[0]:
        st.metric("Price", stock["price"])
        st.metric("Volume", stock["volume"])
        chart = get_chart(symbol)
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
            s2 = symbol2_input.upper().strip()
            if not s2.endswith(".NS"):
                s2 += ".NS"
            d1 = get_chart(symbol)
            d2 = get_chart(s2)
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=d1.index, y=d1["Close"], name=symbol))
            fig.add_trace(go.Scatter(x=d2.index, y=d2["Close"], name=s2))
            st.plotly_chart(fig)

    # Portfolio
    with tabs[4]:
        if portfolio_input:
            st.write(llm_call(f"Analyze portfolio {portfolio_input}"))

    # Indicators
    with tabs[5]:
        st.write(tech)

    # Market
    with tabs[6]:
        st.write(llm_call("Explain Indian market briefly"))

    # -------------------------
    # STEP 5: WATCHLIST TAB
    # -------------------------
    with tabs[7]:
        st.subheader("📌 Watchlist")

        watchlist = st.session_state.watchlist

        

        if watchlist:
            for s in watchlist:
                st.write(f"📊 {s}")
        else:
            st.info("No stocks in watchlist yet")
