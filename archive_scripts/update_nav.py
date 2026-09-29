import os

base_path = os.path.abspath('app/templates/base.html')
with open(base_path, 'r', encoding='utf-8') as f:
    content = f.read()

nav_start = content.find('<ul class="navbar-nav me-auto mb-2 mb-lg-0 fw-medium">')
nav_end = content.find('</ul>', nav_start) + 5

new_nav = """<ul class="navbar-nav me-auto mb-2 mb-lg-0 fw-medium">
                    {% if current_user.is_authenticated %}
                        <li class="nav-item"><a class="nav-link px-3 {{ 'active text-primary' if request.endpoint == 'main.dashboard' else '' }}" href="{{ url_for('main.dashboard') }}">Dashboard</a></li>
                        <li class="nav-item"><a class="nav-link px-3 {{ 'active text-primary' if request.endpoint == 'main.compare' else '' }}" href="{{ url_for('main.compare') }}">Compare</a></li>
                        <li class="nav-item"><a class="nav-link px-3 {{ 'active text-primary' if request.endpoint == 'main.watchlist' else '' }}" href="{{ url_for('main.watchlist') }}">Watchlist</a></li>
                        <li class="nav-item"><a class="nav-link px-3 {{ 'active text-primary' if request.endpoint == 'main.portfolio' else '' }}" href="{{ url_for('main.portfolio') }}">Portfolio</a></li>
                        <li class="nav-item"><a class="nav-link px-3 {{ 'active text-primary' if request.endpoint == 'main.alerts' else '' }}" href="{{ url_for('main.alerts') }}">Alerts</a></li>
                        <li class="nav-item"><a class="nav-link px-3 {{ 'active text-primary' if request.endpoint == 'main.news' else '' }}" href="{{ url_for('main.news') }}">News</a></li>
                        <li class="nav-item dropdown">
                            <a class="nav-link px-3 dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown">More</a>
                            <ul class="dropdown-menu shadow border-0">
                                <li><a class="dropdown-item" href="{{ url_for('main.reports') }}">Reports</a></li>
                                <li><a class="dropdown-item" href="{{ url_for('main.tools') }}">Calculators</a></li>
                                <li><a class="dropdown-item" href="{{ url_for('main.academy') }}">Academy</a></li>
                            </ul>
                        </li>
                    {% endif %}
                </ul>"""

if nav_start != -1:
    new_content = content[:nav_start] + new_nav + content[nav_end:]
    with open(base_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Updated base.html successfully.")
else:
    print("Could not find nav ul.")
