import os

file_path = "app/templates/news.html"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Fix searchIcon issue and hardcoded bg-secondary bg-opacity-25
content = content.replace("searchIcon.className = 'fa-solid fa-spinner fa-spin text-primary';", "if(searchIcon) searchIcon.className = 'fa-solid fa-spinner fa-spin text-primary';")
content = content.replace("searchIcon.className = 'fa-solid fa-magnifying-glass';", "if(searchIcon) searchIcon.className = 'fa-solid fa-magnifying-glass';")
content = content.replace('bg-secondary bg-opacity-25', 'bg-secondary-subtle')

# Fix unclosed span bug from original template
content = content.replace('<span id="currentQueryText" class="text-primary"></h5>', '<span id="currentQueryText" class="text-primary"></span></h5>')
content = content.replace('<span class="badge bg-primary text-truncate" style="max-width: 60%;">${article.source}', '<span class="badge bg-primary-subtle text-primary text-truncate" style="max-width: 60%;">${article.source}</span>')
content = content.replace('btn-outline-primary', 'btn-light text-primary fw-medium border')

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Fixed news.html JS")
