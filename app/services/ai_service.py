import os
from google import genai
from google.genai import types
from app.services.finance_service import get_stock_quote, get_financial_news, get_stock_history, search_stocks

def lookup_stock_price(symbol: str) -> dict:
    """Gets the current stock price, name, exchange, and currency for a stock symbol."""
    try:
        quote = get_stock_quote(symbol.upper())
        return {
            "symbol": symbol,
            "name": quote.get('name'),
            "exchange": quote.get('exchange'),
            "price": quote.get('price'),
            "currency": quote.get('currency'),
            "change": quote.get('change'),
            "change_percent": quote.get('change_percent')
        }
    except Exception as e:
        return {"error": str(e)}

def search_news(query: str) -> list:
    """Gets the latest financial news for a company, topic, or stock symbol."""
    try:
        articles = get_financial_news(query)
        return [{"title": a.get("title"), "source": a.get("source"), "date": a.get("publishedAt"), "description": a.get("description")} for a in articles[:5]]
    except Exception as e:
        return [{"error": str(e)}]

def search_company_symbol(company_name: str) -> list:
    """Searches for the correct stock symbol for a given company name."""
    try:
        results = search_stocks(company_name)
        return [{"symbol": r.get("symbol"), "name": r.get("name"), "exchange": r.get("exchange")} for r in results[:3]]
    except Exception as e:
        return [{"error": str(e)}]

SYSTEM_INSTRUCTION = """
You are the Finance Insight Agent, a professional AI financial assistant.
Your role is to analyze stocks, summarize financial news, and answer queries.

CRITICAL RULES:
1. FACTUAL ACCURACY: You MUST use the provided tools (`search_company_symbol`, `lookup_stock_price`, `search_news`) to retrieve real, up-to-date information before answering. NEVER fabricate prices, news, statistics, or company data. If you compare two stocks, look up both stocks.
2. DISTINGUISH FACTS FROM INTERPRETATION: Clearly separate facts you retrieved using tools from your own analysis or interpretation.
3. NO FINANCIAL ADVICE: Never act as a financial adviser. Never tell the user to buy, sell, or hold a stock. Use neutral wording.
4. STRUCTURE: Use clear, readable markdown structure. Use bullet points or sections (e.g., Summary, Current Data, Recent News) where appropriate.

If the user asks about a company but you aren't sure of its exact Yahoo Finance ticker symbol (especially for international/Indian stocks like TCS -> TCS.NS), use `search_company_symbol` first.
"""

def fetch_agent_insight(query: str, history: list = None) -> str:
    """
    history format: [{'role': 'user', 'text': 'Hello'}, {'role': 'model', 'text': 'Hi'}]
    """
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key or api_key == 'your-gemini-api-key-here':
        raise Exception("AI Analysis Unavailable: The AI service is currently not configured. The administrator needs to configure the GEMINI_API_KEY environment variable.")

    client = genai.Client(api_key=api_key)
    model_name = "gemini-2.5-flash"
    
    config = types.GenerateContentConfig(
        tools=[search_company_symbol, lookup_stock_price, search_news],
        system_instruction=SYSTEM_INSTRUCTION,
        temperature=0.2
    )

    contents = []
    if history:
        for msg in history:
            role = msg.get('role')
            text = msg.get('text')
            if role and text:
                contents.append(types.Content(role=role, parts=[types.Part.from_text(text=text)]))

    try:
        if contents:
            chat = client.chats.create(model=model_name, config=config, history=contents)
        else:
            chat = client.chats.create(model=model_name, config=config)
            
        import time
        max_retries = 3
        base_delay = 1
        
        for attempt in range(max_retries):
            try:
                response = chat.send_message(query)
                return response.text
            except Exception as e:
                err_msg = str(e)
                
                is_quota = "429" in err_msg or "quota" in err_msg.lower() or "resource_exhausted" in err_msg.lower()
                is_timeout = "503" in err_msg or "504" in err_msg or "timeout" in err_msg.lower() or "deadline_exceeded" in err_msg.lower()
                is_auth = "401" in err_msg or "403" in err_msg or "api_key" in err_msg.lower()
                
                # Only retry timeouts
                if is_timeout and attempt < max_retries - 1:
                    time.sleep(base_delay * (2 ** attempt))
                    continue
                    
                if is_quota:
                    raise Exception("AI Analysis Unavailable (Quota Exceeded): The AI service rate limit or daily quota has been reached. Please check back later. The rest of the platform remains fully operational.")
                if is_timeout:
                    raise Exception("AI Analysis Unavailable: The service is currently experiencing high demand or a temporary timeout. Please try again in a few moments.")
                if is_auth:
                    raise Exception("AI Analysis Unavailable: Invalid API Key. Please contact the administrator to verify the configuration.")
                
                raise Exception(f"AI Provider Error: {str(e)} (Details: {e.__class__.__name__})")
                
    except Exception as e:
        # If it's already one of our custom exceptions, re-raise it exactly as is
        if "AI Analysis Unavailable" in str(e) or "AI Provider Error" in str(e):
            raise
        raise Exception(f"AI Provider Error: {str(e)} (Details: {e.__class__.__name__})")
