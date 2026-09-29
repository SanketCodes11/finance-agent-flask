import os

file_path = 'app/templates/auth/login.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

target = '</div>\n        </div>\n    </div>\n</div>\n{% endblock %}'
replacement = '''</div>\n        </div>\n        <div class="text-center mt-3 small opacity-50">\n            <a href="{{ url_for('admin.login') }}" class="text-muted text-decoration-none"><i class="fa-solid fa-shield-halved me-1"></i>Admin Portal</a>\n        </div>\n    </div>\n</div>\n{% endblock %}'''

if 'admin.login' not in content:
    content = content.replace(target, replacement)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
