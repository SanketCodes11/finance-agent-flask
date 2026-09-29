import re

file_path = 'app/templates/stock_detail.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

target = '''<div id="chartLoading" class="position-absolute top-50 start-50 translate-middle text-center d-none" style="z-index: 10;">
                              <div class="spinner-border text-primary" role="status"></div>
                          </div>
                          <div id="tvChart" style="width: 100%; height: 100%;"></div>'''

replacement = '''<div id="chartLoading" class="position-absolute top-50 start-50 translate-middle text-center d-none" style="z-index: 10; background: var(--bs-body-bg); padding: 10px; border-radius: 8px;">
                              <div class="spinner-border text-primary mb-2" role="status"></div>
                              <div class="small fw-bold">Loading Data...</div>
                          </div>
                          <div id="chartError" class="position-absolute top-50 start-50 translate-middle text-center d-none" style="z-index: 10; background: var(--bs-body-bg); padding: 20px; border-radius: 8px; border: 1px solid var(--bs-border-color); width: 80%;">
                              <i class="fa-solid fa-triangle-exclamation text-danger fs-2 mb-3"></i>
                              <h6 class="fw-bold">Failed to load chart data</h6>
                              <p class="small text-muted mb-3" id="chartErrorText">No historical data available for this timeframe.</p>
                              <button class="btn btn-sm btn-primary px-4 rounded-pill" onclick="fetchChartData(document.querySelector('.range-btn.active')?.dataset.range || '1mo')">Retry</button>
                          </div>
                          <div id="tvChart" style="width: 100%; height: 100%;"></div>'''

if target in content:
    content = content.replace(target, replacement)
    
    # Also update fetchChartData to handle errors cleanly
    js_target = '''    function fetchChartData(period) {
        const loading = document.getElementById('chartLoading');
        if(loading) loading.classList.remove('d-none');
        
        fetch(`/api/stock/history?symbol=${SYMBOL}&period=${period}`)
            .then(res => res.json())
            .then(data => {
                if(loading) loading.classList.add('d-none');
                if (data.error) return;'''
    
    js_replace = '''    function fetchChartData(period) {
        const loading = document.getElementById('chartLoading');
        const errorDiv = document.getElementById('chartError');
        const errorText = document.getElementById('chartErrorText');
        const chartDiv = document.getElementById('tvChart');
        
        if(loading) loading.classList.remove('d-none');
        if(errorDiv) errorDiv.classList.add('d-none');
        if(chartDiv) chartDiv.style.opacity = '0.5';
        
        fetch(`/api/stock/history?symbol=${SYMBOL}&period=${period}`)
            .then(res => res.json())
            .then(data => {
                if(loading) loading.classList.add('d-none');
                
                if (data.error) {
                    if(errorText) errorText.textContent = data.error;
                    if(errorDiv) errorDiv.classList.remove('d-none');
                    return;
                }
                if (!data.timestamps || data.timestamps.length === 0) {
                    if(errorText) errorText.textContent = 'No historical data available for this timeframe.';
                    if(errorDiv) errorDiv.classList.remove('d-none');
                    return;
                }
                
                if(chartDiv) chartDiv.style.opacity = '1';'''
                
    content = content.replace(js_target, js_replace)
    
    # And update the catch block
    catch_target = '''            .catch(err => { 
                if(loading) loading.classList.add('d-none'); 
                console.error('Failed to load chart data:', err); 
            });'''
    catch_replace = '''            .catch(err => { 
                if(loading) loading.classList.add('d-none'); 
                if(errorText) errorText.textContent = err.message || 'Network error while fetching data.';
                if(errorDiv) errorDiv.classList.remove('d-none');
                console.error('Failed to load chart data:', err); 
            });'''
    content = content.replace(catch_target, catch_replace)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fixed stock_detail.html errors")
else:
    print("Could not find targets in HTML")
