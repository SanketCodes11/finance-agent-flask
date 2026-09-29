import os

file_path = 'app/routes/main.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('''@bp.route('/')
from app.models.finance import CMSContent
def index():''', '''from app.models.finance import CMSContent
@bp.route('/')
def index():''')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
