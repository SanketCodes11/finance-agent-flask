import os

file_path = "app/templates/tools.html"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace col-md-6 with col-lg-4 so all three can fit in one row on large screens
content = content.replace('col-md-6', 'col-lg-4 col-md-6')

trade_pl_html = """
        <!-- Trade P/L Calculator -->
        <div class="col-lg-4 col-md-6">
            <div class="card border-0 shadow-sm rounded-4 premium-card h-100">
                <div class="card-body p-4">
                    <h5 class="fw-bold mb-4"><i class="fa-solid fa-scale-balanced text-info me-2"></i> Trade P/L Calculator</h5>
                    
                    <div class="row g-2 mb-3">
                        <div class="col-6">
                            <label class="form-label text-muted small">Buy Price</label>
                            <input type="number" id="tradeBuy" class="form-control bg-body-tertiary border-0 rounded-pill px-3" placeholder="0.00" min="0">
                        </div>
                        <div class="col-6">
                            <label class="form-label text-muted small">Sell Price</label>
                            <input type="number" id="tradeSell" class="form-control bg-body-tertiary border-0 rounded-pill px-3" placeholder="0.00" min="0">
                        </div>
                    </div>

                    <div class="mb-3">
                        <label class="form-label text-muted small">Quantity</label>
                        <input type="number" id="tradeQty" class="form-control bg-body-tertiary border-0 rounded-pill px-3" placeholder="1" min="1">
                    </div>
                    
                    <div class="row g-2 mb-4">
                        <div class="col-6">
                            <label class="form-label text-muted small">Buy Charges</label>
                            <input type="number" id="tradeBuyCharges" class="form-control bg-body-tertiary border-0 rounded-pill px-3" value="0" min="0">
                        </div>
                        <div class="col-6">
                            <label class="form-label text-muted small">Sell Charges</label>
                            <input type="number" id="tradeSellCharges" class="form-control bg-body-tertiary border-0 rounded-pill px-3" value="0" min="0">
                        </div>
                    </div>
                    
                    <button class="btn btn-info text-white rounded-pill w-100 fw-medium shadow-sm mb-4" onclick="calculateTradePL()">Calculate</button>
                    
                    <div id="tradeResultBox" class="p-3 bg-secondary-subtle text-secondary-emphasis rounded-4 text-center">
                        <p class="mb-1 small">Net P/L</p>
                        <h3 class="fw-bold mb-2" id="tradeNetPL">0.00</h3>
                        <div class="d-flex justify-content-between small text-muted px-2">
                            <span>Ret: <span id="tradeReturn" class="fw-bold">0.00%</span></span>
                            <span>Charges: <span id="tradeTotalCharges" class="fw-bold">0.00</span></span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
"""

# Insert before the end of the row
content = content.replace('    </div>\n</div>\n{% endblock %}', trade_pl_html + '    </div>\n</div>\n{% endblock %}')

js_html = """
function calculateTradePL() {
    const buyPrice = Math.max(0, parseFloat(document.getElementById('tradeBuy').value) || 0);
    const sellPrice = Math.max(0, parseFloat(document.getElementById('tradeSell').value) || 0);
    const qty = Math.max(1, parseFloat(document.getElementById('tradeQty').value) || 0);
    const buyCharges = Math.max(0, parseFloat(document.getElementById('tradeBuyCharges').value) || 0);
    const sellCharges = Math.max(0, parseFloat(document.getElementById('tradeSellCharges').value) || 0);
    
    if (buyPrice > 0 && qty > 0) {
        const buyValue = buyPrice * qty;
        const sellValue = sellPrice * qty;
        const totalCharges = buyCharges + sellCharges;
        
        const netPL = sellValue - buyValue - totalCharges;
        const totalInvestment = buyValue + buyCharges;
        const returnPct = totalInvestment > 0 ? (netPL / totalInvestment) * 100 : 0;
        
        const resultBox = document.getElementById('tradeResultBox');
        const netPlElem = document.getElementById('tradeNetPL');
        const returnElem = document.getElementById('tradeReturn');
        
        netPlElem.textContent = netPL.toFixed(2);
        returnElem.textContent = returnPct.toFixed(2) + '%';
        document.getElementById('tradeTotalCharges').textContent = totalCharges.toFixed(2);
        
        if (netPL > 0) {
            resultBox.className = 'p-3 bg-success-subtle text-success-emphasis rounded-4 text-center';
            netPlElem.className = 'fw-bold mb-2 text-success';
            returnElem.className = 'fw-bold text-success';
        } else if (netPL < 0) {
            resultBox.className = 'p-3 bg-danger-subtle text-danger-emphasis rounded-4 text-center';
            netPlElem.className = 'fw-bold mb-2 text-danger';
            returnElem.className = 'fw-bold text-danger';
        } else {
            resultBox.className = 'p-3 bg-secondary-subtle text-secondary-emphasis rounded-4 text-center';
            netPlElem.className = 'fw-bold mb-2';
            returnElem.className = 'fw-bold';
        }
    }
}
</script>"""

content = content.replace('</script>', js_html)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated tools.html with Trade P/L Calculator.")
