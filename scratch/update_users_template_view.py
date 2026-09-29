import os

file_path = 'app/templates/admin/users.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

target = '''<div class="d-flex justify-content-end gap-2">'''
replacement = '''<div class="d-flex justify-content-end gap-2">
                                    <a href="{{ url_for('admin.user_detail', user_id=u.id) }}" class="btn btn-sm btn-outline-info" title="View 360 Profile">
                                        <i class="fa-solid fa-eye"></i>
                                    </a>'''

content = content.replace(target, replacement)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
