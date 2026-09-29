import os

with open('app/templates/base.html', 'r', encoding='utf-8') as f:
    content = f.read()

target = '<li><a class="dropdown-item" href="{{ url_for(\'main.reports\') }}">Reports</a></li>'
replacement = '<li><a class="dropdown-item fw-medium text-primary" href="{{ url_for(\'main.screener\') }}"><i class="fa-solid fa-filter me-2"></i>Stock Screener</a></li>\n                                  ' + target

if 'main.screener' not in content:
    content = content.replace(target, replacement)
    with open('app/templates/base.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Added screener to base.html")
