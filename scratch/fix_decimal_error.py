import os

file_path = 'app/api/paper_trading.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("except (ValueError, TypeError):", "except (ValueError, TypeError, __import__('decimal').InvalidOperation):")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
