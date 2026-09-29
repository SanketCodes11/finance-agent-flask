import re

file_path = "app/services/finance_service.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Add imports and cache vars
header = """import yfinance as yf
import requests
from flask import current_app
import time
import threading

QUOTE_CACHE = {}
QUOTE_CACHE_LOCK = threading.Lock()
QUOTE_CACHE_TTL = 300  # 5 minutes
"""
content = re.sub(r"^import yfinance as yf\nimport requests\nfrom flask import current_app\n", header, content, count=1)

# Modify get_stock_quote
old_quote = """def get_stock_quote(symbol):
    try:"""
new_quote = """def get_stock_quote(symbol):
    if not symbol:
        raise ValueError("Symbol is required")
        
    normalized_symbol = symbol.upper().strip()
    current_time = time.time()
    
    with QUOTE_CACHE_LOCK:
        if normalized_symbol in QUOTE_CACHE:
            data, timestamp = QUOTE_CACHE[normalized_symbol]
            if current_time - timestamp < QUOTE_CACHE_TTL:
                return data

    try:"""
content = content.replace(old_quote, new_quote)

# Modify the return of get_stock_quote to save to cache
old_return = """            'market_cap': info.get('marketCap', fast_info.get('marketCap', 0)),
            'description': info.get('longBusinessSummary', 'Description unavailable.')
        }
    except Exception as e:"""
new_return = """            'market_cap': info.get('marketCap', fast_info.get('marketCap', 0)),
            'description': info.get('longBusinessSummary', 'Description unavailable.')
        }
        
        with QUOTE_CACHE_LOCK:
            QUOTE_CACHE[normalized_symbol] = (result, time.time())
            
        return result
    except Exception as e:"""
content = content.replace(old_return, new_return)

# Modify the assignment to return
# In the original code, it was returning the dict directly: `return { 'symbol': symbol, ... }`
# I need to change that to `result = { ... }` so I can cache it.
old_return_dict = """        return {
            'symbol': symbol,"""
new_return_dict = """        result = {
            'symbol': symbol,"""
content = content.replace(old_return_dict, new_return_dict)


# Modify get_multiple_stock_quotes
old_multi = """def get_multiple_stock_quotes(symbols):
    if not symbols:
        return {}
    
    results = {}
    import concurrent.futures
    
    def fetch_single(sym):
        try:
            return sym, get_stock_quote(sym)
        except:
            return sym, None
            
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_sym = {executor.submit(fetch_single, sym): sym for sym in symbols}
        for future in concurrent.futures.as_completed(future_to_sym):
            sym, data = future.result()
            if data:
                results[sym] = data
                
    return results"""

new_multi = """def get_multiple_stock_quotes(symbols):
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
        
    def fetch_single(norm_sym):
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
                
    return results"""
content = content.replace(old_multi, new_multi)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Patched finance_service.py")
