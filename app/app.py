import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import requests
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
import os

# -------------------------
# API KEY & LLM SETUP
# -------------------------
# Streamlit will automatically load these if they are in .streamlit/secrets.toml
# or configured in Streamlit Cloud Secrets.
GROQ_API_KEY = os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY") or st.secrets.get("NEWS_API_KEY")

if not GROQ_API_KEY:
    st.error("GROQ_API_KEY not found. Please add it to your secrets.")
    st.stop()
    
if not NEWS_API_KEY:
    st.warning("NEWS_API_KEY not found. News sentiment will be disabled.")

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0,
    groq_api_key=GROQ_API_KEY,
)

# -------------------------
# STOCK DATA FUNCTIONS
# -------------------------
def get_stock_data(symbol):
    stock = yf.Ticker(symbol)
    data = stock.history(period="7d")

    if data.empty:
        return None

    current_price = data["Close"].iloc[-1]
    avg_price = data["Close"].mean()
    volume = data["Volume"].iloc[-1]

    return {
        "symbol": symbol,
        "current_price": round(current_price, 2),
        "avg_price": round(avg_price, 2),
        "volume": int(volume)
    }

def get_technical_indicators(symbol):
    stock = yf.Ticker(symbol)
    data = stock.history(period="1mo")
    
    if data.empty or len(data) < 15:
        return None
        
    data['SMA_14'] = data['Close'].rolling(window=14).mean()
    
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    data['RSI_14'] = 100 - (100 / (1 + rs))
    
    latest_sma = data['SMA_14'].iloc[-1]
    latest_rsi = data['RSI_14'].iloc[-1]
    
    return {
        "sma_14": round(latest_sma, 2),
        "rsi_14": round(latest_rsi, 2)
    }

def get_latest_news(symbol):
    if not NEWS_API_KEY:
        return "News API key missing."
        
    # Clean the symbol for a better news search (e.g., RELIANCE.NS -> RELIANCE India)
    search_query = f"{symbol.replace('.NS', '').replace('.BO', '')} India market"
    url = f"https://newsapi.org/v2/everything?q={search_query}&language=en&sortBy=publishedAt&pageSize=3&apiKey={NEWS_API_KEY}"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if data.get("status") == "ok" and data.get("articles"):
            headlines = [article["title"] for article in data["articles"]]
            return "\n".join(headlines)
        else:
            return "No recent news found for this stock."
    except Exception as e:
        return f"Error fetching news: {str(e)}"

# -------------------------
# LLM AGENTS
# -------------------------
def stock_data_agent(stock_info):
    prompt = f"""
    You are a Stock Data Agent. Briefly interpret this market data:
    Symbol: {stock_info['symbol']}
    Current Price: ₹{stock_info['current_price']}
    7-Day Average: ₹{stock_info['avg_price']}
    Volume: {stock_info['volume']}
    Provide a 2-sentence summary of the price action.
    """
    return llm.invoke([HumanMessage(content=prompt)]).content

def technical_analysis_agent(symbol, tech_data):
    if not tech_data:
        return "Insufficient data for technical analysis."
        
    prompt = f"""
    You are a Technical Analysis Agent. Analyze these indicators for {symbol}:
    14-Day SMA: ₹{tech_data['sma_14']}
    14-Day RSI: {tech_data['rsi_14']}
    
    Note: RSI above 70 is overbought, below 30 is oversold.
    Provide a 2-sentence technical outlook.
    """
    return llm.invoke([HumanMessage(content=prompt)]).content

def news_sentiment_agent(symbol, news_headlines):
    if "missing" in news_headlines or "Error" in news_headlines or "No recent news" in news_headlines:
        return "Could not analyze sentiment due to lack of news data."
        
    prompt = f"""
    You are a News Sentiment Agent. Analyze the sentiment of these recent headlines for {symbol}:
    {news_headlines}
    
    Determine if the sentiment is Bullish, Bearish, or Neutral, and explain why in 2 sentences.
    """
    return llm.invoke([HumanMessage(content=prompt)]).content

def supervisor_agent(symbol, price_insight, tech_insight, news_insight):
    prompt = f"""
    You are the Supervisor Agent for a financial research system. 
    Synthesize the following reports for {symbol} into a single cohesive, professional executive summary (max 4 sentences):
    
    1. Price Action: {price_insight}
    2. Technicals: {tech_insight}
    3. News Sentiment: {news_insight}
    """
    return llm.invoke([HumanMessage(content=prompt)]).content

# -------------------------
# UI
# -------------------------
st.title("📈 Multi-Agent Financial Research AI")

symbol_input = st.text_input("Enter Indian Stock Symbol (e.g., RELIANCE, TCS, INFY)")

symbol = symbol_input.strip().upper()

if symbol and not symbol.endswith(".NS"):
    symbol = symbol + ".NS"

if st.button("Analyze") and symbol:
    with st.spinner("Agents are gathering and analyzing market data..."):
        
        # 1. Fetch Raw Data via Tools
        stock_info = get_stock_data(symbol)
        tech_info = get_technical_indicators(symbol)
        news_headlines = get_latest_news(symbol)

        if not stock_info:
            st.error("No data found for this symbol. Please check the ticker.")
        else:
            # 2. Run Sub-Agents
            price_insight = stock_data_agent(stock_info)
            tech_insight = technical_analysis_agent(symbol, tech_info)
            news_insight = news_sentiment_agent(symbol, news_headlines)
            
            # 3. Run Supervisor Agent
            final_summary = supervisor_agent(symbol, price_insight, tech_insight, news_insight)

            # 4. Display Dashboard UI
            st.success("Analysis Complete!")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.subheader("📊 Price Data")
                st.write(f"**Price:** ₹{stock_info['current_price']}")
                st.write(f"**Volume:** {stock_info['volume']}")
                st.info(price_insight)
                
            with col2:
                st.subheader("📈 Technicals")
                if tech_info:
                    st.write(f"**SMA (14):** ₹{tech_info['sma_14']}")
                    st.write(f"**RSI (14):** {tech_info['rsi_14']}")
                else:
                    st.write("Insufficient historical data.")
                st.info(tech_insight)
                
            with col3:
                st.subheader("📰 Sentiment")
                st.write("**Latest Headlines:**")
                st.caption(news_headlines)
                st.info(news_insight)

            st.markdown("---")
            st.subheader("🤖 Supervisor Executive Summary")
            st.write(final_summary)

            # 5. Display Chart
            st.markdown("---")
            stock = yf.Ticker(symbol)
            chart_data = stock.history(period="30d")
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=chart_data.index, y=chart_data["Close"], mode="lines", name="Close Price"))
            fig.update_layout(title=f"{symbol} - Last 30 Days", xaxis_title="Date", yaxis_title="Price (₹)")
            
            st.plotly_chart(fig, use_container_width=True)
