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
st.set_page_config(page_title="Multi-Agent Financial Reserach AI", layout="wide")

GROQ_API_KEY = os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY") or st.secrets.get("NEWS_API_KEY")

llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)

# -------------------------
# SESSION STATE (SAFE)
# -------------------------
if "watchlist" not in st.session_state:
    st.session_state.watchlist = []

if "current_symbol" not in st.session_state:
    st.session_state.current_symbol = ""

# -------------------------
# CALLBACK
# -------------------------
def add_to_watchlist():
    symbol = st.session_state.current_symbol
    if symbol and symbol not in st.session_state.watchlist:
        st.session_state.watchlist.append(symbol)

def load_from_watchlist(symbol):
    st.session_state.current_symbol = symbol.replace(".NS", "")
    st.rerun()

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
            "volume": int(data["Volume"].iloc[-1])
        }
    except:
        return None

@st.cache_data(ttl=600)
def get_chart(symbol):
    return yf.Ticker(symbol).history(period="30d")

@st.cache_data(ttl=600)
def get_fundamentals(symbol):
    try:
        ticker = yf.Ticker(symbol)

        # fallback-safe extraction
        info = ticker.info if ticker.info else {}

        pe = info.get("trailingPE") or info.get("forwardPE")
        roe = info.get("returnOnEquity")
        debt = info.get("debtToEquity")
        growth = info.get("earningsGrowth") or info.get("revenueGrowth")

        return {
            "PE": pe if pe else "N/A",
            "ROE": roe if roe else "N/A",
            "Debt": debt if debt else "N/A",
            "Growth": growth if growth else "N/A"
        }

    except:
        return {
            "PE": "N/A",
            "ROE": "N/A",
            "Debt": "N/A",
            "Growth": "N/A"
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
        "SMA": round(data["SMA"].iloc[-1], 2),
        "EMA": round(data["EMA"].iloc[-1], 2),
        "RSI": round(data["RSI"].iloc[-1], 2)
    }
    
@st.cache_data(ttl=600)
def get_news(symbol):
    try:
        query = symbol.replace(".NS", "")
        url = f"https://newsapi.org/v2/everything?q={query}&pageSize=3&apiKey={NEWS_API_KEY}"
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
        return "AI analysis unavailable"

def portfolio_score(symbols):
    score = 0
    total = 0

    for s in symbols:
        if not s.endswith(".NS"):
            s += ".NS"

        tech = get_indicators(s)

        if tech["RSI"] < 70:
            score += 1
        if tech["RSI"] > 30:
            score += 1

        total += 2

    return round((score / total) * 100, 2) if total else 0

def risk_engine(rsi):
    if rsi > 70:
        return "High Risk"
    elif rsi < 30:
        return "Low Risk"
    else:
        return "Moderate Risk"

# -------------------------
# UI INPUT (CONNECTED)
# -------------------------
st.title("Multi-Agent Financial Reserach AI")

symbol_input = st.text_input(
    "Stock (e.g. RELIANCE)",
    value=st.session_state.current_symbol
)

symbol2_input = st.text_input("Compare (optional)")
portfolio_input = st.text_input("Portfolio (comma separated)")

# -------------------------
# ANALYZE FLOW
# -------------------------
if st.button("Analyze") and symbol_input:

    symbol = symbol_input.upper().strip()
    if not symbol.endswith(".NS"):
        symbol += ".NS"

    st.session_state.current_symbol = symbol_input.upper().strip()

    stock = get_stock_data(symbol)
    if not stock:
        st.error("Stock fetch failed")
        st.stop()

    chart = get_chart(symbol)
    fundamentals = get_fundamentals(symbol)
    news = get_news(symbol)

    summary = llm_call(f"Analyze {symbol}. No code.")
    bull = llm_call(f"Bullish case for {symbol}.")
    bear = llm_call(f"Bearish case for {symbol}.")
    judge = llm_call("Give final investment decision.")

    # WATCHLIST BUTTON
    st.button("Add to Watchlist", on_click=add_to_watchlist)

    # -------------------------
    # TABS
    # -------------------------
    tabs = st.tabs([
        "Dashboard","Summary","Debate",
        "Comparison","Portfolio","Indicators",
        "Market","Watchlist","Fundamentals","Sector","Assets"
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
        st.write("News:")
        st.write(news)

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

            d2 = get_chart(s2)

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=chart.index, y=chart["Close"], name=symbol))
            fig.add_trace(go.Scatter(x=d2.index, y=d2["Close"], name=s2))
            st.plotly_chart(fig)

    # Portfolio
    with tabs[4]:
        if portfolio_input:
            symbols = [s.strip().upper() for s in portfolio_input.split(",")]

            score = portfolio_score(symbols)

            st.metric("Portfolio Score", f"{score}/100")

            st.write(llm_call(f"Analyze portfolio {portfolio_input}"))
    # Indicators
    with tabs[5]:
        indicators = get_indicators(symbol)

        st.metric("SMA (14)", indicators["SMA"])
        st.metric("EMA (14)", indicators["EMA"])
        st.metric("RSI", indicators["RSI"])

        if indicators["RSI"] > 70:
            st.warning("Overbought (High Risk)")
        elif indicators["RSI"] < 30:
            st.success("Oversold (Opportunity)")
        else:
            st.info("Neutral Zone")

        risk = risk_engine(indicators["RSI"])

        st.write("### 🚨 Alerts")
        st.write(f"Risk Level: {risk}")

        if indicators["RSI"] > 70:
            st.error("SELL SIGNAL: Overbought")

        elif indicators["RSI"] < 30:
            st.success("BUY SIGNAL: Oversold")

        else:
            st.info("No strong signal") 
    # Market
    with tabs[6]:
        st.subheader("Market Context")

        hour = datetime.now().hour

        if 9 <= hour <= 15:
          st.success("Market Open (NSE)")
        else:
          st.warning("Market Closed")

        st.markdown("---")

        st.write("### 🇮🇳 Indian Market Insights")
        st.write("• NSE & BSE dominate Indian equities")
        st.write("• IT, Banking, FMCG are key sectors")
        st.write("• Influenced by RBI, inflation, global markets")

        st.markdown("---")

        st.write("### Currency")
        st.info("All values shown in INR (₹)")

        st.markdown("---")

    
    
    # -------------------------
    # WATCHLIST (FIXED + CLICKABLE)
    # -------------------------
    with tabs[7]:
        st.subheader("Watchlist")

        if st.session_state.watchlist:
            for s in st.session_state.watchlist:
                col1, col2 = st.columns([3,1])

                # CLICK → LOAD ANALYSIS
                if col1.button(f" {s}", key=f"load_{s}"):
                    load_from_watchlist(s)

                # REMOVE
                if col2.button("❌", key=f"remove_{s}"):
                    st.session_state.watchlist.remove(s)
                    st.rerun()
        else:
            st.info("No stocks in watchlist yet")

    # Fundamentals
    with tabs[8]:
        st.write("### Fundamental Analysis")
        st.write(f"P/E: {fundamentals.get('PE')}")
        st.write(f"ROE: {fundamentals.get('ROE')}")
        st.write(f"Debt/Equity: {fundamentals.get('Debt')}")
        st.write(f"Growth: {fundamentals.get('Growth')}")

    # Sector
    with tabs[9]:
        st.write("### Sector Comparison (IT Sector Example)")

        peers = ["TCS.NS","INFY.NS","WIPRO.NS"]

       
        for p in peers:
            f = get_fundamentals(p)

        st.write(f"*{p}*")
        st.write(f"P/E: {f['PE']}")
        st.write(f"ROE: {f['ROE']}")
        st.write("---")
        
        st.write(f"{p} → PE: {f.get('PE')} | ROE: {f.get('ROE')}")

    with tabs[10]:
      st.subheader("Multi-Asset Analysis")

    # GOLD
      gold = get_stock_data("GC=F")

    # USDINR
      usd = get_stock_data("INR=X")

    # BTC
      btc = get_stock_data("BTC-USD")

      if gold:
         st.metric("Gold", gold["price"])

      if usd:
         st.metric("USD/INR", usd["price"])

      if btc:
         st.metric("Bitcoin", btc["price"])
    
