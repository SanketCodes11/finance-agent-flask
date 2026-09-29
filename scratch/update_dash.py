import os

with open('app/templates/admin/dashboard.html', 'r', encoding='utf-8') as f:
    content = f.read()

if 'fa-list-check me-1' not in content:
    content = content.replace('</a>', '</a>\n            <a href="{{ url_for(\'admin.activity\') }}" class="btn btn-outline-info ms-2">\n                <i class="fa-solid fa-list-check me-1"></i> Activity Logs\n            </a>', 1)
    
    with open('app/templates/admin/dashboard.html', 'w', encoding='utf-8') as f:
        f.write(content)
