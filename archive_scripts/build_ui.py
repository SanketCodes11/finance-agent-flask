import os

base_dir = os.path.abspath('app/templates')

# Update base.html navigation
base_path = os.path.join(base_dir, 'base.html')
with open(base_path, 'r', encoding='utf-8') as f:
    base_html = f.read()

# Let's replace the navigation section in base.html
# We'll just write the full base.html navigation if we can, or we can use replace.
