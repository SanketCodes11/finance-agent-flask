from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user
from urllib.parse import urlsplit
from app import db
from app.models.user import User
from app.models.finance import LoginHistory
import re

bp = Blueprint('auth', __name__)

def is_valid_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Username and password are required.', 'danger')
            return render_template('auth/login.html')
            
        user = User.query.filter_by(username=username).first()
        if user is None or not user.check_password(password):
            flash('Invalid username or password', 'danger')
            return render_template('auth/login.html')
            
        # Strict separation: Prevent admins from using the normal login flow
        if getattr(user, 'is_admin', False):
            flash('Administrator accounts must log in through the dedicated Super Admin Portal.', 'info')
            return redirect(url_for('admin.login'))
            
        login_user(user, remember=request.form.get('remember_me'))
        
        # Record login history
        login_history = LoginHistory(
            user_id=user.id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(login_history)
        db.session.commit()
        
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('main.dashboard')
        return redirect(next_page)
        
    return render_template('auth/login.html')

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    if request.method == 'POST':
        from email_validator import validate_email, EmailNotValidError
        
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        password_confirm = request.form.get('password_confirm', '')
        
        errors = []
        if not username or len(username) < 3 or not re.match(r'^[a-zA-Z0-9_]+$', username):
            errors.append("Username must be at least 3 characters and contain only letters, numbers, and underscores.")
            
        try:
            valid = validate_email(email, check_deliverability=False)
            email = valid.normalized
        except EmailNotValidError as e:
            errors.append(str(e))
            
        if not password or len(password) < 8:
            errors.append("Password must be at least 8 characters long.")
        elif not re.search(r'[A-Z]', password) or not re.search(r'[a-z]', password) or not re.search(r'\d', password):
            errors.append("Password must include uppercase, lowercase, and a number.")
            
        if password != password_confirm:
            errors.append("Passwords do not match.")
            
        if User.query.filter_by(username=username).first():
            errors.append("Username is already taken.")
        if User.query.filter_by(email=email).first():
            errors.append("Email is already registered.")
            
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('auth/register.html', username=username, email=email)
            
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user! Please log in.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/register.html')
