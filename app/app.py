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
st.set_page_config(page_title="AI Financial Research", layout="wide")

GROQ_API_KEY = os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY") or st.secrets.get("NEWS_API_KEY")

if not GROQ_API_KEY:
    st.error("Missing GROQ API key")
    st.stop()

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0
)

# -------------------------
# DATA
# -------------------------
@st.cache_data(ttl=600)
def get_stock(symbol):
    data = yf.Ticker(symbol).history(period="7d")
    return {
        "price": round(data["Close"].iloc[-1], 2),
        "avg": round(data["Close"].mean(), 2),
        "volume": int(data["Volume"].iloc[-1])
    }

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
        "sma": round(data["SMA"].iloc[-1], 2),
        "ema": round(data["EMA"].iloc[-1], 2),
        "rsi": round(data["RSI"].iloc[-1], 2)
    }

@st.cache_data(ttl=600)
def get_news(symbol):
    if not NEWS_API_KEY:
        return "No news"

    query = symbol.replace(".NS", "")
    url = f"https://newsapi.org/v2/everything?q={query}&pageSize=3&apiKey={NEWS_API_KEY}"

    try:
        res = requests.get(url).json()
        headlines = [a["title"] for a in res.get("articles", [])]
        return "\n".join(headlines[:3])
    except:
        return "News unavailable"

@st.cache_data(ttl=600)
def get_chart(symbol):
    return yf.Ticker(symbol).history(period="30d")

# -------------------------
# AGENTS (SHORT OUTPUTS)
# -------------------------
def llm_call(prompt):
    return llm.invoke([HumanMessage(content=prompt)]).content

def summary_agent(symbol, data, tech, news):
    return llm_call(f"""
    Give a short financial summary (max 3 lines):
    Price: {data}
    Indicators: {tech}
    News: {news}
    """)

def bull_agent(symbol, summary):
    return llm_call(f"Give 2-line bullish view for {symbol}: {summary}")

def bear_agent(symbol, summary):
    return llm_call(f"Give 2-line bearish risks for {symbol}: {summary}")

def judge_agent(bull, bear):
    return llm_call(f"Give final verdict in 2 lines:\nBull: {bull}\nBear: {bear}")

def portfolio_agent(data):
    return llm_call(f"Analyze portfolio in 3 lines: {data}")

def macro_agent():
    return llm_call("Give current market outlook in 3 short lines")

# -------------------------
# UI
# -------------------------
st.title("📈 AI Financial Research Platform")

col1, col2 = st.columns(2)
symbol1 = col1.text_input("Stock 1")
symbol2 = col2.text_input("Stock 2 (optional)")
portfolio_input = st.text_input("Portfolio (comma separated)")

if st.button("Analyze") and symbol1:

    symbol1 += ".NS" if ".NS" not in symbol1 else ""
    symbol2 += ".NS" if symbol2 and ".NS" not in symbol2 else ""

    data = get_stock(symbol1)
    tech = get_indicators(symbol1)
    news = get_news(symbol1)

    summary = summary_agent(symbol1, data, tech, news)
    bull = bull_agent(symbol1, summary)
    bear = bear_agent(symbol1, summary)
    verdict = judge_agent(bull, bear)

    tabs = st.tabs([
        "Dashboard",
        "AI Summary",
        "Debate",
        "Comparison",
        "Portfolio",
        "Indicators",
        "Macro"
    ])

    # -------------------------
    # DASHBOARD
    # -------------------------
    with tabs[0]:
        st.metric("Price", data["price"])
        st.metric("Volume", data["volume"])

        chart = get_chart(symbol1)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=chart.index, y=chart["Close"]))
        st.plotly_chart(fig)

    # -------------------------
    # SUMMARY
    # -------------------------
    with tabs[1]:
        st.write(summary)

    # -------------------------
    # DEBATE
    # -------------------------
    with tabs[2]:
        st.write("Bull:", bull)
        st.write("Bear:", bear)
        st.success("Final Verdict: " + verdict)

    # -------------------------
    # COMPARISON
    # -------------------------
    with tabs[3]:
        if symbol2:
            d1 = get_chart(symbol1)
            d2 = get_chart(symbol2)

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=d1.index, y=d1["Close"], name=symbol1))
            fig.add_trace(go.Scatter(x=d2.index, y=d2["Close"], name=symbol2))
            st.plotly_chart(fig)

    # -------------------------
    # PORTFOLIO
    # -------------------------
    with tabs[4]:
        if portfolio_input:
            symbols = [s.strip().upper()+".NS" for s in portfolio_input.split(",")]
            pdata = [get_stock(s) for s in symbols]
            st.write(portfolio_agent(pdata))

    # -------------------------
    # INDICATORS (UPGRADED)
    # -------------------------
    with tabs[5]:
        st.write(f"**SMA ({tech['sma']})** → Trend direction (stable average)")
        st.write(f"**EMA ({tech['ema']})** → Faster reaction to price changes")
        st.write(f"**RSI ({tech['rsi']})** → Momentum (overbought >70, oversold <30)")

    # -------------------------
    # MACRO
    # -------------------------
    with tabs[6]:
        st.write(macro_agent())
