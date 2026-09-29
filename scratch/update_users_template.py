import os

file_path = 'app/templates/admin/users.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('<th>Role</th>', '<th>Role</th>\n                            <th class="text-end px-4">Actions</th>')

action_buttons = '''                            <td class="text-end px-4">
                                <a href="{{ url_for('admin.user_detail', user_id=u.id) }}" class="btn btn-sm btn-outline-primary shadow-sm rounded-3">
                                    <i class="fa-solid fa-eye"></i> View
                                </a>
                                <!-- Role Toggle Dropdown -->
                                <div class="dropdown d-inline-block ms-1">
                                    <button class="btn btn-sm btn-light border dropdown-toggle" type="button" data-bs-toggle="dropdown" aria-expanded="false">
                                        <i class="fa-solid fa-gear"></i>
                                    </button>
                                    <ul class="dropdown-menu dropdown-menu-end shadow-sm border-0">
                                        <li>
                                            <form method="POST" action="{{ url_for('admin.toggle_active', user_id=u.id) }}" class="d-inline w-100">
                                                <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                                                <button type="submit" class="dropdown-item {% if u.is_active %}text-danger{% else %}text-success{% endif %}">
                                                    {% if u.is_active %}<i class="fa-solid fa-ban me-2"></i>Deactivate{% else %}<i class="fa-solid fa-check me-2"></i>Activate{% endif %}
                                                </button>
                                            </form>
                                        </li>
                                        <li>
                                            <form method="POST" action="{{ url_for('admin.toggle_admin', user_id=u.id) }}" class="d-inline w-100">
                                                <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                                                <button type="submit" class="dropdown-item" onclick="return confirm('Change admin status for {{ u.username }}?');">
                                                    {% if u.is_admin %}<i class="fa-regular fa-user me-2"></i>Demote to User{% else %}<i class="fa-solid fa-shield me-2"></i>Promote to Admin{% endif %}
                                                </button>
                                            </form>
                                        </li>
                                    </ul>
                                </div>
                            </td>'''

# Replace the existing role dropdown block with the new action_buttons
# Wait, I don't want to break the existing file. Let's just use a simpler script to read/replace.
