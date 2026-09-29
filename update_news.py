import os

file_path = "app/templates/news.html"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

replacements = {
    'bg-dark': 'bg-body',
    'border-secondary': 'border-0 premium-card shadow-sm',
    'text-light': 'text-body',
    'text-secondary': 'text-muted',
    'class="form-control bg-body border-0 premium-card shadow-sm text-body"': 'class="form-control bg-body-tertiary border-0 rounded-pill px-4"',
    '<span class="input-group-text bg-body border-0 premium-card shadow-sm text-muted">': '',
    '<i class="fa-solid fa-magnifying-glass" id="newsSearchIcon"></i>': '',
    '</span>': '',
    '<div class="input-group">': '<div class="input-group input-group-lg shadow-sm rounded-pill bg-body border">',
    'btn btn-primary': 'btn btn-primary rounded-pill px-4 m-1 fw-medium',
}

for old, new in replacements.items():
    content = content.replace(old, new)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated news.html")
