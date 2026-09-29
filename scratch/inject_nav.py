import os

base_path = 'app/templates/base.html'
with open(base_path, 'r', encoding='utf-8') as f:
    content = f.read()

target = '<li><a class="dropdown-item py-2" href="{{ url_for(\'auth.logout\') }}">'
replacement = '''{% if current_user.is_admin %}
                                <li><a class="dropdown-item py-2" href="{{ url_for('admin.dashboard') }}"><i class="fa-solid fa-shield-halved me-2 text-primary"></i>Admin Dashboard</a></li>
                                <li><hr class="dropdown-divider"></li>
                                {% endif %}
                                ''' + target

if '{% if current_user.is_admin %}' not in content:
    content = content.replace(target, replacement)
    with open(base_path, 'w', encoding='utf-8') as f:
        f.write(content)
