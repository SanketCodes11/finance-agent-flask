import re

file_path = 'app/templates/stock_detail.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace everything from <h5 class="fw-bold tracking-tight mb-0">Historical Performance</h5> down to <canvas id="priceChart"></canvas> </div>
start_idx = content.find('<div class="d-flex justify-content-between align-items-center mb-4">')
end_idx = content.find('<canvas id="priceChart"></canvas>')

if start_idx != -1 and end_idx != -1:
    end_tag_idx = content.find('</div>', end_idx) + 6
    old_block = content[start_idx:end_tag_idx]
    
    new_block = '''<div class="d-flex flex-wrap justify-content-between align-items-center mb-4 gap-2">
                          <div class="d-flex align-items-center gap-2">
                              <h5 class="fw-bold tracking-tight mb-0 me-2">Historical Performance</h5>
                              
                              <div class="dropdown">
                                  <button class="btn btn-sm btn-light border rounded-pill fw-medium dropdown-toggle" type="button" data-bs-toggle="dropdown">
                                      <i class="fa-solid fa-chart-candlestick me-1"></i> <span id="chartTypeLabel">Candles</span>
                                  </button>
                                  <ul class="dropdown-menu dropdown-menu-sm shadow-sm border-0">
                                      <li><a class="dropdown-item chart-type-btn active" href="#" data-type="candle" data-label="Candles"><i class="fa-solid fa-chart-candlestick me-2 text-muted"></i>Candles</a></li>
                                      <li><a class="dropdown-item chart-type-btn" href="#" data-type="line" data-label="Line"><i class="fa-solid fa-chart-line me-2 text-muted"></i>Line</a></li>
                                      <li><a class="dropdown-item chart-type-btn" href="#" data-type="area" data-label="Area"><i class="fa-solid fa-chart-area me-2 text-muted"></i>Area</a></li>
                                  </ul>
                              </div>

                              <div class="dropdown">
                                  <button class="btn btn-sm btn-light border rounded-pill fw-medium dropdown-toggle" type="button" data-bs-toggle="dropdown" data-bs-auto-close="outside">
                                      <i class="fa-solid fa-chart-simple me-1"></i> Indicators
                                  </button>
                                  <div class="dropdown-menu dropdown-menu-sm shadow-sm border-0 p-3" style="width: 250px;">
                                      <h6 class="dropdown-header px-0 fw-bold">Overlays</h6>
                                      <div class="form-check form-switch mb-2">
                                          <input class="form-check-input ind-toggle" type="checkbox" role="switch" id="ind-sma20" data-ind="SMA" data-period="20">
                                          <label class="form-check-label small" for="ind-sma20">SMA (20)</label>
                                      </div>
                                      <div class="form-check form-switch mb-2">
                                          <input class="form-check-input ind-toggle" type="checkbox" role="switch" id="ind-sma50" data-ind="SMA" data-period="50">
                                          <label class="form-check-label small" for="ind-sma50">SMA (50)</label>
                                      </div>
                                      <div class="form-check form-switch mb-2">
                                          <input class="form-check-input ind-toggle" type="checkbox" role="switch" id="ind-ema20" data-ind="EMA" data-period="20">
                                          <label class="form-check-label small" for="ind-ema20">EMA (20)</label>
                                      </div>
                                      <div class="form-check form-switch mb-2">
                                          <input class="form-check-input ind-toggle" type="checkbox" role="switch" id="ind-bb" data-ind="BB" data-period="20" data-dev="2">
                                          <label class="form-check-label small" for="ind-bb">Bollinger Bands</label>
                                      </div>
                                      <div class="form-check form-switch mb-2">
                                          <input class="form-check-input ind-toggle" type="checkbox" role="switch" id="ind-vwap" data-ind="VWAP">
                                          <label class="form-check-label small" for="ind-vwap">VWAP</label>
                                      </div>
                                      
                                      <h6 class="dropdown-header px-0 fw-bold mt-3">Oscillators (Panes)</h6>
                                      <div class="form-check form-switch mb-2">
                                          <input class="form-check-input ind-toggle" type="checkbox" role="switch" id="ind-rsi" data-ind="RSI" data-period="14">
                                          <label class="form-check-label small" for="ind-rsi">RSI (14)</label>
                                      </div>
                                      <div class="form-check form-switch mb-2">
                                          <input class="form-check-input ind-toggle" type="checkbox" role="switch" id="ind-macd" data-ind="MACD" data-fast="12" data-slow="26" data-signal="9">
                                          <label class="form-check-label small" for="ind-macd">MACD (12, 26, 9)</label>
                                      </div>
                                  </div>
                              </div>
                          </div>

                          <div class="btn-group shadow-sm bg-body-tertiary rounded-pill p-1 flex-wrap" role="group">
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
                      
                      <div class="chart-container relative" style="height:450px; width:100%; border: 1px solid var(--bs-border-color); border-radius: 8px; overflow: hidden; position: relative;">
                          <div id="chartLoading" class="position-absolute top-50 start-50 translate-middle text-center d-none" style="z-index: 10;">
                              <div class="spinner-border text-primary" role="status"></div>
                          </div>
                          <div id="tvChart" style="width: 100%; height: 100%;"></div>
                      </div>'''
                      
    content = content.replace(old_block, new_block)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Replaced HTML block successfully.")
else:
    print("Could not find start or end index.")
