import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import requests
import sqlite3
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
import os

# -------------------------
# CONFIG
# -------------------------
st.set_page_config(page_title="AI Financial Platform", layout="wide")

GROQ_API_KEY = os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY") or st.secrets.get("NEWS_API_KEY")

if not GROQ_API_KEY:
    st.error("Missing GROQ API Key")
    st.stop()

llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)

# -------------------------
# DATABASE (WATCHLIST)
# -------------------------
def init_db():
    conn = sqlite3.connect("watchlist.db")
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS watchlist (symbol TEXT PRIMARY KEY)")
    conn.commit()
    conn.close()

def add_stock(symbol):
    conn = sqlite3.connect("watchlist.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO watchlist VALUES (?)", (symbol,))
    conn.commit()
    conn.close()

def get_watchlist():
    conn = sqlite3.connect("watchlist.db")
    c = conn.cursor()
    c.execute("SELECT symbol FROM watchlist")
    data = c.fetchall()
    conn.close()
    return [d[0] for d in data]

def delete_stock(symbol):
    conn = sqlite3.connect("watchlist.db")
    c = conn.cursor()
    c.execute("DELETE FROM watchlist WHERE symbol=?", (symbol,))
    conn.commit()
    conn.close()

init_db()

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
            "avg": round(data["Close"].mean(), 2),
            "volume": int(data["Volume"].iloc[-1])
        }
    except:
        return None

@st.cache_data(ttl=600)
def get_technical_indicators(symbol):
    try:
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
    except:
        return None

@st.cache_data(ttl=600)
def get_news(symbol):
    try:
        query = symbol.replace(".NS", "")
        url = f"https://newsapi.org/v2/everything?q={query}&pageSize=3&apiKey={NEWS_API_KEY}"
        res = requests.get(url).json()
        return "\n".join([a["title"] for a in res.get("articles", [])[:3]])
    except:
        return "News unavailable"

@st.cache_data(ttl=600)
def get_chart(symbol):
    return yf.Ticker(symbol).history(period="30d")

# -------------------------
# LLM CALL
# -------------------------
def llm_call(prompt):
    return llm.invoke([HumanMessage(content=prompt)]).content

# -------------------------
# AGENTS
# -------------------------
def summary_agent(symbol, stock, tech, news):
    return llm_call(f"Analyze {symbol}. Give trend, position, news impact, recommendation. No code.")

def debate_agents(symbol):
    bull = llm_call(f"Bullish case for {symbol}. No code.")
    bear = llm_call(f"Bearish risks for {symbol}. No code.")
    judge = llm_call(f"Final decision. No code.")
    return bull, bear, judge

def indicator_agent(tech):
    return llm_call(f"Explain SMA, EMA, RSI with insights. No code.")

def portfolio_agent(data):
    return llm_call(f"Analyze portfolio {data}. No code.")

def macro_agent():
    return llm_call("Explain Indian market briefly. No code.")

# -------------------------
# UI
# -------------------------
st.title("📊 AI Financial Intelligence Platform")

symbol_input = st.text_input("Stock (e.g. RELIANCE)")
symbol2_input = st.text_input("Compare (optional)")
portfolio_input = st.text_input("Portfolio (comma separated)")

# Watchlist click handler
if "selected_stock" in st.session_state:
    symbol_input = st.session_state.selected_stock.replace(".NS", "")
    del st.session_state.selected_stock

if st.button("Analyze") and symbol_input:

    symbol = symbol_input.upper().strip()
    if not symbol.endswith(".NS"):
        symbol += ".NS"

    stock = get_stock_data(symbol)

    if stock is None:
        st.error("Stock fetch failed")
        st.stop()

    tech = get_technical_indicators(symbol)
    news = get_news(symbol)

    summary = summary_agent(symbol, stock, tech, news)
    bull, bear, judge = debate_agents(symbol)

    # ⭐ Add Watchlist
    if st.button("⭐ Add to Watchlist"):
        add_stock(symbol)
        st.success(f"{symbol} added")

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
            symbols = [s.strip().upper()+".NS" for s in portfolio_input.split(",")]
            pdata = [get_stock_data(s) for s in symbols if get_stock_data(s)]
            st.write(portfolio_agent(pdata))

    # Indicators
    with tabs[5]:
        if tech:
            st.metric("SMA", tech["sma"])
            st.metric("EMA", tech["ema"])
            st.metric("RSI", tech["rsi"])
            st.write(indicator_agent(tech))

    # Market
    with tabs[6]:
        st.write(macro_agent())

    # Watchlist
    with tabs[7]:
        st.subheader("📌 Watchlist")

        watchlist = get_watchlist()

        if watchlist:
            for s in watchlist:
                col1, col2 = st.columns([3,1])

                if col1.button(f"📊 {s}", key=f"view_{s}"):
                    st.session_state.selected_stock = s
                    st.rerun()

                if col2.button("❌", key=f"del_{s}"):
                    delete_stock(s)
                    st.rerun()
        else:
            st.info("No stocks in watchlist yet")
