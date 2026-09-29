import os

init_path = 'app/__init__.py'
with open(init_path, 'r', encoding='utf-8') as f:
    content = f.read()

target = 'from app.routes.admin_db import bp as admin_db_bp'
replacement = '''from app.routes.admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    from app.routes.admin_db import bp as admin_db_bp'''

if 'from app.routes.admin import bp as admin_bp' not in content:
    content = content.replace(target, replacement)
    with open(init_path, 'w', encoding='utf-8') as f:
        f.write(content)
