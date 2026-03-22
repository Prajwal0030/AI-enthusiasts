# AI Financial Research Assistant

## Project Vision

This project aims to build a **multi-agent financial intelligence platform** that assists users in analyzing stocks using real-time market data, technical indicators, and AI-driven insights.

The system follows a modular **agent-based architecture**, where multiple specialized AI agents collaborate to generate comprehensive financial analysis and investment recommendations.

---

# Current Features (Week 4)

### Multi-Agent Financial Analysis

The system includes multiple AI agents:

- Stock Analysis Agent – interprets price and volume data  
- Technical Analysis Agent – analyzes SMA, EMA, RSI  
- News Sentiment Agent – evaluates recent market news  
- Supervisor Agent – combines all insights into a structured summary  

---

### AI Investment Decision System

- Generates **Buy / Hold / Sell recommendations**
- Provides **confidence level**
- Includes **reasoning based on technical + sentiment analysis**

---

### Multi-Agent Debate System

- **Bull Agent** – highlights growth opportunities  
- **Bear Agent** – identifies risks  
- **Judge Agent** – gives final balanced decision  

---

### Portfolio AI Analyzer

Users can input multiple stocks to get:

- Diversification analysis  
- Risk evaluation  
- Strengths and weaknesses  
- Investment suggestions  

---

### Advanced Technical Indicators

Includes:

- SMA (Trend analysis)  
- EMA (Short-term trend sensitivity)  
- RSI (Momentum indicator)  

Also provides **AI-based interpretation** for better decision-making.

---

### Stock Comparison System

- Compare two stocks simultaneously  
- Visualize performance with interactive charts  

---

### Economic Context Agent

Provides macro-level insights:

- Inflation trends  
- Interest rates  
- Market sentiment  
- Investment outlook  

---

### UI & Performance

- Tab-based dashboard for structured insights  
- Interactive Plotly charts  
- Streamlit caching for performance optimization  

---

# Architecture (Simplified)

User Input  
↓  
Stock Data (Yahoo Finance API)  
↓  
Technical Indicators + News Data  
↓  
Multi-Agent Analysis  
↓  
Supervisor + Debate Agents  
↓  
Recommendation System  
↓  
Streamlit Dashboard  

---

# Tech Stack

- Python  
- Streamlit  
- Plotly  
- yfinance  
- News API  
- LangChain  
- Groq LLM  
- Pandas  

---

# Week 1 Implementation

- Stock data retrieval  
- Basic LLM insights  
- Streamlit dashboard  

---

# Week 2 Implementation

- Multi-agent architecture  
- Technical + sentiment analysis  
- Supervisor agent  

---

# Week 3 Implementation

- Multi-agent debate system  
- Stock comparison  
- UI upgrade  
- Performance optimization  

---

# Week 4 Implementation

- Investment recommendation system (Buy/Hold/Sell)  
- Portfolio AI analyzer  
- Advanced indicators (SMA, EMA, RSI)  
- Economic context agent  
- Improved structured AI outputs  

---

# Deployment

Deployed on **Streamlit Cloud**

Users can analyze stocks like:

RELIANCE  
TCS  
INFY  

---

# Goal

To build a **real-world financial intelligence system powered by AI agents** that helps users make smarter investment decisions.
