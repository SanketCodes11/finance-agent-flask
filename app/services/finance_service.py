import os
# Fix Vercel read-only filesystem issue for yfinance
os.environ["YFINANCE_CACHE_DIR"] = "/tmp/yf_cache"
import yfinance as yf
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
        ticker = yf.Ticker(symbol)
        
        try:
            info = ticker.info
        except Exception:
            info = {}
            
        fast_info = getattr(ticker, 'fast_info', {})
        
        hist = ticker.history(period="5d")
        if hist.empty:
            raise ValueError("No price data available for this symbol.")
            
        current_price = hist['Close'].iloc[-1]
        previous_close = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
        
        change = current_price - previous_close
        change_percent = (change / previous_close) * 100 if previous_close else 0
        
        currency = info.get('currency', fast_info.get('currency', 'USD'))
        
        inr_price = None
        if currency and currency.upper() != 'INR':
            try:
                forex_ticker = yf.Ticker(f"{currency.upper()}INR=X")
                fx_rate = getattr(forex_ticker, 'fast_info', {}).get('lastPrice')
                if not fx_rate:
                    fx_hist = forex_ticker.history(period="1d")
                    if not fx_hist.empty:
                        fx_rate = fx_hist['Close'].iloc[-1]
                if fx_rate:
                    inr_price = round(float(current_price * fx_rate), 2)
            except Exception:
                pass
                
        exchange = info.get('exchange') or fast_info.get('exchange', 'Unknown Exchange')
        if exchange in ['BSE', 'BSI']:
            exchange = 'BSE (Bombay Stock Exchange)'
        elif exchange in ['NSE', 'NSI']:
            exchange = 'NSE (National Stock Exchange)'
            
        return {
            'symbol': symbol,
            'name': info.get('longName', info.get('shortName', symbol)),
            'price': round(float(current_price), 2),
            'currency': currency,
            'inr_price': inr_price,
            'exchange': exchange,
            'country': info.get('country', 'Unknown'),
            'change': round(float(change), 2),
            'change_percent': round(float(change_percent), 2),
            'previous_close': round(float(previous_close), 2),
            'open': round(float(hist['Open'].iloc[-1]), 2),
            'day_high': round(float(hist['High'].iloc[-1]), 2),
            'day_low': round(float(hist['Low'].iloc[-1]), 2),
            'fiftyTwoWeekHigh': info.get('fiftyTwoWeekHigh', fast_info.get('yearHigh')),
            'fiftyTwoWeekLow': info.get('fiftyTwoWeekLow', fast_info.get('yearLow')),
            'volume': int(hist['Volume'].iloc[-1]),
            'market_cap': info.get('marketCap', fast_info.get('marketCap', 0)),
            'description': info.get('longBusinessSummary', 'Description unavailable.'),
            'provider': 'Yahoo Finance',
            'last_updated': int(time.time())
        }
    except Exception as e:
        err_msg = str(e).lower()
        if '429' in err_msg or 'too many requests' in err_msg:
            _trip_yahoo_circuit()
            raise ValueError("Market data currently unavailable (Yahoo rate limited).")
        raise ValueError(f"Failed to fetch data for {symbol}: {str(e)}")

def _fetch_twelvedata_quote(symbol, api_key):
    norm = symbol.upper().strip()
    exchange_param = ""
    twelve_sym = norm
    if norm.endswith(".NS"):
        twelve_sym = norm[:-3]
        exchange_param = "&exchange=NSE"
    elif norm.endswith(".BO"):
        twelve_sym = norm[:-3]
        exchange_param = "&exchange=BSE"
        
    url = f"https://api.twelvedata.com/quote?symbol={twelve_sym}{exchange_param}&apikey={api_key}"
    resp = requests.get(url, timeout=5)
    resp.raise_for_status()
    data = resp.json()
    
    if data.get('status') == 'error':
        if data.get('code') == 429:
            raise Exception("429_TWELVEDATA")
        raise ValueError(data.get('message', 'Twelve Data API Error'))
        
    current_price = float(data.get('close') or 0.0)
    previous_close = float(data.get('previous_close') or current_price)
    change = float(data.get('change') or 0.0)
    change_percent = float(data.get('percent_change') or 0.0)
    
    currency = data.get('currency', 'USD')
    
    inr_price = None
    if currency and currency.upper() != 'INR':
        try:
            # Fallback to yahoo for forex only, or Twelve Data price
            fx_url = f"https://api.twelvedata.com/price?symbol={currency.upper()}/INR&apikey={api_key}"
            fx_resp = requests.get(fx_url, timeout=3).json()
            if 'price' in fx_resp:
                inr_price = round(current_price * float(fx_resp['price']), 2)
        except Exception:
            pass
            
    exchange_str = data.get('exchange', 'Unknown')
    if 'NSE' in exchange_str.upper():
        exchange_str = 'NSE (National Stock Exchange)'
    elif 'BSE' in exchange_str.upper():
        exchange_str = 'BSE (Bombay Stock Exchange)'
        
    ft_week = data.get('fifty_two_week', {})
    
    return {
        'symbol': symbol,
        'name': data.get('name') or symbol,
        'price': round(current_price, 2),
        'currency': currency,
        'inr_price': inr_price,
        'exchange': exchange_str,
        'country': 'Unknown',
        'change': round(change, 2),
        'change_percent': round(change_percent, 2),
        'previous_close': round(previous_close, 2),
        'open': round(float(data.get('open') or 0.0), 2),
        'day_high': round(float(data.get('high') or 0.0), 2),
        'day_low': round(float(data.get('low') or 0.0), 2),
        'fiftyTwoWeekHigh': float(ft_week.get('high') or 0.0) if ft_week.get('high') else None,
        'fiftyTwoWeekLow': float(ft_week.get('low') or 0.0) if ft_week.get('low') else None,
        'volume': int(data.get('volume') or 0),
        'market_cap': 0,
        'description': 'Description unavailable via standard tier.',
        'provider': 'Twelve Data',
        'last_updated': int(data.get('timestamp') or time.time())
    }

def get_stock_quote(symbol):
    if not symbol:
        raise ValueError("Symbol is required")
        
    normalized_symbol = symbol.upper().strip()
    current_time = time.time()
    
    with QUOTE_CACHE_LOCK:
        if normalized_symbol in QUOTE_CACHE:
            data, timestamp = QUOTE_CACHE[normalized_symbol]
            if current_time - timestamp < QUOTE_CACHE_TTL:
                return data

    api_key = current_app.config.get('TWELVE_DATA_API_KEY')
    result = None
    
    if api_key and api_key != 'your-twelvedata-api-key-here':
        try:
            result = _fetch_twelvedata_quote(symbol, api_key)
        except Exception as e:
            err_str = str(e)
            if '429_TWELVEDATA' in err_str or '429' in err_str:
                current_app.logger.warning("TwelveData 429 rate limit hit.")
            else:
                current_app.logger.error(f"TwelveData fetch error for {symbol}: {err_str}")
            result = None
            

    if not result:
        try:
            result = _fetch_yahoo_quote(symbol)
        except Exception:
            result = None

    if not result and '.' not in normalized_symbol:
        # If both providers failed and it's a generic symbol, it might be an Indian/international stock missing its suffix.
        # Let's search for it and use the top result's exact symbol.
        search_res = search_stocks(normalized_symbol)
        if search_res and search_res[0].get('symbol') != normalized_symbol:
            best_match = search_res[0].get('symbol')
            # Try fetching with the corrected symbol
            if api_key and api_key != 'your-twelvedata-api-key-here':
                try:
                    result = _fetch_twelvedata_quote(best_match, api_key)
                except Exception:
                    pass
            if not result:
                result = _fetch_yahoo_quote(best_match)
                
    if not result:
        raise ValueError("Market data currently unavailable. Could not fetch current live data.")
        
    with QUOTE_CACHE_LOCK:
        QUOTE_CACHE[normalized_symbol] = (result, time.time())
        
    return result

def get_multiple_stock_quotes(symbols):
    if not symbols:
        return {}
    
    results = {}
    import concurrent.futures
    
    unique_requests = {}
    for sym in symbols:
        if not sym: continue
        norm = sym.upper().strip()
        if norm not in unique_requests:
            unique_requests[norm] = []
        unique_requests[norm].append(sym)
        
    symbols_to_fetch = []
    current_time = time.time()
    
    with QUOTE_CACHE_LOCK:
        for norm, orig_list in unique_requests.items():
            if norm in QUOTE_CACHE:
                data, timestamp = QUOTE_CACHE[norm]
                if current_time - timestamp < QUOTE_CACHE_TTL:
                    for orig_sym in orig_list:
                        results[orig_sym] = data
                else:
                    symbols_to_fetch.append(norm)
            else:
                symbols_to_fetch.append(norm)
                
    if not symbols_to_fetch:
        return results
        
    from flask import current_app
    app_obj = current_app._get_current_object()
        
    def fetch_single(norm_sym):
        with app_obj.app_context():
            try:
                return norm_sym, get_stock_quote(norm_sym)
            except:
                return norm_sym, None
            
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        future_to_sym = {executor.submit(fetch_single, norm): norm for norm in symbols_to_fetch}
        for future in concurrent.futures.as_completed(future_to_sym):
            norm_sym, data = future.result()
            if data:
                for orig_sym in unique_requests[norm_sym]:
                    results[orig_sym] = data
                
    return results


def _fetch_twelvedata_history(symbol, period, interval_yd, api_key):
    from datetime import datetime
    interval_map = {'5m': '5min', '15m': '15min', '1d': '1day', '1wk': '1week'}
    td_interval = interval_map.get(interval_yd, '1day')
    
    size_map = {'1d': 78, '5d': 130, '1w': 130, '1mo': 22, '3mo': 65, '6mo': 130, '1y': 252, '5y': 260, 'max': 500}
    outputsize = size_map.get(period, 30)

    td_sym = symbol
    exchange_param = ""
    if symbol.endswith('.NS'):
        td_sym = symbol[:-3]
        exchange_param = "&exchange=NSE"
    elif symbol.endswith('.BO'):
        td_sym = symbol[:-3]
        exchange_param = "&exchange=BSE"

    url = f"https://api.twelvedata.com/time_series?symbol={td_sym}{exchange_param}&interval={td_interval}&outputsize={outputsize}&apikey={api_key}"
    
    import requests
    response = requests.get(url, timeout=5)
    response.raise_for_status()
    data = response.json()
    
    if data.get('status') == 'error':
        err = data.get('message', '')
        if 'You have reached' in err or 'Rate limit' in err:
            raise Exception("429_TWELVEDATA")
        raise ValueError(f"TwelveData Error: {err}")
        
    values = data.get('values', [])
    if not values:
        raise ValueError("No historical data found from TwelveData.")
        
    values.reverse() # Newest first -> Oldest first for charts
    
    labels, timestamps, opens, highs, lows, closes, volumes = [], [], [], [], [], [], []
    
    for v in values:
        dt_str = v.get('datetime')
        try:
            if len(dt_str) > 10:
                dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
            else:
                dt = datetime.strptime(dt_str, "%Y-%m-%d")
        except:
            continue
            
        labels.append(dt.strftime('%Y-%m-%d'))
        timestamps.append(int(dt.timestamp()))
        opens.append(round(float(v.get('open', 0)), 2))
        highs.append(round(float(v.get('high', 0)), 2))
        lows.append(round(float(v.get('low', 0)), 2))
        closes.append(round(float(v.get('close', 0)), 2))
        volumes.append(int(v.get('volume', 0)))
        
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

def get_stock_history(symbol, period='1mo'):
    if not _check_yahoo_circuit():
        raise ValueError("Market history currently unavailable (Yahoo rate limited).")
        
    valid_periods = ['1d', '5d', '1w', '1mo', '3mo', '6mo', '1y', '5y', 'max']
    if period not in valid_periods:
        period = '1mo'
        
    interval = '1d'
    if period == '1d':
        interval = '5m'
    elif period == '1w' or period == '5d':
        period = '5d'
        interval = '15m'
    elif period in ['5y', 'max']:
        interval = '1wk'
        
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period, interval=interval)
        
        # If empty and symbol has no suffix, try searching for the correct suffix
        if hist.empty and '.' not in symbol:
            search_res = search_stocks(symbol)
            if search_res and search_res[0].get('symbol') != symbol:
                best_match = search_res[0].get('symbol')
                ticker = yf.Ticker(best_match)
                hist = ticker.history(period=period, interval=interval)

        # Ensure we don't send NaN values which break JSON and Lightweight Charts
        hist = hist.dropna(subset=['Open', 'High', 'Low', 'Close', 'Volume'])
        # Ensure timestamps are strictly unique and ascending (required by Lightweight Charts)
        hist = hist[~hist.index.duplicated(keep='first')]
        hist = hist.sort_index()
        
        
        if hist.empty:
            api_key = current_app.config.get('TWELVE_DATA_API_KEY')
            if api_key and api_key != 'your-twelvedata-api-key-here':
                try:
                    return _fetch_twelvedata_history(symbol, period, interval, api_key)
                except Exception as e:
                    current_app.logger.warning(f"TwelveData history fallback failed: {e}")
            raise ValueError("No historical data found.")

            
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


