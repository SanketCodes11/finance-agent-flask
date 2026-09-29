with open('app/templates/base.html', 'r', encoding='utf-8') as f:
    content = f.read()

target_nav = '<li class="nav-item"><a class="nav-link px-3 {{ \'active text-primary\' if request.endpoint == \'main.news\' else \'\' }}" href="{{ url_for(\'main.news\') }}">News</a></li>'
nav_addition = '\n                          <li class="nav-item"><a class="nav-link px-3 {{ \'active text-primary\' if request.endpoint == \'main.goals\' else \'\' }}" href="{{ url_for(\'main.goals\') }}">Goals</a></li>'

if 'main.goals' not in content:
    content = content.replace(target_nav, target_nav + nav_addition)
    
target_menu = '<li><a class="dropdown-item" href="{{ url_for(\'auth.logout\') }}"><i class="fa-solid fa-right-from-bracket me-2"></i>Logout</a></li>'
menu_addition = '<li><a class="dropdown-item" href="{{ url_for(\'main.workspace\') }}"><i class="fa-solid fa-gear me-2"></i>Workspace & Profile</a></li>\n                                  <li><hr class="dropdown-divider"></li>\n                                  '

if 'main.workspace' not in content:
    content = content.replace(target_menu, menu_addition + target_menu)
    
with open('app/templates/base.html', 'w', encoding='utf-8') as f:
    f.write(content)
