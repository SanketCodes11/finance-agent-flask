import re

file_path = "app/api/finance.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

import_target = "from app.models.finance import Watchlist, StockCache"
import_replacement = "from app.models.finance import Watchlist, StockCache, PlatformSetting"
content = content.replace(import_target, import_replacement)

# Update ask_agent
ask_target = """@bp.route('/agent/ask', methods=['POST'])
@login_required
def ask_agent():
    data = request.get_json()"""
ask_replacement = """@bp.route('/agent/ask', methods=['POST'])
@login_required
def ask_agent():
    settings = PlatformSetting.get_settings()
    if not settings.ai_analyst_enabled and not current_user.is_admin:
        return jsonify({'error': 'AI Analyst is temporarily disabled by the administrator. Please check back later.'}), 403

    data = request.get_json()"""
content = content.replace(ask_target, ask_replacement)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated finance.py to check ai_analyst_enabled toggle.")
