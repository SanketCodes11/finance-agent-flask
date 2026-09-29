import os
# Fix Vercel read-only filesystem issue for yfinance
os.environ["YFINANCE_CACHE_DIR"] = "/tmp/yf_cache"

import requests
import yfinance as yf

# Global session to bypass Vercel IP blocks
yf_session = requests.Session()
yf_session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive'
})

try:
    yf.set_tz_cache_location("/tmp/yf_tz")
except Exception:
    pass

import requests
from flask import current_app
import time
import threading

QUOTE_CACHE = {}
QUOTE_CACHE_LOCK = threading.Lock()
QUOTE_CACHE_TTL = 300  # 5 minutes

YAHOO_CIRCUIT_BREAKER = {
    'is_open': False,
    'opened_at': 0,
    'timeout': 900  # 15 minutes
}
YAHOO_CB_LOCK = threading.Lock()

def _check_yahoo_circuit():
    with YAHOO_CB_LOCK:
        if YAHOO_CIRCUIT_BREAKER['is_open']:
            if time.time() - YAHOO_CIRCUIT_BREAKER['opened_at'] > YAHOO_CIRCUIT_BREAKER['timeout']:
                YAHOO_CIRCUIT_BREAKER['is_open'] = False
                return True
            return False
        return True

def _trip_yahoo_circuit():
    with YAHOO_CB_LOCK:
        if not YAHOO_CIRCUIT_BREAKER['is_open']:
            YAHOO_CIRCUIT_BREAKER['is_open'] = True
            YAHOO_CIRCUIT_BREAKER['opened_at'] = time.time()
            current_app.logger.warning("Yahoo Finance circuit breaker tripped.")

def _fetch_yahoo_quote(symbol):
    if not _check_yahoo_circuit():
        raise ValueError("Market data currently unavailable (Yahoo rate limited).")
        
    try:
        ticker = yf.Ticker(symbol, session=yf_session)
        
        try:
            info = ticker.info
        except Exception:
            info = {}
            
        fast_info = getattr(ticker, 'fast_info', {})
        
        hist = ticker.history(period="5d")
        if hist.empty:
            errors = []
            
            try:
                return _fetch_yahoo_history_raw(symbol, period, interval)
            except Exception as e:
                errors.append(f"Yahoo Raw: {str(e)}")
                
            api_key = current_app.config.get('TWELVE_DATA_API_KEY')
            if api_key and api_key != 'your-twelvedata-api-key-here':
                try:
                    return _fetch_twelvedata_history(symbol, period, interval, api_key)
                except Exception as e:
                    errors.append(f"TwelveData: {str(e)}")
            else:
                errors.append("TwelveData API Key missing.")
                
            raise ValueError(f"No historical data found. Details: {' | '.join(errors)}")

            
        labels = [date.strftime('%Y-%m-%d') for date in hist.index]
        timestamps = [int(date.timestamp()) for date in hist.index]
        opens = [round(price, 2) for price in hist['Open'].tolist()]
        highs = [round(price, 2) for price in hist['High'].tolist()]
        lows = [round(price, 2) for price in hist['Low'].tolist()]
        closes = [round(price, 2) for price in hist['Close'].tolist()]
        volumes = [int(v) for v in hist['Volume'].tolist()]
        
        return {
            'labels': labels,
            'prices': closes,
            'timestamps': timestamps,
            'open': opens,
            'high': highs,
            'low': lows,
            'close': closes,
            'volume': volumes
        }
    except Exception as e:
        err_msg = str(e).lower()
        if '429' in err_msg or 'too many requests' in err_msg:
            _trip_yahoo_circuit()
            raise ValueError("Market history currently unavailable (Yahoo rate limited).")
        raise ValueError(f"Failed to fetch history for {symbol}: {str(e)}")

import time

NEWS_CACHE = {}
NEWS_CACHE_TTL = 300  # 5 minutes

class NewsAPIError(Exception):
    pass

class NewsNotConfiguredError(Exception):
    pass

def get_financial_news(query='finance'):
    api_key = current_app.config.get('NEWS_API_KEY')
    if not api_key or api_key == 'your-newsapi-key-here':
        raise NewsNotConfiguredError("News service is not configured. Administrator needs to configure the NEWS_API_KEY.")
        
    cache_key = query.lower()
    current_time = time.time()
    
    if cache_key in NEWS_CACHE:
        cache_data, timestamp = NEWS_CACHE[cache_key]
        if current_time - timestamp < NEWS_CACHE_TTL:
            return cache_data
            
    url = f"https://newsapi.org/v2/everything?q={query}&sortBy=publishedAt&language=en&pageSize=10"
    headers = {'X-Api-Key': api_key, 'User-Agent': 'FinanceInsightAgent/1.0'}
    
    try:
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 429:
            raise NewsAPIError("NewsAPI rate limit exceeded. Please try again later.")
        elif response.status_code == 401:
            raise NewsAPIError("Invalid NEWS_API_KEY configured.")
        
        response.raise_for_status()
        data = response.json()
        
        articles = []
        for item in data.get('articles', []):
            if item.get('title') and item.get('url') and item.get('title') != '[Removed]':
                articles.append({
                    'title': item.get('title'),
                    'description': item.get('description'),
                    'url': item.get('url'),
                    'source': item.get('source', {}).get('name', 'Unknown'),
                    'publishedAt': item.get('publishedAt'),
                    'urlToImage': item.get('urlToImage')
                })
                
        NEWS_CACHE[cache_key] = (articles, current_time)
        return articles
        
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"NewsAPI network error: {str(e)}")
        raise NewsAPIError("Network error occurred while fetching news. Please try again.")
    except Exception as e:
        current_app.logger.error(f"NewsAPI error: {str(e)}")
        if isinstance(e, NewsAPIError):
            raise
        raise NewsAPIError("An unexpected error occurred while fetching news.")

def search_stocks(query):
    if not query:
        return []
    
    url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query}&quotesCount=10"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        results = []
        for quote in data.get('quotes', []):
            if quote.get('quoteType') not in ['EQUITY', 'ETF', 'MUTUALFUND']:
                continue
                
            results.append({
                'symbol': quote.get('symbol'),
                'name': quote.get('longname') or quote.get('shortname') or quote.get('symbol'),
                'exchange': quote.get('exchDisp') or quote.get('exchange', ''),
                'type': quote.get('typeDisp', ''),
                'score': quote.get('score', 0)
            })
            
        return results
    except Exception as e:
        current_app.logger.error(f"Search API error: {str(e)}")
        return []


