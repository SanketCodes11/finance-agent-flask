import re

file_path = 'app/templates/stock_detail.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

target = '''    function generateAIAnalysis(name, stockData) {
        const container = document.getElementById('aiAnalysisContainer');
        const query = `Analyze the stock ${name} (${SYMBOL}). Current Price: ${stockData.price}, 52W Range: ${stockData.fiftyTwoWeekLow}-${stockData.fiftyTwoWeekHigh}, Market Cap: ${formatNumber(stockData.market_cap)}. Keep the analysis highly concise, structured with short bullet points, professional, and focus on general market positioning. Do not give financial advice.`;
        
        fetch('/api/agent/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content') },
            body: JSON.stringify({ query: query, history: [] })
        }).then(res => res.json()).then(data => {
            if (data.error) {
                container.innerHTML = `<div class="text-white-50"><i class="fa-solid fa-triangle-exclamation me-2"></i> ${data.error}</div>`;
            } else {
                const parsedMarkdown = typeof marked !== 'undefined' ? marked.parse(data.response) : data.response.replace(/\\n/g, '<br>');
                container.innerHTML = parsedMarkdown;
            }
        }).catch(err => {
            container.innerHTML = `<div class="text-white-50"><i class="fa-solid fa-circle-exclamation me-2"></i> AI Analysis is currently unavailable.</div>`;
        });
    }'''

replace = '''    function generateAIAnalysis(name, stockData) {
        // Save globally for retry button
        window.lastAiName = name;
        window.lastAiStockData = stockData;
        
        const container = document.getElementById('aiAnalysisContainer');
        container.innerHTML = '<div class="text-white-50"><i class="fa-solid fa-circle-notch fa-spin me-2"></i> Generating analysis...</div>';
        
        const query = `Analyze the stock ${name} (${SYMBOL}). Current Price: ${stockData.price}, 52W Range: ${stockData.fiftyTwoWeekLow}-${stockData.fiftyTwoWeekHigh}, Market Cap: ${formatNumber(stockData.market_cap)}. Keep the analysis highly concise, structured with short bullet points, professional, and focus on general market positioning. Do not give financial advice.`;
        
        fetch('/api/agent/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content') },
            body: JSON.stringify({ query: query, history: [] })
        }).then(res => res.json()).then(data => {
            if (data.error) {
                let html = `<div class="text-white-50 mb-2"><i class="fa-solid fa-triangle-exclamation me-2"></i> ${data.error}</div>`;
                // Add retry button if it is a temporary error (not quota or invalid key)
                if (data.error.includes("high demand") || data.error.includes("temporary timeout") || data.error.includes("unexpected provider error")) {
                    html += `<button class="btn btn-sm btn-outline-light mt-2" onclick="generateAIAnalysis(window.lastAiName, window.lastAiStockData)"><i class="fa-solid fa-rotate-right me-1"></i> Retry</button>`;
                }
                container.innerHTML = html;
            } else {
                const parsedMarkdown = typeof marked !== 'undefined' ? marked.parse(data.response) : data.response.replace(/\\n/g, '<br>');
                container.innerHTML = parsedMarkdown;
            }
        }).catch(err => {
            container.innerHTML = `
                <div class="text-white-50 mb-2"><i class="fa-solid fa-circle-exclamation me-2"></i> AI Analysis is currently unavailable. (Network error)</div>
                <button class="btn btn-sm btn-outline-light mt-2" onclick="generateAIAnalysis(window.lastAiName, window.lastAiStockData)"><i class="fa-solid fa-rotate-right me-1"></i> Retry</button>
            `;
        });
    }'''

content = content.replace(target, replace)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Fixed stock_detail.html generateAIAnalysis")
