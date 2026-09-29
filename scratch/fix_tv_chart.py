import re

file_path = 'app/static/js/tv_chart.js'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix clientWidth 0 issues
target1 = '''        const chartOptions = {
            width: this.container.clientWidth,
            height: 400,'''
replace1 = '''        const initialWidth = this.container.clientWidth > 0 ? this.container.clientWidth : (this.container.parentElement ? this.container.parentElement.clientWidth : 800);
        const chartOptions = {
            width: initialWidth,
            height: 400,'''
content = content.replace(target1, replace1)

target2 = '''this.chart.applyOptions({ width: this.container.clientWidth });'''
replace2 = '''this.chart.applyOptions({ width: this.container.clientWidth > 0 ? this.container.clientWidth : 800 });'''
content = content.replace(target2, replace2)

target3 = '''p.chart.applyOptions({ width: this.container.clientWidth });'''
replace3 = '''p.chart.applyOptions({ width: this.container.clientWidth > 0 ? this.container.clientWidth : 800 });'''
content = content.replace(target3, replace3)

# Add fitContent() in setData
target4 = '''        if (chartType === 'area') {
            this.volumeSeries.setData(volumeData);
        }'''
replace4 = '''        if (chartType === 'area') {
            this.volumeSeries.setData(volumeData);
        }
        
        // Ensure chart auto-scales to fit the newly added data
        setTimeout(() => {
            if(this.chart && this.chart.timeScale) {
                this.chart.timeScale().fitContent();
            }
        }, 50);'''
content = content.replace(target4, replace4)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Fixed tv_chart.js")
