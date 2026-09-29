import os
import re

file_path = "app/templates/watchlist.html"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace all hardcoded dark theme classes with theme-aware ones
replacements = {
    'bg-dark': 'bg-body',
    'border-secondary': 'border-0 shadow-sm premium-card',
    'text-light': 'text-body',
    'text-secondary': 'text-muted',
    'bg-secondary bg-opacity-50': 'bg-secondary-subtle text-secondary',
    'bg-secondary bg-opacity-25': 'bg-secondary-subtle text-secondary',
    'bg-success bg-opacity-25': 'bg-success-subtle',
    'bg-danger bg-opacity-25': 'bg-danger-subtle',
    'btn-outline-danger': 'btn-light text-danger border-0',
    'btn-outline-info': 'btn-light text-info border-0',
    'btn-outline-primary': 'btn-light text-primary border-0',
    'table-dark': 'table-hover',
    'class="ps-4 text-light fw-bold"': 'class="ps-4 text-body fw-bold"',
}

for old, new in replacements.items():
    content = content.replace(old, new)

# Fix search input background
content = content.replace('bg-dark border-secondary text-light', 'bg-body-tertiary border-0 px-4')
content = content.replace('btn-outline-primary', 'btn-primary px-4 fw-medium shadow-sm')

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated watchlist.html")
