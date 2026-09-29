import json
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, abort
from flask_login import login_required, current_user
from sqlalchemy import inspect
from app import db
from app.models.user import User, AdminAuditLog
from app.models.finance import PlatformSetting
from app.models.finance import LoginHistory, SearchHistory
from sqlalchemy import func
from app.decorators import admin_required
from datetime import datetime, timezone

bp = Blueprint('admin', __name__)

def log_admin_action(action, table_name=None, record_id=None, details=None):
    """Helper to safely record admin audit logs."""
    log = AdminAuditLog(
        admin_id=current_user.id,
        action=action,
        table_name=table_name,
        record_id=str(record_id) if record_id else None,
        details=json.dumps(details) if details else None,
        ip_address=request.remote_addr
    )
    db.session.add(log)
    # We don't commit here, we let the calling function commit the transaction

@bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Admin Overview Dashboard."""
    # Overview Statistics
    total_users = User.query.count()
    active_admins = User.query.filter_by(is_admin=True, is_active=True).count()
    
    # DB Table counts (safe system health check)
    inspector = inspect(db.engine)
    total_tables = len(inspector.get_table_names())
    
    # Recent audit logs
    recent_activity = AdminAuditLog.query.order_by(AdminAuditLog.timestamp.desc()).limit(10).all()
    
    return render_template('admin/dashboard.html', 
                           total_users=total_users, 
                           active_admins=active_admins,
                           total_tables=total_tables,
                           recent_activity=recent_activity)

@bp.route('/users')
@login_required
@admin_required
def users():
    """User Management List."""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('q', '').strip()
    
    query = User.query
    if search:
        query = query.filter(
            (User.username.ilike(f'%{search}%')) | 
            (User.email.ilike(f'%{search}%'))
        )
        
    pagination = query.order_by(User.created_at.desc()).paginate(page=page, per_page=15, error_out=False)
    
    # Check if the current user is the last active admin (for UI warnings)
    active_admins_count = User.query.filter_by(is_admin=True, is_active=True).count()
    
    
    # Fetch last successful logins
    last_logins = dict(db.session.query(
        LoginHistory.user_id, 
        func.max(LoginHistory.login_time)
    ).group_by(LoginHistory.user_id).all())
    
    return render_template('admin/users.html', 
                           pagination=pagination, 
                           search=search,
                           active_admins_count=active_admins_count,
                           last_logins=last_logins)

@bp.route('/users/<int:user_id>/toggle_admin', methods=['POST'])
@login_required
@admin_required
def toggle_admin(user_id):
    """Toggle a user's admin status securely."""
    user = User.query.get_or_404(user_id)
    
    # LAST ADMIN PROTECTION: Prevent demoting the last active admin
    if user.is_admin and user.is_active:
        active_admins_count = User.query.filter_by(is_admin=True, is_active=True).count()
        if active_admins_count <= 1:
            flash("Action Blocked: You cannot demote the last active super admin. The system must have at least one.", "danger")
            return redirect(url_for('admin.users'))
            
    user.is_admin = not user.is_admin
    action_name = "granted_admin" if user.is_admin else "revoked_admin"
    
    log_admin_action(
        action=action_name, 
        table_name="user", 
        record_id=user.id, 
        details={"username": user.username, "email": user.email}
    )
    
    db.session.commit()
    status = "granted Admin privileges" if user.is_admin else "demoted to regular user"
    flash(f"User {user.username} has been {status}.", "success")
    return redirect(url_for('admin.users'))

@bp.route('/users/<int:user_id>/toggle_active', methods=['POST'])
@login_required
@admin_required
def toggle_active(user_id):
    """Toggle a user's active status securely."""
    user = User.query.get_or_404(user_id)
    
    # LAST ADMIN PROTECTION: Prevent deactivating the last active admin
    if user.is_admin and user.is_active:
        active_admins_count = User.query.filter_by(is_admin=True, is_active=True).count()
        if active_admins_count <= 1:
            flash("Action Blocked: You cannot deactivate the last active super admin.", "danger")
            return redirect(url_for('admin.users'))
            
    user.is_active = not user.is_active
    action_name = "activated_user" if user.is_active else "deactivated_user"
    
    log_admin_action(
        action=action_name, 
        table_name="user", 
        record_id=user.id, 
        details={"username": user.username, "email": user.email}
    )
    
    db.session.commit()
    status = "activated" if user.is_active else "deactivated"
    flash(f"User {user.username} has been {status}.", "success")
    return redirect(url_for('admin.users'))


from sqlalchemy import text
import math

@bp.route('/activity')
@login_required
@admin_required
def activity():
    """Live Activity & Audit Center."""
    page = request.args.get('page', 1, type=int)
    search_user = request.args.get('user', '').strip()
    search_event = request.args.get('event', '').strip()
    per_page = 20
    
    # Base unified query
    base_query = """
    SELECT 
        u.username,
        u.email,
        a.user_id,
        a.event_type,
        a.details,
        a.ip_address,
        a.event_time,
        a.source
    FROM (
        SELECT admin_id as user_id, action as event_type, details, ip_address, timestamp as event_time, 'Admin Log' as source FROM admin_audit_log
        UNION ALL
        SELECT user_id, 'login' as event_type, user_agent as details, ip_address, login_time as event_time, 'Login' as source FROM login_history
        UNION ALL
        SELECT user_id, 'stock_search' as event_type, symbol as details, NULL as ip_address, searched_at as event_time, 'Search' as source FROM search_history
        UNION ALL
        SELECT user_id, event_type, details, ip_address, timestamp as event_time, 'Activity' as source FROM activity_log
    ) a
    JOIN user u ON u.id = a.user_id
    """
    
    count_query = """
    SELECT COUNT(*) FROM (
        SELECT admin_id as user_id, action as event_type FROM admin_audit_log
        UNION ALL
        SELECT user_id, 'login' as event_type FROM login_history
        UNION ALL
        SELECT user_id, 'stock_search' as event_type FROM search_history
        UNION ALL
        SELECT user_id, event_type FROM activity_log
    ) a
    JOIN user u ON u.id = a.user_id
    """
    
    params = {}
    where_clauses = []
    
    if search_user:
        where_clauses.append("(u.username LIKE :user OR u.email LIKE :user)")
        params['user'] = f"%{search_user}%"
        
    if search_event:
        where_clauses.append("a.event_type LIKE :event")
        params['event'] = f"%{search_event}%"
        
    if where_clauses:
        where_str = " WHERE " + " AND ".join(where_clauses)
        base_query += where_str
        count_query += where_str
        
    # Get total records safely
    with db.engine.connect() as conn:
        total_records = conn.execute(text(count_query), params).scalar()
        
    total_pages = math.ceil(total_records / per_page)
    
    # Add ordering and pagination
    base_query += " ORDER BY a.event_time DESC LIMIT :limit OFFSET :offset"
    params['limit'] = per_page
    params['offset'] = (page - 1) * per_page
    
    # Get rows
    activities = []
    with db.engine.connect() as conn:
        result = conn.execute(text(base_query), params)
        activities = [dict(zip(result.keys(), row)) for row in result]
        
    return render_template('admin/activity.html', 
                           activities=activities,
                           page=page,
                           total_pages=total_pages,
                           total_records=total_records,
                           search_user=search_user,
                           search_event=search_event)


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

from app.models.finance import Watchlist, PortfolioItem, PortfolioTransaction, Alert, VirtualAccount, VirtualOrder, FinancialGoal

@bp.route('/users/<int:user_id>')
@admin_required
def user_detail(user_id):
    """User 360 Profile: Comprehensive view of a user's data."""
    user = User.query.get_or_404(user_id)
    
    # Gather all associated data
    watchlists = Watchlist.query.filter_by(user_id=user.id).all()
    portfolio = PortfolioItem.query.filter_by(user_id=user.id).all()
    alerts = Alert.query.filter_by(user_id=user.id).all()
    goals = FinancialGoal.query.filter_by(user_id=user.id).all()
    
    virtual_account = VirtualAccount.query.filter_by(user_id=user.id).first()
    virtual_orders = VirtualOrder.query.filter_by(account_id=virtual_account.id).order_by(VirtualOrder.timestamp.desc()).limit(10).all() if virtual_account else []
    
    from app.models.finance import VirtualWalletTransaction
    wallet_txs = VirtualWalletTransaction.query.filter_by(account_id=virtual_account.id).order_by(VirtualWalletTransaction.timestamp.desc()).limit(10).all() if virtual_account else []
    
    recent_logins = LoginHistory.query.filter_by(user_id=user.id).order_by(LoginHistory.login_time.desc()).limit(10).all()
    
    # Calculate portfolio total value (naive sum of quantity * avg_price for simplicity in admin view)
    portfolio_value = sum(item.shares * item.avg_price for item in portfolio)
    
    return render_template('admin/user_detail.html',
                           user=user,
                           watchlists=watchlists,
                           portfolio=portfolio,
                           portfolio_value=portfolio_value,
                           alerts=alerts,
                           goals=goals,
                           virtual_account=virtual_account,
                           virtual_orders=virtual_orders,
                           wallet_txs=wallet_txs,
                           recent_logins=recent_logins)


@bp.route('/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def settings():
    """Global Platform Settings (Maintenance Mode, AI Toggle)."""
    settings = PlatformSetting.get_settings()
    
    if request.method == 'POST':
        # Check toggles
        maintenance = request.form.get('maintenance_mode') == 'on'
        ai_enabled = request.form.get('ai_analyst_enabled') == 'on'
        
        # Log if changed
        if settings.maintenance_mode != maintenance:
            log_admin_action('update_settings', 'platform_setting', str(settings.id), 
                             f'Maintenance Mode changed to {maintenance}')
        if settings.ai_analyst_enabled != ai_enabled:
            log_admin_action('update_settings', 'platform_setting', str(settings.id), 
                             f'AI Analyst globally changed to {ai_enabled}')
                             
        settings.maintenance_mode = maintenance
        settings.ai_analyst_enabled = ai_enabled
        db.session.commit()
        
        flash('Platform settings updated successfully.', 'success')
        return redirect(url_for('admin.settings'))
        
    return render_template('admin/settings.html', settings=settings)

