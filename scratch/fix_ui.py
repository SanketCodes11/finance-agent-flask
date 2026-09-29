import re

file_path = 'app/templates/stock_detail.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

start_idx = content.find('<div class="d-flex flex-wrap justify-content-between align-items-center mb-4 gap-2">')
end_idx = content.find('<div class="chart-container relative"')

if start_idx != -1 and end_idx != -1:
    old_block = content[start_idx:end_idx]
    
    new_block = '''<div class="d-flex flex-wrap justify-content-between align-items-center mb-4 gap-3">
                          <div class="d-flex align-items-center flex-wrap gap-3">
                              <h5 class="fw-bold tracking-tight mb-0 me-2 d-none d-md-block">Historical Performance</h5>
                              
                              <div class="btn-group shadow-sm bg-body-tertiary rounded-pill p-1 flex-wrap" role="group">
                                  <button type="button" class="btn btn-sm rounded-pill px-3 chart-type-btn text-muted fw-medium border-0 active bg-primary text-white shadow-sm" data-type="candle"><i class="fa-solid fa-chart-candlestick d-none d-sm-inline me-1"></i>Candles</button>
                                  <button type="button" class="btn btn-sm rounded-pill px-3 chart-type-btn text-muted fw-medium border-0" data-type="line"><i class="fa-solid fa-chart-line d-none d-sm-inline me-1"></i>Line</button>
                                  <button type="button" class="btn btn-sm rounded-pill px-3 chart-type-btn text-muted fw-medium border-0" data-type="area"><i class="fa-solid fa-chart-area d-none d-sm-inline me-1"></i>Area</button>
                              </div>

                              <div class="dropdown">
                                  <button class="btn btn-sm btn-light border rounded-pill fw-medium dropdown-toggle shadow-sm" type="button" data-bs-toggle="dropdown" data-bs-auto-close="outside">
                                      <i class="fa-solid fa-chart-simple me-1 text-primary"></i> Indicators
                                  </button>
                                  <div class="dropdown-menu dropdown-menu-sm shadow border-0 p-3" style="width: 250px;">
                                      <h6 class="dropdown-header px-0 fw-bold">Overlays</h6>
                                      <div class="form-check form-switch mb-2">
                                          <input class="form-check-input ind-toggle" type="checkbox" role="switch" id="ind-sma20" data-ind="SMA" data-period="20">
                                          <label class="form-check-label small text-body" for="ind-sma20">SMA (20)</label>
                                      </div>
                                      <div class="form-check form-switch mb-2">
                                          <input class="form-check-input ind-toggle" type="checkbox" role="switch" id="ind-sma50" data-ind="SMA" data-period="50">
                                          <label class="form-check-label small text-body" for="ind-sma50">SMA (50)</label>
                                      </div>
                                      <div class="form-check form-switch mb-2">
                                          <input class="form-check-input ind-toggle" type="checkbox" role="switch" id="ind-ema20" data-ind="EMA" data-period="20">
                                          <label class="form-check-label small text-body" for="ind-ema20">EMA (20)</label>
                                      </div>
                                      <div class="form-check form-switch mb-2">
                                          <input class="form-check-input ind-toggle" type="checkbox" role="switch" id="ind-bb" data-ind="BB" data-period="20" data-dev="2">
                                          <label class="form-check-label small text-body" for="ind-bb">Bollinger Bands</label>
                                      </div>
                                      <div class="form-check form-switch mb-2">
                                          <input class="form-check-input ind-toggle" type="checkbox" role="switch" id="ind-vwap" data-ind="VWAP">
                                          <label class="form-check-label small text-body" for="ind-vwap">VWAP</label>
                                      </div>
                                      
                                      <h6 class="dropdown-header px-0 fw-bold mt-3 border-top pt-2">Oscillators (Panes)</h6>
                                      <div class="form-check form-switch mb-2">
                                          <input class="form-check-input ind-toggle" type="checkbox" role="switch" id="ind-rsi" data-ind="RSI" data-period="14">
                                          <label class="form-check-label small text-body" for="ind-rsi">RSI (14)</label>
                                      </div>
                                      <div class="form-check form-switch mb-2">
                                          <input class="form-check-input ind-toggle" type="checkbox" role="switch" id="ind-macd" data-ind="MACD" data-fast="12" data-slow="26" data-signal="9">
                                          <label class="form-check-label small text-body" for="ind-macd">MACD (12, 26, 9)</label>
                                      </div>
                                  </div>
                              </div>
                          </div>

                          <div class="btn-group shadow-sm bg-body-tertiary rounded-pill p-1 flex-wrap ms-auto" role="group">
                              <button type="button" class="btn btn-sm rounded-pill px-2 range-btn text-muted fw-medium border-0" data-range="1d">1D</button>
                              <button type="button" class="btn btn-sm rounded-pill px-2 range-btn text-muted fw-medium border-0" data-range="1w">1W</button>
                              <button type="button" class="btn btn-sm rounded-pill px-2 range-btn text-muted fw-medium border-0 active bg-primary text-white shadow-sm" data-range="1mo">1M</button>
                              <button type="button" class="btn btn-sm rounded-pill px-2 range-btn text-muted fw-medium border-0" data-range="3mo">3M</button>
                              <button type="button" class="btn btn-sm rounded-pill px-2 range-btn text-muted fw-medium border-0" data-range="6mo">6M</button>
                              <button type="button" class="btn btn-sm rounded-pill px-2 range-btn text-muted fw-medium border-0" data-range="1y">1Y</button>
                              <button type="button" class="btn btn-sm rounded-pill px-2 range-btn text-muted fw-medium border-0" data-range="5y">5Y</button>
                              <button type="button" class="btn btn-sm rounded-pill px-2 range-btn text-muted fw-medium border-0" data-range="max">MAX</button>
                          </div>
                      </div>
                      
                      '''
    
    content = content.replace(old_block, new_block)
    
    # Let's ensure the JS script for chart type buttons is updated to match the new button structure
    # Previously it updated document.getElementById('chartTypeLabel').textContent = this.dataset.label;
    # Now they are just a button group, so they behave like the range buttons.
    old_js_chart_btn = '''        // Chart Type toggles
        document.querySelectorAll('.chart-type-btn').forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                document.querySelectorAll('.chart-type-btn').forEach(b => b.classList.remove('active'));
                this.classList.add('active');
                currentChartType = this.dataset.type;
                document.getElementById('chartTypeLabel').textContent = this.dataset.label;
                
                if (tvChartMgr && rawChartData) {
                    tvChartMgr.setData(rawChartData, currentChartType);
                    applyActiveIndicators();
                }
            });
        });'''
    new_js_chart_btn = '''        // Chart Type toggles
        document.querySelectorAll('.chart-type-btn').forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                document.querySelectorAll('.chart-type-btn').forEach(b => {
                    b.classList.remove('bg-primary', 'text-white', 'shadow-sm', 'active');
                    b.classList.add('text-muted');
                });
                this.classList.remove('text-muted');
                this.classList.add('bg-primary', 'text-white', 'shadow-sm', 'active');
                
                currentChartType = this.dataset.type;
                
                if (tvChartMgr && rawChartData) {
                    tvChartMgr.setData(rawChartData, currentChartType);
                    applyActiveIndicators();
                }
            });
        });'''
    content = content.replace(old_js_chart_btn, new_js_chart_btn)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("UI fixed successfully.")
else:
    print("Could not find blocks.")
