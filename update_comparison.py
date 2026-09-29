import os

file_path = "app/templates/comparison.html"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace hardcoded dark card with theme-aware AI insight card
content = content.replace(
    '<div class="card border-0 bg-gradient-dark text-white rounded-4 shadow-sm premium-card">', 
    '<div class="card border-0 bg-info-subtle text-info-emphasis rounded-4 shadow-sm premium-card">'
)
content = content.replace(
    '<h5 class="fw-bold tracking-tight text-white mb-4"><i class="fa-solid fa-sparkles text-warning me-2"></i> AI Comparison Summary</h5>',
    '<h5 class="fw-bold tracking-tight mb-4"><i class="fa-solid fa-sparkles text-info me-2"></i> AI Comparison Summary</h5>'
)
content = content.replace(
    '<div id="aiSummary" class="markdown-body text-white opacity-90 lh-lg">',
    '<div id="aiSummary" class="markdown-body opacity-90 lh-lg">'
)
content = content.replace(
    '<div class="spinner-grow spinner-grow-sm text-warning" role="status"></div>',
    '<div class="spinner-grow spinner-grow-sm text-info" role="status"></div>'
)

# Also fix the stock cards which hardcode bg-body but that's fine, although premium-card should be used.
content = content.replace('<div class="card border-0 shadow-sm rounded-4 bg-body h-100">', '<div class="card border-0 shadow-sm rounded-4 premium-card h-100">')

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated comparison.html")
