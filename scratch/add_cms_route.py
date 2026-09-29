import os

file_path = 'app/routes/admin.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

cms_routes = '''
from app.models.finance import CMSContent

@bp.route('/cms', methods=['GET', 'POST'])
@admin_required
def cms():
    """Manage Homepage and General Content (CMS)."""
    if request.method == 'POST':
        # Safely handle form submission to update CMS values
        for key, value in request.form.items():
            if key.startswith('cms_'):
                db_key = key.replace('cms_', '', 1)
                item = CMSContent.query.filter_by(key=db_key).first()
                if item:
                    item.value = value
                    item.is_published = True
                else:
                    item = CMSContent(key=db_key, title=db_key.replace('_', ' ').title(), value=value, is_published=True)
                    db.session.add(item)
                
                # Log action
                log_admin_action('update_cms', 'cms_content', item.key, details=f'Updated CMS key: {item.key}')
        
        db.session.commit()
        flash('Content successfully updated and published to the website.', 'success')
        return redirect(url_for('admin.cms'))
        
    # Get all CMS items to display in the form
    cms_items = CMSContent.query.all()
    # Create a dictionary for easy template access
    cms_dict = {item.key: item.value for item in cms_items}
    
    return render_template('admin/cms.html', cms_dict=cms_dict)
'''

if "@bp.route('/cms'" not in content:
    content += cms_routes
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
