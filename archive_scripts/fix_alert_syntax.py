import os

path = os.path.abspath('app/api/finance.py')
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the broken replacements
content = content.replace("alerts = Alert, PortfolioTransaction.query", "alerts = Alert.query")
content = content.replace("new_alert = Alert, PortfolioTransaction(", "new_alert = Alert(")
content = content.replace("alert = Alert, PortfolioTransaction.query", "alert = Alert.query")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Fixed broken Alert syntax in finance.py")
