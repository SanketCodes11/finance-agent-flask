import os

file_path = 'app/templates/index.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

target1 = 'Smarter Investing with <span class="text-primary">AI Insights</span>'
rep1 = '{{ homepage_title|safe }}'

target2 = 'Finance Insight Agent combines real-time market data, comprehensive news analysis, and AI-driven insights to help you make informed financial decisions.'
rep2 = '{{ homepage_subtitle|safe }}'

content = content.replace(target1, rep1).replace(target2, rep2)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
