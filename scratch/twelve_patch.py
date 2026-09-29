import re

file_path = "app/services/finance_service.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

header = """import yfinance as yf
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
        result = _fetch_yahoo_quote(symbol)
        
    with QUOTE_CACHE_LOCK:
        QUOTE_CACHE[normalized_symbol] = (result, time.time())
        
    return result
"""

# Replace the beginning of the file up to get_multiple_stock_quotes
start_marker = "import yfinance as yf"
end_marker = "def get_multiple_stock_quotes(symbols):"

content = content[:content.find(start_marker)] + header + "\n" + content[content.find(end_marker):]

# Add Yahoo Circuit breaker to get_stock_history
old_history = """def get_stock_history(symbol, period='1mo'):
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
        ticker = yf.Ticker(symbol)"""

new_history = """def get_stock_history(symbol, period='1mo'):
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
        ticker = yf.Ticker(symbol)"""

content = content.replace(old_history, new_history)

# Also handle 429 in get_stock_history
old_hist_except = """    except Exception as e:
        raise ValueError(f"Failed to fetch history for {symbol}: {str(e)}")"""

new_hist_except = """    except Exception as e:
        err_msg = str(e).lower()
        if '429' in err_msg or 'too many requests' in err_msg:
            _trip_yahoo_circuit()
            raise ValueError("Market history currently unavailable (Yahoo rate limited).")
        raise ValueError(f"Failed to fetch history for {symbol}: {str(e)}")"""
        
content = content.replace(old_hist_except, new_hist_except)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Twelve Data implementation complete.")
