import re

file_path = "app/routes/admin.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

import_target = "from app.models.finance import CMSContent, Watchlist, PortfolioItem"
import_replacement = "from app.models.finance import CMSContent, Watchlist, PortfolioItem, PlatformSetting"
content = content.replace(import_target, import_replacement)

settings_route = """
@bp.route('/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def settings():
    \"\"\"Global Platform Settings (Maintenance Mode, AI Toggle).\"\"\"
    settings = PlatformSetting.get_settings()
    
    if request.method == 'POST':
        # Check toggles
        maintenance = request.form.get('maintenance_mode') == 'on'
        ai_enabled = request.form.get('ai_analyst_enabled') == 'on'
        
        # Log if changed
        if settings.maintenance_mode != maintenance:
            log_admin_action('update_settings', 'platform_setting', str(settings.id), 
                             f'Maintenance Mode changed to {maintenance}')
        if settings.ai_analyst_enabled != ai_enabled:
            log_admin_action('update_settings', 'platform_setting', str(settings.id), 
                             f'AI Analyst globally changed to {ai_enabled}')
                             
        settings.maintenance_mode = maintenance
        settings.ai_analyst_enabled = ai_enabled
        db.session.commit()
        
        flash('Platform settings updated successfully.', 'success')
        return redirect(url_for('admin.settings'))
        
    return render_template('admin/settings.html', settings=settings)
"""

content += "\n" + settings_route + "\n"

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated admin.py with /settings route.")
