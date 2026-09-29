import re

file_path = 'app/services/finance_service.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

target = '''        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period, interval=interval)
        
        if hist.empty:'''

replacement = '''        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period, interval=interval)
        
        # Ensure we don't send NaN values which break JSON and Lightweight Charts
        hist = hist.dropna(subset=['Open', 'High', 'Low', 'Close', 'Volume'])
        # Ensure timestamps are strictly unique and ascending (required by Lightweight Charts)
        hist = hist[~hist.index.duplicated(keep='first')]
        hist = hist.sort_index()
        
        if hist.empty:'''

if target in content:
    content = content.replace(target, replacement)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fixed finance_service.py")
else:
    print("Could not find target in finance_service.py")
