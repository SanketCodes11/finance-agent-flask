import os

with open('app/templates/admin/users.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Add header
if '<th>Last Login</th>' not in content:
    content = content.replace('<th>Joined (UTC)</th>', '<th>Joined (UTC)</th>\n                            <th>Last Login</th>')

# Add table cell
target_cell = '<td class="text-muted small">{{ u.created_at.strftime(\'%Y-%m-%d %H:%M\') }}</td>'
replacement_cell = '''<td class="text-muted small">{{ u.created_at.strftime('%Y-%m-%d %H:%M') }}</td>
                            <td class="small text-muted">
                                {% if u.id in last_logins %}
                                    {{ last_logins[u.id].strftime('%Y-%m-%d %H:%M') }}
                                {% else %}
                                    <em>Never</em>
                                {% endif %}
                            </td>'''

if 'last_logins[u.id]' not in content:
    content = content.replace(target_cell, replacement_cell)

with open('app/templates/admin/users.html', 'w', encoding='utf-8') as f:
    f.write(content)
