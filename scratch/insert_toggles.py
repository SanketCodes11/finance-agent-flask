import re

file_path = 'app/templates/stock_detail.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

if 'id="ind-rsi"' not in content:
    target = 'id="ind-vwap" data-ind="VWAP">\n                                          <label class="form-check-label small" for="ind-vwap">VWAP</label>\n                                      </div>'
    replacement = target + '''
                                      <h6 class="dropdown-header px-0 fw-bold mt-3">Oscillators (Panes)</h6>
                                      <div class="form-check form-switch mb-2">
                                          <input class="form-check-input ind-toggle" type="checkbox" role="switch" id="ind-rsi" data-ind="RSI" data-period="14">
                                          <label class="form-check-label small" for="ind-rsi">RSI (14)</label>
                                      </div>
                                      <div class="form-check form-switch mb-2">
                                          <input class="form-check-input ind-toggle" type="checkbox" role="switch" id="ind-macd" data-ind="MACD" data-fast="12" data-slow="26" data-signal="9">
                                          <label class="form-check-label small" for="ind-macd">MACD (12, 26, 9)</label>
                                      </div>'''
    
    content = content.replace(target, replacement)

    # I also need to update applyActiveIndicators to pass fast/slow/signal for MACD
    target_js = 'if (cb.dataset.dev) params.stdDev = parseFloat(cb.dataset.dev);'
    replacement_js = target_js + '''
            if (cb.dataset.fast) params.fast = parseInt(cb.dataset.fast);
            if (cb.dataset.slow) params.slow = parseInt(cb.dataset.slow);
            if (cb.dataset.signal) params.signal = parseInt(cb.dataset.signal);'''
    content = content.replace(target_js, replacement_js)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
