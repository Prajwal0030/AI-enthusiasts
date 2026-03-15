import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import requests
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
import os

# -------------------------
# API KEYS
# -------------------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY") or st.secrets.get("NEWS_API_KEY")

if not GROQ_API_KEY:
    st.error("GROQ_API_KEY not found")
    st.stop()

# -------------------------
# LLM SETUP
# -------------------------
llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0,
    groq_api_key=GROQ_API_KEY,
)

# -------------------------
# DATA FUNCTIONS
# -------------------------
def get_stock_data(symbol):

    stock = yf.Ticker(symbol)
    data = stock.history(period="7d")

    if data.empty:
        return None

    return {
        "symbol": symbol,
        "current_price": round(data["Close"].iloc[-1], 2),
        "avg_price": round(data["Close"].mean(), 2),
        "volume": int(data["Volume"].iloc[-1])
    }


def get_technical_indicators(symbol):

    stock = yf.Ticker(symbol)
    data = stock.history(period="1mo")

    if len(data) < 15:
        return None

    data["SMA_14"] = data["Close"].rolling(window=14).mean()

    delta = data["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()

    rs = avg_gain / avg_loss
    data["RSI"] = 100 - (100 / (1 + rs))

    return {
        "sma": round(data["SMA_14"].iloc[-1], 2),
        "rsi": round(data["RSI"].iloc[-1], 2)
    }


def get_latest_news(symbol):

    if not NEWS_API_KEY:
        return "News API key missing"

    query = symbol.replace(".NS", "")

    url = f"https://newsapi.org/v2/everything?q={query}&pageSize=3&apiKey={NEWS_API_KEY}"

    try:
        res = requests.get(url).json()
        headlines = [a["title"] for a in res.get("articles", [])]

        if headlines:
            return "\n".join(headlines)
        else:
            return "No recent news found"

    except:
        return "News fetch error"


# -------------------------
# AGENTS
# -------------------------
def stock_data_agent(stock_info):

    prompt = f"""
    You are a financial analyst.

    Interpret this stock data:

    Price: ₹{stock_info['current_price']}
    Avg Price: ₹{stock_info['avg_price']}
    Volume: {stock_info['volume']}

    Give a short interpretation.
    """

    return llm.invoke([HumanMessage(content=prompt)]).content


def technical_agent(symbol, tech):

    if not tech:
        return "Not enough data for indicators."

    prompt = f"""
    Analyze the technical indicators:

    SMA: {tech['sma']}
    RSI: {tech['rsi']}

    RSI>70 overbought
    RSI<30 oversold

    Give a short analysis.
    """

    return llm.invoke([HumanMessage(content=prompt)]).content


def news_agent(symbol, headlines):

    prompt = f"""
    Determine the sentiment for this news about {symbol}:

    {headlines}

    Classify sentiment and explain briefly.
    """

    return llm.invoke([HumanMessage(content=prompt)]).content


def supervisor_agent(symbol, price, tech, news):

    prompt = f"""
    Combine these analyses for {symbol}

    Price Analysis:
    {price}

    Technical Analysis:
    {tech}

    News Sentiment:
    {news}

    Give a short executive investment summary.
    """

    return llm.invoke([HumanMessage(content=prompt)]).content


# -------------------------
# UI
# -------------------------
st.title("📈 Multi-Agent Financial Research AI")

col1, col2 = st.columns(2)

with col1:
    symbol_input1 = st.text_input("Stock 1 (example RELIANCE)")

with col2:
    symbol_input2 = st.text_input("Stock 2 (optional comparison)")

symbol1 = symbol_input1.strip().upper()
symbol2 = symbol_input2.strip().upper()

if symbol1 and not symbol1.endswith(".NS"):
    symbol1 += ".NS"

if symbol2 and not symbol2.endswith(".NS"):
    symbol2 += ".NS"


# -------------------------
# ANALYSIS
# -------------------------
if st.button("Analyze") and symbol1:

    with st.spinner("Running AI financial agents..."):

        # STOCK 1 DATA
        stock1 = get_stock_data(symbol1)
        tech1 = get_technical_indicators(symbol1)
        news1 = get_latest_news(symbol1)

        price_insight = stock_data_agent(stock1)
        tech_insight = technical_agent(symbol1, tech1)
        news_insight = news_agent(symbol1, news1)

        final_summary = supervisor_agent(
            symbol1,
            price_insight,
            tech_insight,
            news_insight
        )

        # -------------------------
        # DISPLAY STOCK 1
        # -------------------------
        st.success("Analysis Complete")

        colA, colB, colC = st.columns(3)

        with colA:
            st.subheader("Price")
            st.write(f"₹{stock1['current_price']}")
            st.write(f"Volume: {stock1['volume']}")
            st.info(price_insight)

        with colB:
            st.subheader("Technicals")
            if tech1:
                st.write(f"SMA: {tech1['sma']}")
                st.write(f"RSI: {tech1['rsi']}")
            st.info(tech_insight)

        with colC:
            st.subheader("News Sentiment")
            st.caption(news1)
            st.info(news_insight)

        st.markdown("---")
        st.subheader("Supervisor AI Summary")
        st.write(final_summary)

        # -------------------------
        # STOCK 1 CHART
        # -------------------------
        data = yf.Ticker(symbol1).history(period="30d")

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data["Close"],
            mode="lines",
            name=symbol1
        ))

        st.plotly_chart(fig, use_container_width=True)

        # -------------------------
        # STOCK COMPARISON
        # -------------------------
        if symbol2:

            stock2 = get_stock_data(symbol2)
            tech2 = get_technical_indicators(symbol2)

            st.markdown("---")
            st.subheader("Stock Comparison")

            colX, colY = st.columns(2)

            with colX:
                st.markdown(f"### {symbol1}")
                st.write(f"Price ₹{stock1['current_price']}")
                if tech1:
                    st.write(f"RSI {tech1['rsi']}")

            with colY:
                st.markdown(f"### {symbol2}")
                st.write(f"Price ₹{stock2['current_price']}")
                if tech2:
                    st.write(f"RSI {tech2['rsi']}")

            # -------------------------
            # COMPARISON CHART
            # -------------------------
            data1 = yf.Ticker(symbol1).history(period="30d")
            data2 = yf.Ticker(symbol2).history(period="30d")

            fig2 = go.Figure()

            fig2.add_trace(go.Scatter(
                x=data1.index,
                y=data1["Close"],
                mode="lines",
                name=symbol1
            ))

            fig2.add_trace(go.Scatter(
                x=data2.index,
                y=data2["Close"],
                mode="lines",
                name=symbol2
            ))

            fig2.update_layout(
                title="Stock Price Comparison",
                xaxis_title="Date",
                yaxis_title="Price"
            )

            st.plotly_chart(fig2, use_container_width=True)
