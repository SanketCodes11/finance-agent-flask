import os

file_path = 'app/templates/stock_detail.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace block with new chart toolbar and container
target_html_block = '''                      <div class="d-flex justify-content-between align-items-center mb-4">
                          <h5 class="fw-bold tracking-tight mb-0">Historical Performance</h5>
                          <div class="btn-group shadow-sm bg-body-tertiary rounded-pill p-1" role="group">
                              <button type="button" class="btn btn-sm rounded-pill px-3 range-btn text-muted fw-medium border-0" data-range="5d">1W</button>
                              <button type="button" class="btn btn-sm rounded-pill px-3 range-btn text-muted fw-medium border-0 active bg-primary text-white shadow-sm" data-range="1mo">1M</button>
                              <button type="button" class="btn btn-sm rounded-pill px-3 range-btn text-muted fw-medium border-0" data-range="3mo">3M</button>
                              <button type="button" class="btn btn-sm rounded-pill px-3 range-btn text-muted fw-medium border-0" data-range="6mo">6M</button>
                              <button type="button" class="btn btn-sm rounded-pill px-3 range-btn text-muted fw-medium border-0" data-range="1y">1Y</button>
                          </div>
                      </div>
                      
                      <div class="chart-container relative" style="height:400px; width:100%">
                          <div id="chartLoading" class="position-absolute top-50 start-50 translate-middle text-center d-none z-index-1">
                              <div class="spinner-border text-primary" role="status"></div>
                          </div>
                          <canvas id="priceChart"></canvas>
                      </div>'''

replace_html_block = '''                      <div class="d-flex flex-wrap justify-content-between align-items-center mb-4 gap-2">
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

if 'id="tvChart"' not in content:
    content = content.replace(target_html_block, replace_html_block)

    # Now add scripts
    scripts_insertion = '''    <script src="https://unpkg.com/lightweight-charts/dist/lightweight-charts.standalone.production.js"></script>
    <script src="{{ url_for('static', filename='js/indicators.js') }}"></script>
    <script src="{{ url_for('static', filename='js/tv_chart.js') }}"></script>
    <script>
        const SYMBOL = '{{ symbol }}';
        let tvChartMgr = null;
        let currentChartType = 'candle';
        let rawChartData = null;'''

    content = content.replace('''  <script>
      const SYMBOL = '{{ symbol }}';
      let chartInstance = null;''', scripts_insertion)

    
    fetch_chart_func = '''    function fetchChartData(period) {
        const loading = document.getElementById('chartLoading');
        loading.classList.remove('d-none');
        
        fetch(`/api/stock/history?symbol=${SYMBOL}&period=${period}`)
            .then(res => res.json())
            .then(data => {
                loading.classList.add('d-none');
                if (data.error) return;
                
                // Format for Lightweight Charts
                const formattedData = [];
                for(let i=0; i<data.timestamps.length; i++) {
                    formattedData.push({
                        time: data.timestamps[i],
                        open: data.open[i],
                        high: data.high[i],
                        low: data.low[i],
                        close: data.close[i],
                        volume: data.volume[i]
                    });
                }
                
                // Sort ascending just in case
                formattedData.sort((a,b) => a.time - b.time);
                rawChartData = formattedData;
                
                const isDark = document.documentElement.getAttribute('data-bs-theme') === 'dark' || (document.documentElement.getAttribute('data-bs-theme') === 'auto' && window.matchMedia('(prefers-color-scheme: dark)').matches);
                
                if (!tvChartMgr) {
                    tvChartMgr = new TVChart('tvChart', isDark);
                } else {
                    tvChartMgr.setTheme(isDark);
                }
                
                tvChartMgr.setData(formattedData, currentChartType);
                applyActiveIndicators();
            })
            .catch(err => { loading.classList.add('d-none'); console.error(err); });
    }

    function applyActiveIndicators() {
        if (!tvChartMgr) return;
        tvChartMgr.clearIndicators();
        document.querySelectorAll('.ind-toggle:checked').forEach(cb => {
            const ind = cb.dataset.ind;
            const params = {};
            if (cb.dataset.period) params.period = parseInt(cb.dataset.period);
            if (cb.dataset.dev) params.stdDev = parseFloat(cb.dataset.dev);
            tvChartMgr.addIndicator(ind, params);
        });
    }

    // Bind indicator toggles
    document.querySelectorAll('.ind-toggle').forEach(cb => {
        cb.addEventListener('change', applyActiveIndicators);
    });

    // Bind Chart Type toggles
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

    # Remove the old renderChart and its calls
    import re
    content = re.sub(r'function fetchChartData\(period\) \{[\s\S]*?function renderChart\(labels, data\) \{[\s\S]*?\}\s*\}\s*\}\);', fetch_chart_func, content)
    
    # Also fix the bd-theme listener
    content = content.replace('''    document.getElementById('bd-theme').addEventListener('click', () => {
        if (chartInstance) {
            setTimeout(() => {
                const activeRange = document.querySelector('.range-btn.active').dataset.range;
                fetchChartData(activeRange);
            }, 100);
        }
    });''', '''    document.getElementById('bd-theme').addEventListener('click', () => {
        if (tvChartMgr) {
            setTimeout(() => {
                const isDark = document.documentElement.getAttribute('data-bs-theme') === 'dark' || (document.documentElement.getAttribute('data-bs-theme') === 'auto' && window.matchMedia('(prefers-color-scheme: dark)').matches);
                tvChartMgr.setTheme(isDark);
            }, 100);
        }
    });''')

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
