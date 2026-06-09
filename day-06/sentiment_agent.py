"""
Day 6: Sentiment Analysis Agent for FinTech Research
Adds news sentiment analysis to multi-agent system
"""

import requests
import os
import json
import re
from typing import TypedDict, Annotated
from dotenv import load_dotenv
import operator
from datetime import datetime

load_dotenv()
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

if not MISTRAL_API_KEY:
    print("❌ Error: MISTRAL_API_KEY not found")
    exit(1)

print("✅ API key loaded")

# ============================================
# STEP 1: Define State (Updated for Sentiment)
# ============================================

class FinTechAgentState(TypedDict):
    messages: Annotated[list, operator.add]
    user_input: str
    next_agent: str
    stock_data: dict
    sentiment_data: dict
    return_calculation: dict
    final_answer: str

# ============================================
# STEP 2: Stock Price Tool 
# ============================================

def get_stock_price(symbol: str) -> dict:
    """Fetch stock price using yfinance"""
    try:
        import yfinance as yf
        stock = yf.Ticker(symbol)
        info = stock.info
        
        current_price = info.get('regularMarketPrice', info.get('currentPrice', 0))
        previous_close = info.get('regularMarketPreviousClose', info.get('previousClose', 0))
        
        daily_change = current_price - previous_close if previous_close else 0
        daily_change_percent = (daily_change / previous_close) * 100 if previous_close else 0
        
        return {
            "symbol": symbol.upper(),
            "current_price": round(current_price, 2),
            "previous_close": round(previous_close, 2),
            "daily_change": round(daily_change, 2),
            "daily_change_percent": round(daily_change_percent, 2),
            "name": info.get('longName', symbol.upper()),
            "market_cap": info.get('marketCap', 'N/A')
        }
    except Exception as e:
        return {"symbol": symbol.upper(), "error": str(e), "current_price": 0}

# ============================================
# STEP 3: News Fetching Tool 
# ============================================

def get_stock_news(symbol: str) -> list:
    
    try:
        # Using yfinance news (free, built into the library)
        import yfinance as yf
        stock = yf.Ticker(symbol)
        
        # Get news (returns list of dicts with title, link, publisher, etc.)
        news = stock.news
        
        if not news:
            return []
        
        # Extract relevant information
        articles = []
        for item in news[:5]:  # Get top 5 news articles
            articles.append({
                "title": item.get('title', 'No title'),
                "publisher": item.get('publisher', 'Unknown'),
                "link": item.get('link', '#'),
                "published": item.get('providerPublishTime', 'Unknown')
            })
        
        return articles
    except Exception as e:
        print(f"   ⚠️ News fetch error: {e}")
        return []

# ============================================
# STEP 4: Sentiment Analysis with Mistral AI
# ============================================

def analyze_sentiment(symbol: str, news_articles: list) -> dict:
    
    if not news_articles:
        return {
            "symbol": symbol,
            "overall_sentiment": "neutral",
            "confidence": 0,
            "summary": "No news available for analysis",
            "key_drivers": []
        }
    
    # Prepare news text for analysis
    news_text = ""
    for i, article in enumerate(news_articles, 1):
        news_text += f"{i}. {article['title']}\n"
    
    prompt = f"""
Analyze the sentiment of these news headlines for stock {symbol}:

{news_text}

Return ONLY valid JSON in this exact format:
{{
    "overall_sentiment": "positive" or "negative" or "neutral",
    "confidence": 0-100,
    "summary": "One sentence summary of sentiment",
    "key_drivers": ["driver1", "driver2"]
}}
"""

    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "mistral-small-latest",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 300
    }
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=30)
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            # Extract JSON from response
            import json as json_lib
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                sentiment_data = json_lib.loads(json_match.group())
                return {
                    "symbol": symbol,
                    "overall_sentiment": sentiment_data.get("overall_sentiment", "neutral"),
                    "confidence": sentiment_data.get("confidence", 0),
                    "summary": sentiment_data.get("summary", ""),
                    "key_drivers": sentiment_data.get("key_drivers", []),
                    "articles_analyzed": len(news_articles)
                }
    except Exception as e:
        print(f"   ⚠️ Sentiment analysis error: {e}")
    
    return {
        "symbol": symbol,
        "overall_sentiment": "neutral",
        "confidence": 0,
        "summary": "Could not analyze sentiment",
        "key_drivers": []
    }

# ============================================
# STEP 5: Sentiment Analysis Agent Node
# ============================================

def sentiment_agent_node(state: FinTechAgentState) -> dict:
    """Agent that fetches news and analyzes sentiment"""
    
    question = state.get("user_input", "")
    
    # Extract stock symbol from question
    stock_symbols = ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN", "META", "NVDA"]
    stock_names = {
        "apple": "AAPL", "google": "GOOGL", "microsoft": "MSFT",
        "tesla": "TSLA", "amazon": "AMZN", "meta": "META", "nvidia": "NVDA"
    }
    
    found_symbol = None
    for name, symbol in stock_names.items():
        if name in question.lower():
            found_symbol = symbol
            break
    
    if not found_symbol:
        for symbol in stock_symbols:
            if symbol.lower() in question.lower():
                found_symbol = symbol
                break
    
    if not found_symbol:
        return {"sentiment_data": {"error": "Could not identify stock symbol"}}
    
    print(f"📰 Sentiment Agent: Analyzing news for {found_symbol}...")
    
    # Fetch news
    news = get_stock_news(found_symbol)
    print(f"   Found {len(news)} recent articles")
    
    # Analyze sentiment
    sentiment = analyze_sentiment(found_symbol, news)
    
    return {"sentiment_data": sentiment}

# ============================================
# STEP 6: Supervisor Agent 
# ============================================

def supervisor_node(state: FinTechAgentState) -> dict:
    """Supervisor routes to appropriate agent"""
    
    question = state.get("user_input", "").lower()
    
    # Sentiment keywords
    sentiment_keywords = ["sentiment", "news", "feeling", "market mood", 
                          "positive", "negative", "reaction", "impact"]
    
    # Stock price keywords
    price_keywords = ["price", "stock", "trading", "worth", "value", 
                      "aapl", "googl", "msft", "tsla", "apple", "tesla"]
    
    if any(k in question for k in sentiment_keywords):
        print("👔 Supervisor: Routing to Sentiment Analysis Agent")
        return {"next_agent": "sentiment_agent"}
    elif any(k in question for k in price_keywords):
        print("👔 Supervisor: Routing to Stock Price Agent")
        return {"next_agent": "stock_price_agent"}
    else:
        print("👔 Supervisor: Routing to Final Answer")
        return {"next_agent": "final_answer"}

# ============================================
# STEP 7: Stock Price Agent Node
# ============================================

def stock_price_agent_node(state: FinTechAgentState) -> dict:
    
    
    question = state.get("user_input", "")
    
    stock_names = {
        "apple": "AAPL", "google": "GOOGL", "microsoft": "MSFT",
        "tesla": "TSLA", "amazon": "AMZN", "meta": "META", "nvidia": "NVDA"
    }
    
    found_symbol = None
    for name, symbol in stock_names.items():
        if name in question.lower():
            found_symbol = symbol
            break
    
    if not found_symbol:
        for symbol in ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN", "META", "NVDA"]:
            if symbol.lower() in question.lower():
                found_symbol = symbol
                break
    
    if found_symbol:
        print(f"💹 Stock Price Agent: Fetching data for {found_symbol}...")
        stock_data = get_stock_price(found_symbol)
        
        # Check for buy price in question
        numbers = re.findall(r'\d+', question)
        return_calc = {}
        if numbers and ("bought" in question.lower() or "purchase" in question.lower()):
            buy_price = float(numbers[0])
            current_price = stock_data.get("current_price", 0)
            if current_price > 0:
                absolute_return = current_price - buy_price
                percentage_return = (absolute_return / buy_price) * 100
                return_calc = {
                    "buy_price": buy_price,
                    "absolute_return": round(absolute_return, 2),
                    "percentage_return": round(percentage_return, 2),
                    "is_profit": percentage_return > 0
                }
        
        return {"stock_data": stock_data, "return_calculation": return_calc}
    
    return {"stock_data": {"error": "Could not identify stock"}}

# ============================================
# STEP 8: Final Answer Node 
# ============================================

def final_answer_node(state: FinTechAgentState) -> dict:
    """Generate final response using Mistral AI"""
    
    context_parts = []
    
    # Add sentiment data if available
    sentiment = state.get("sentiment_data", {})
    if sentiment and not sentiment.get("error"):
        context_parts.append(f"""
Sentiment Analysis for {sentiment.get('symbol')}:
- Overall Sentiment: {sentiment.get('overall_sentiment', 'neutral')} (confidence: {sentiment.get('confidence', 0)}%)
- Summary: {sentiment.get('summary', 'No summary')}
- Key Drivers: {', '.join(sentiment.get('key_drivers', []))}
- Articles Analyzed: {sentiment.get('articles_analyzed', 0)}
""")
    
    # Add stock data if available
    stock = state.get("stock_data", {})
    if stock and not stock.get("error"):
        context_parts.append(f"""
Stock Data for {stock.get('symbol')}:
- Current Price: ${stock.get('current_price', 0)}
- Daily Change: ${stock.get('daily_change', 0)} ({stock.get('daily_change_percent', 0)}%)
- Market Cap: {stock.get('market_cap', 'N/A')}
""")
    
    # Add return calculation if available
    ret = state.get("return_calculation", {})
    if ret and not ret.get("error"):
        profit_status = "PROFIT" if ret.get("is_profit") else "LOSS"
        context_parts.append(f"""
Return Analysis:
- Return: ${ret.get('absolute_return', 0)} ({ret.get('percentage_return', 0)}%) - {profit_status}
""")
    
    if context_parts:
        context = "\n".join(context_parts)
        prompt = f"""
Based on this research:

{context}

Answer the user's question naturally and helpfully: {state.get('user_input')}

Be concise (2-3 sentences). If sentiment is positive, mention it. If it's a loss, be neutral but factual.
"""
    else:
        prompt = f"Answer this question concisely and helpfully: {state.get('user_input')}"
    
    # Call Mistral
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "mistral-small-latest",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 200
    }
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=30)
        if response.status_code == 200:
            return {"final_answer": response.json()["choices"][0]["message"]["content"]}
        return {"final_answer": f"Error: API returned {response.status_code}"}
    except Exception as e:
        return {"final_answer": f"Error: {e}"}

# ============================================
# STEP 9: Orchestrator
# ============================================

def run_fintech_agent(question: str):
    """Run the complete multi-agent FinTech system"""
    
    print("\n" + "="*60)
    print(f"❓ User: {question}")
    print("="*60)
    
    state = {
        "messages": [],
        "user_input": question,
        "next_agent": "",
        "stock_data": {},
        "sentiment_data": {},
        "return_calculation": {},
        "final_answer": ""
    }
    
    # Supervisor decides
    state.update(supervisor_node(state))
    
    # Execute appropriate agent
    if state.get("next_agent") == "sentiment_agent":
        state.update(sentiment_agent_node(state))
    elif state.get("next_agent") == "stock_price_agent":
        state.update(stock_price_agent_node(state))
    
    # Generate final answer
    state.update(final_answer_node(state))
    
    print(f"\n🤖 Final Answer: {state['final_answer']}")
    print("="*60)
    
    return state

# ============================================
# STEP 10: Main
# ============================================

if __name__ == "__main__":
    print("="*60)
    print("🤖 DAY 6: MULTI-AGENT SYSTEM WITH SENTIMENT ANALYSIS")
    print("="*60)
    
    try:
        import yfinance
        print("✅ yfinance ready")
    except ImportError:
        print("⚠️ Install yfinance: pip install yfinance")
    
    test_questions = [
        "What is Apple stock price?",
        "What is the sentiment around Tesla stock?",
        "I bought Microsoft at $300. How am I doing?",
        "What is an AI agent?"
    ]
    
    for q in test_questions:
        run_fintech_agent(q)
    
    print("\n" + "="*60)
    print("✅ Sentiment Analysis Agent Working!")
    print("="*60)