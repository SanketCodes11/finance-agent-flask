import re

file_path = 'app/api/finance.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

target = '''    try:
        history_data = get_stock_history(symbol, period)
        return jsonify(history_data)
    except Exception as e:'''

replacement = '''    try:
        history_data = get_stock_history(symbol, period)
        import logging
        logging.info(f"API /stock/history SUCCESS: symbol={symbol}, period={period}, candles={len(history_data.get('timestamps', []))}")
        return jsonify(history_data)
    except Exception as e:
        import logging
        logging.error(f"API /stock/history ERROR: symbol={symbol}, period={period}, error={str(e)}")'''

if target in content:
    content = content.replace(target, replacement)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fixed finance.py")
else:
    print("Target not found in finance.py")
