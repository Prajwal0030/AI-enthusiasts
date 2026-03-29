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
    conn = sqlite3.connect("stocks.db")
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS watchlist (symbol TEXT PRIMARY KEY)")
    conn.commit()
    conn.close()

def add_stock(symbol):
    conn = sqlite3.connect("stocks.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO watchlist VALUES (?)", (symbol,))
    conn.commit()
    conn.close()

def get_watchlist():
    conn = sqlite3.connect("stocks.db")
    c = conn.cursor()
    c.execute("SELECT symbol FROM watchlist")
    data = c.fetchall()
    conn.close()
    return [d[0] for d in data]

def delete_stock(symbol):
    conn = sqlite3.connect("stocks.db")
    c = conn.cursor()
    c.execute("DELETE FROM watchlist WHERE symbol=?", (symbol,))
    conn.commit()
    conn.close()

init_db()

# -------------------------
# SAFE DATA FUNCTIONS
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
# SECTOR DATA
# -------------------------
SECTOR_MAP = {
    "RELIANCE.NS": ["ONGC.NS", "IOC.NS"],
    "TCS.NS": ["INFY.NS", "WIPRO.NS"]
}

def get_sector_peers(symbol):
    return SECTOR_MAP.get(symbol, [])

# -------------------------
# AGENTS
# -------------------------
def llm_call(prompt):
    return llm.invoke([HumanMessage(content=prompt)]).content

def summary_agent(symbol, stock, tech, news):
    return llm_call(f"""
    Analyze {symbol} stock:

    Price: {stock}
    Indicators: {tech}
    News: {news}

    Provide structured financial insight and recommendation.
    """)

def fundamental_agent(symbol, fundamentals):
    return llm_call(f"""
    Analyze fundamentals of {symbol}:

    PE: {fundamentals['pe']}
    Market Cap: {fundamentals['market_cap']}
    ROE: {fundamentals['roe']}
    Sector: {fundamentals['sector']}

    Give investment insight.
    """)

def macro_agent():
    return llm_call("""
    Explain Indian market context:

    - NSE vs BSE
    - RBI impact
    - Inflation
    - Interest rates
    """)

def recommendation_agent(symbol, summary, tech):
    return llm_call(f"""
    Based on {symbol}:

    {summary}

    RSI: {tech['rsi']}

    Give BUY / HOLD / SELL with confidence.
    """)

def portfolio_agent(data):
    return llm_call(f"""
    Analyze portfolio:

    {data}

    Give diversification and risk analysis.
    """)

# -------------------------
# UI
# -------------------------
st.title("AI Financial Research Platform 🇮🇳")

col1, col2 = st.columns(2)

symbol1 = col1.text_input("Stock 1")
symbol2 = col2.text_input("Stock 2 (optional)")
portfolio_input = st.text_input("Portfolio (comma separated)")

if st.button("Analyze") and symbol1:

    symbol1 = symbol1.strip().upper()
    if not symbol1.endswith(".NS"):
        symbol1 += ".NS"

    stock = get_stock_data(symbol1)
    tech = get_technical_indicators(symbol1)
    news = get_news(symbol1)
    fundamentals = get_fundamentals(symbol1)

    summary = summary_agent(symbol1, stock, tech, news)
    recommendation = recommendation_agent(symbol1, summary, tech)

    tabs = st.tabs([
        "Dashboard",
        "AI Summary",
        "Fundamentals",
        "Sector Comparison",
        "Portfolio",
        "Watchlist",
        "Economic Context"
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

    # Fundamentals
    with tabs[2]:
        st.write(fundamental_agent(symbol1, fundamentals))

    # Sector Comparison
    with tabs[3]:
        peers = get_sector_peers(symbol1)
        for p in peers:
            data = get_stock_data(p)
            if data:
                st.write(f"{p}: ₹{data['price']}")

    # Portfolio
    with tabs[4]:
        if portfolio_input:
            symbols = [s.strip().upper()+".NS" for s in portfolio_input.split(",")]
            pdata = [get_stock_data(s) for s in symbols if get_stock_data(s)]
            st.write(portfolio_agent(pdata))

    # Watchlist
    with tabs[5]:
        if st.button("Add to Watchlist"):
            add_stock(symbol1)

        watchlist = get_watchlist()

        for s in watchlist:
            col1, col2 = st.columns([3,1])
            col1.write(s)
            if col2.button(f"Remove {s}"):
                delete_stock(s)

    # Macro
    with tabs[6]:
        st.write(macro_agent())
