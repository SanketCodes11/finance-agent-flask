import re

file_path = "app/routes/main.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Add the import and before_app_request
import_target = "from app.models.finance import Watchlist, SearchHistory"
import_replacement = "from app.models.finance import Watchlist, SearchHistory, PlatformSetting\nfrom flask import request, jsonify"
content = content.replace(import_target, import_replacement)

before_request = """
@bp.before_app_request
def check_maintenance_mode():
    # Allow static files and health checks
    if request.endpoint and request.endpoint.startswith('static'):
        return
    if request.path == '/health':
        return
        
    try:
        settings = PlatformSetting.get_settings()
        if settings.maintenance_mode:
            # Allow admins to bypass
            if current_user.is_authenticated and current_user.is_admin:
                return
            
            # Allow auth endpoints (so admins can login)
            if request.endpoint and request.endpoint.startswith('auth.'):
                return
                
            # Allow admin endpoints
            if request.endpoint and request.endpoint.startswith('admin.'):
                return
                
            if request.path.startswith('/api/'):
                return jsonify({"error": "Platform is under maintenance. Please try again later."}), 503
            
            return render_template('errors/maintenance.html'), 503
    except Exception:
        # DB might not be initialized during initial setup/migration
        pass
"""

# Insert after bp = Blueprint('main', __name__)
target = "bp = Blueprint('main', __name__)"
content = content.replace(target, target + "\n\n" + before_request)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated main.py with maintenance mode check.")
