import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import requests
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
import os

# -------------------------
# PAGE CONFIG
# -------------------------
st.set_page_config(page_title="AI Financial Research", layout="wide")

# -------------------------
# API KEYS
# -------------------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY") or st.secrets.get("NEWS_API_KEY")

if not GROQ_API_KEY:
    st.error("Missing GROQ API key")
    st.stop()

# -------------------------
# LLM
# -------------------------
llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0,
    groq_api_key=GROQ_API_KEY
)

# -------------------------
# DATA FUNCTIONS
# -------------------------
@st.cache_data(ttl=600)
def get_stock_data(symbol):
    stock = yf.Ticker(symbol)
    data = stock.history(period="7d")

    if data.empty:
        return None

    return {
        "price": round(data["Close"].iloc[-1], 2),
        "avg": round(data["Close"].mean(), 2),
        "volume": int(data["Volume"].iloc[-1])
    }

@st.cache_data(ttl=600)
def get_technical_indicators(symbol):
    stock = yf.Ticker(symbol)
    data = stock.history(period="1mo")

    if len(data) < 20:
        return None

    # SMA
    data["SMA"] = data["Close"].rolling(14).mean()

    # EMA (NEW)
    data["EMA"] = data["Close"].ewm(span=14).mean()

    # RSI
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

@st.cache_data(ttl=600)
def get_news(symbol):
    if not NEWS_API_KEY:
        return "No news API"

    query = symbol.replace(".NS", "")
    url = f"https://newsapi.org/v2/everything?q={query}&pageSize=3&apiKey={NEWS_API_KEY}"

    try:
        res = requests.get(url).json()
        headlines = [a["title"] for a in res.get("articles", [])]
        return "\n".join(headlines) if headlines else "No news"
    except:
        return "Error fetching news"

@st.cache_data(ttl=600)
def get_chart(symbol):
    return yf.Ticker(symbol).history(period="30d")

# -------------------------
# AGENTS
# -------------------------
def stock_agent(data):
    return llm.invoke([HumanMessage(content=f"Analyze stock price {data}")]).content

def tech_agent(data):
    return llm.invoke([HumanMessage(content=f"Analyze indicators {data}")]).content

def news_agent(data):
    return llm.invoke([HumanMessage(content=f"Analyze sentiment {data}")]).content

def supervisor(symbol, p, t, n):
    return llm.invoke([HumanMessage(content=f"{symbol} analysis:\n{p}\n{t}\n{n}")]).content

# -------------------------
# DEBATE AGENTS
# -------------------------
def bull(symbol, summary):
    return llm.invoke([HumanMessage(content=f"Bull case for {symbol}: {summary}")]).content

def bear(symbol, summary):
    return llm.invoke([HumanMessage(content=f"Bear case for {symbol}: {summary}")]).content

def judge(symbol, b, br):
    return llm.invoke([HumanMessage(content=f"Judge: {b} vs {br}")]).content

# -------------------------
# PORTFOLIO AGENT (NEW)
# -------------------------
def portfolio_agent(symbols, data):
    prompt = f"""
    Analyze this portfolio:
    Stocks: {symbols}
    Data: {data}

    Evaluate diversification, risk, and suggestions.
    """
    return llm.invoke([HumanMessage(content=prompt)]).content

# -------------------------
# ECONOMIC AGENT (NEW)
# -------------------------
def macro_agent():
    prompt = """
    Explain current market conditions including inflation, interest rates,
    and overall market trend in simple terms.
    """
    return llm.invoke([HumanMessage(content=prompt)]).content

# -------------------------
# UI
# -------------------------
st.title("📈 AI Financial Research Platform")

col1, col2 = st.columns(2)
symbol1 = col1.text_input("Stock 1")
symbol2 = col2.text_input("Stock 2")

portfolio_input = st.text_input("Portfolio (comma separated)")

if st.button("Analyze") and symbol1:

    symbol1 += ".NS" if ".NS" not in symbol1 else ""
    symbol2 += ".NS" if symbol2 and ".NS" not in symbol2 else ""

    stock1 = get_stock_data(symbol1)
    tech1 = get_technical_indicators(symbol1)
    news1 = get_news(symbol1)

    p = stock_agent(stock1)
    t = tech_agent(tech1)
    n = news_agent(news1)

    summary = supervisor(symbol1, p, t, n)

    bull_view = bull(symbol1, summary)
    bear_view = bear(symbol1, summary)
    judge_view = judge(symbol1, bull_view, bear_view)

    # TABS
    tabs = st.tabs([
        "Market Dashboard",
        "Summary",
        "Debate",
        "Comparison",
        "Portfolio AI",
        "Advanced Indicators",
        "Economic Context"
    ])

    # -------------------------
    # MARKET DASHBOARD
    # -------------------------
    with tabs[0]:
        st.metric("Price", stock1["price"])
        st.metric("Volume", stock1["volume"])

        data = get_chart(symbol1)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=data.index, y=data["Close"]))
        st.plotly_chart(fig)

    # -------------------------
    # SUMMARY
    # -------------------------
    with tabs[1]:
        st.success(summary)

    # -------------------------
    # DEBATE
    # -------------------------
    with tabs[2]:
        st.write("Bull:", bull_view)
        st.write("Bear:", bear_view)
        st.success(judge_view)

    # -------------------------
    # COMPARISON
    # -------------------------
    with tabs[3]:
        if symbol2:
            data1 = get_chart(symbol1)
            data2 = get_chart(symbol2)

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=data1.index, y=data1["Close"], name=symbol1))
            fig.add_trace(go.Scatter(x=data2.index, y=data2["Close"], name=symbol2))
            st.plotly_chart(fig)

    # -------------------------
    # PORTFOLIO
    # -------------------------
    with tabs[4]:
        if portfolio_input:
            symbols = [s.strip().upper()+".NS" for s in portfolio_input.split(",")]

            portfolio_data = []
            for s in symbols:
                d = get_stock_data(s)
                if d:
                    portfolio_data.append(d)

            st.write(portfolio_agent(symbols, portfolio_data))

    # -------------------------
    # ADVANCED INDICATORS
    # -------------------------
    with tabs[5]:
        st.write("SMA:", tech1["sma"])
        st.write("EMA:", tech1["ema"])
        st.write("RSI:", tech1["rsi"])

    # -------------------------
    # ECONOMIC CONTEXT
    # -------------------------
    with tabs[6]:
        st.write(macro_agent())
