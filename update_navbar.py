import os

with open('app/templates/base.html', 'r', encoding='utf-8') as f:
    content = f.read()

target = """<li class="nav-item"><a class="nav-link px-3 {{ 'active text-primary' if request.endpoint == 'main.portfolio' else '' }}" href="{{ url_for('main.portfolio') }}">Portfolio</a></li>"""
replacement = target + """\n                        <li class="nav-item"><a class="nav-link px-3 {{ 'active text-primary' if request.endpoint == 'main.paper_trade' else '' }}" href="{{ url_for('main.paper_trade') }}">Paper Trading</a></li>"""

if "main.paper_trade" not in content:
    content = content.replace(target, replacement)
    with open('app/templates/base.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Updated base.html navbar")
else:
    print("Already updated")
