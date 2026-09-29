import re

file_path = "app/templates/admin/cms.html"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

target = """<a href="#" class="list-group-item list-group-item-action fw-medium py-3 text-muted disabled">
                    <i class="fa-solid fa-gears me-2"></i> Platform Settings <span class="badge bg-secondary float-end">Coming Soon</span>
                </a>"""
replacement = """<a href="{{ url_for('admin.settings') }}" class="list-group-item list-group-item-action fw-medium py-3 text-muted">
                    <i class="fa-solid fa-gears me-2"></i> Platform Settings
                </a>"""

content = content.replace(target, replacement)
with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated cms.html sidebar.")
