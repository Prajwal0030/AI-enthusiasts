# AI Financial Research Assistant

## Project Vision

This project aims to build a **multi-agent financial research system** that helps analyze stocks using real-time market data, technical indicators, and news sentiment.

The system is designed as a modular **agent-based architecture** where specialized agents analyze different aspects of financial data and a supervisor agent synthesizes the final insight.

Future agents planned for the system include:

- Stock Analysis Agent
- Technical Analysis Agent
- News Sentiment Agent
- Risk Modeling Agent (future)
- Portfolio Optimization Agent (future)
- Supervisor Agent (controls orchestration)

---

# Current Features (Week 2)

The system currently supports:

### Stock Data Analysis
Retrieves real-time Indian stock data using **Yahoo Finance API (yfinance)** including:

- Current stock price
- Average price
- Trading volume

### Technical Indicators
Calculates basic technical indicators including:

- 14-day Simple Moving Average (SMA)
- 14-day Relative Strength Index (RSI)

### News Sentiment Analysis
Fetches the latest financial news headlines using **News API** and uses an LLM to determine:

- Bullish
- Bearish
- Neutral sentiment

### Supervisor Agent
A **Supervisor AI Agent** synthesizes the outputs from:

- Stock Data Agent
- Technical Analysis Agent
- News Sentiment Agent

and generates a final **executive financial summary**.

### Interactive Visualization
The platform also includes:

- 30-day stock price chart
- Interactive Plotly visualization
- Streamlit dashboard

---

# Architecture (Simplified)

User Input  
↓  
Stock Data Tool (Yahoo Finance API)  
↓  
Technical Analysis Tool  
↓  
News Retrieval Tool (News API)  
↓  
LLM Agents analyze each data source  
↓  
Supervisor Agent synthesizes insights  
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

Implemented:

- Stock data retrieval using yfinance
- Basic LLM insight generation
- Streamlit dashboard
- 30-day price visualization

---

# Week 2 Implementation

Expanded the system into a **multi-agent financial analysis platform** by introducing:

- Stock Data Agent
- Technical Analysis Agent
- News Sentiment Agent
- Supervisor Agent for final financial reasoning

The application now provides a comprehensive analysis combining **market data, technical indicators, and news sentiment**.

---

# Future Roadmap

Upcoming improvements include:

- Multi-agent investment debate system
- Portfolio risk exposure analysis
- Market regime detection
- Portfolio optimization agents
- Advanced multi-agent orchestration

---

# Deployment

The application is deployed using **Streamlit Cloud**.

Users can enter an Indian stock symbol such as:
RELIANCE
TCS
INFY

and receive a full AI-powered financial analysis.

---

# Goal of the Project

The long-term goal is to build a **financial intelligence platform powered by AI agents** capable of assisting investors with deeper research and decision-making.
