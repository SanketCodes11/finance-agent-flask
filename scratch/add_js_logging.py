import re

file_path = 'app/templates/stock_detail.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

target = '''        fetch(`/api/stock/history?symbol=${SYMBOL}&period=${period}`)
            .then(res => res.json())
            .then(data => {'''

replace = '''        fetch(`/api/stock/history?symbol=${SYMBOL}&period=${period}`)
            .then(res => {
                console.log(`[API] /stock/history HTTP ${res.status}`);
                return res.json();
            })
            .then(data => {
                console.log(`[API] Response keys: ${Object.keys(data).join(', ')}`);
                if (data.timestamps) {
                    console.log(`[API] Candles received: ${data.timestamps.length}`);
                }'''

content = content.replace(target, replace)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Added JS logging")
