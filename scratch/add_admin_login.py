import os

file_path = 'app/routes/admin.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

route_code = '''
from urllib.parse import urlsplit, urljoin
from flask_login import login_user
from app.models.finance import LoginHistory

def is_safe_url(target):
    ref_url = urlsplit(request.host_url)
    test_url = urlsplit(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Dedicated Super Admin Login."""
    if current_user.is_authenticated:
        if current_user.is_admin and current_user.is_active:
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('main.dashboard'))
            
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Username and password are required.', 'danger')
            return render_template('admin/login.html')
            
        user = User.query.filter_by(username=username).first()
        
        # Verify credentials first
        if user is None or not user.check_password(password):
            flash('Invalid username or password.', 'danger')
            return render_template('admin/login.html')
            
        # Enforce strict Admin-only check
        if not user.is_admin or not user.is_active:
            # We do NOT log them in. Just show generic denied message.
            flash('Access Denied: Admin privileges required.', 'danger')
            return render_template('admin/login.html')
            
        # Securely log in the verified active admin
        login_user(user, remember=request.form.get('remember_me'))
        
        # Record login history (matches normal auth flow)
        login_history = LoginHistory(
            user_id=user.id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(login_history)
        
        # Admin Audit Log (Optional but good for visibility)
        log = AdminAuditLog(
            admin_id=user.id,
            action='admin_login',
            table_name='user',
            record_id=str(user.id),
            details='{"ip": "%s"}' % request.remote_addr,
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        # Secure open redirect prevention
        next_page = request.args.get('next')
        if not next_page or not is_safe_url(next_page):
            next_page = url_for('admin.dashboard')
            
        return redirect(next_page)
        
    return render_template('admin/login.html')
'''

if "@bp.route('/login', methods=['GET', 'POST'])" not in content:
    content += '\n' + route_code
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
