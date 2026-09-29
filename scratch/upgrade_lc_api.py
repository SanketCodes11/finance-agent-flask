import re

file_path = 'app/static/js/tv_chart.js'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

replacements = {
    r'\.addCandlestickSeries\(': '.addSeries(LightweightCharts.CandlestickSeries, ',
    r'\.addLineSeries\(': '.addSeries(LightweightCharts.LineSeries, ',
    r'\.addAreaSeries\(': '.addSeries(LightweightCharts.AreaSeries, ',
    r'\.addHistogramSeries\(': '.addSeries(LightweightCharts.HistogramSeries, '
}

for old_regex, new_text in replacements.items():
    content = re.sub(old_regex, new_text, content)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated tv_chart.js")
