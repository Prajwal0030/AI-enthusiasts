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
st.set_page_config(page_title="AI Financial Research", layout="wide")

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
# DATA FUNCTIONS (SAFE)
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
def get_fundamentals(symbol):
    try:
        info = yf.Ticker(symbol).info
        return {
            "pe": info.get("trailingPE"),
            "market_cap": info.get("marketCap"),
            "roe": info.get("returnOnEquity"),
            "sector": info.get("sector")
        }
    except:
        return None

@st.cache_data(ttl=600)
def get_news(symbol):
    if not NEWS_API_KEY:
        return "News unavailable"

    try:
        query = symbol.replace(".NS", "")
        url = f"https://newsapi.org/v2/everything?q={query}&pageSize=3&apiKey={NEWS_API_KEY}"
        res = requests.get(url).json()
        headlines = [a["title"] for a in res.get("articles", [])]
        return "\n".join(headlines[:3])
    except:
        return "Error fetching news"

@st.cache_data(ttl=600)
def get_chart(symbol):
    try:
        return yf.Ticker(symbol).history(period="30d")
    except:
        return None

# -------------------------
# SECTOR MAP
# -------------------------
SECTOR_MAP = {
    "RELIANCE.NS": ["ONGC.NS", "IOC.NS"],
    "TCS.NS": ["INFY.NS", "WIPRO.NS"]
}

# -------------------------
# LLM CALL
# -------------------------
def llm_call(prompt):
    return llm.invoke([HumanMessage(content=prompt)]).content

# -------------------------
# AGENTS
# -------------------------
def summary_agent(symbol, stock, tech, news):
    return llm_call(f"""
    Analyze {symbol}:

    Price: {stock}
    Indicators: {tech}
    News: {news}

    Give structured financial analysis + recommendation.
    """)

def bull_agent(symbol, summary):
    return llm_call(f"Give bullish case for {symbol}: {summary}")

def bear_agent(symbol, summary):
    return llm_call(f"Give bearish case for {symbol}: {summary}")

def judge_agent(bull, bear):
    return llm_call(f"Compare:\nBull: {bull}\nBear: {bear}\nFinal decision:")

def indicator_agent(tech):
    return llm_call(f"""
    Explain indicators:
    SMA {tech['sma']}, EMA {tech['ema']}, RSI {tech['rsi']}
    """)

def fundamental_agent(symbol, fundamentals):
    return llm_call(f"""
    Analyze fundamentals of {symbol}:
    {fundamentals}
    """)

def sector_agent(symbol, peers):
    return llm_call(f"""
    Compare {symbol} with peers:
    {peers}
    """)

def macro_agent():
    return llm_call("Explain Indian market context (RBI, inflation, sentiment)")

def portfolio_agent(data):
    return llm_call(f"Analyze portfolio: {data}")

def recommendation_agent(symbol, summary, tech):
    return llm_call(f"""
    Based on {symbol}:
    {summary}
    RSI: {tech['rsi']}

    Give BUY/HOLD/SELL + confidence.
    """)

def calculate_risk(tech):
    if tech['rsi'] > 70:
        return "High Risk"
    elif tech['rsi'] < 30:
        return "Low Risk"
    return "Moderate Risk"

# -------------------------
# UI
# -------------------------
st.title("AI Financial Research Platform 🇮🇳")

col1, col2 = st.columns(2)
symbol1 = col1.text_input("Stock 1")
symbol2 = col2.text_input("Stock 2 (optional)")
portfolio_input = st.text_input("Portfolio (comma separated)")

if st.button("Analyze") and symbol1:

    symbol1 = symbol1.upper().strip()
    if not symbol1.endswith(".NS"):
        symbol1 += ".NS"

    if symbol2:
        symbol2 = symbol2.upper().strip()
        if not symbol2.endswith(".NS"):
            symbol2 += ".NS"

    stock = get_stock_data(symbol1)
    tech = get_technical_indicators(symbol1)
    news = get_news(symbol1)
    fundamentals = get_fundamentals(symbol1)

    summary = summary_agent(symbol1, stock, tech, news)
    bull = bull_agent(symbol1, summary)
    bear = bear_agent(symbol1, summary)
    verdict = judge_agent(bull, bear)
    recommendation = recommendation_agent(symbol1, summary, tech)
    risk = calculate_risk(tech)

    tabs = st.tabs([
        "Dashboard",
        "AI Summary",
        "Debate",
        "Comparison",
        "Portfolio",
        "Indicators",
        "Fundamentals",
        "Sector",
        "Watchlist",
        "Macro"
    ])

    # Dashboard
    with tabs[0]:
        st.metric("Price", stock["price"])
        st.metric("Volume", stock["volume"])

        chart = get_chart(symbol1)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=chart.index, y=chart["Close"]))
        st.plotly_chart(fig)

    # Summary
    with tabs[1]:
        st.write(summary)
        st.success(recommendation)
        st.write(f"Risk: {risk}")

    # Debate
    with tabs[2]:
        st.write("Bull:", bull)
        st.write("Bear:", bear)
        st.success(verdict)

    # Comparison
    with tabs[3]:
        if symbol2:
            d1 = get_chart(symbol1)
            d2 = get_chart(symbol2)

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=d1.index, y=d1["Close"], name=symbol1))
            fig.add_trace(go.Scatter(x=d2.index, y=d2["Close"], name=symbol2))
            st.plotly_chart(fig)

    # Portfolio
    with tabs[4]:
        if portfolio_input:
            symbols = [s.strip().upper()+".NS" for s in portfolio_input.split(",")]
            pdata = [get_stock_data(s) for s in symbols if get_stock_data(s)]
            st.write(portfolio_agent(pdata))

    # Indicators
    with tabs[5]:
        st.metric("SMA", tech['sma'])
        st.metric("EMA", tech['ema'])
        st.metric("RSI", tech['rsi'])
        st.write(indicator_agent(tech))

    # Fundamentals
    with tabs[6]:
        st.write(fundamental_agent(symbol1, fundamentals))

    # Sector
    with tabs[7]:
        peers = SECTOR_MAP.get(symbol1, [])
        st.write(peers)
        st.write(sector_agent(symbol1, peers))

    # Watchlist
    with tabs[8]:
        if st.button("Add to Watchlist"):
            add_stock(symbol1)
            st.success("Added!")

        watchlist = get_watchlist()

        for s in watchlist:
            col1, col2 = st.columns([3,1])
            col1.write(s)
            if col2.button(f"Remove {s}", key=s):
                delete_stock(s)
                st.rerun()

    # Macro
    with tabs[9]:
        st.write(macro_agent())
