import re

file_path = "app/api/finance.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

target = "from app.models.finance import Watchlist, SearchHistory, PortfolioItem, Alert, PortfolioTransaction"
replacement = "from app.models.finance import Watchlist, SearchHistory, PortfolioItem, Alert, PortfolioTransaction, PlatformSetting"

if replacement not in content:
    content = content.replace(target, replacement)
    
with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Fixed finance.py import.")
