from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user, login_required
from app.models.finance import Watchlist, SearchHistory, PlatformSetting
from flask import request, jsonify

bp = Blueprint('main', __name__)


@bp.before_app_request
def check_maintenance_mode():
    # Allow static files and health checks
    if request.endpoint and request.endpoint.startswith('static'):
        return
    if request.path == '/health':
        return
        
    try:
        settings = PlatformSetting.get_settings()
        if settings.maintenance_mode:
            # Allow admins to bypass
            if current_user.is_authenticated and current_user.is_admin:
                return
            
            # Allow auth endpoints (so admins can login)
            if request.endpoint and request.endpoint.startswith('auth.'):
                return
                
            # Allow admin endpoints
            if request.endpoint and request.endpoint.startswith('admin.'):
                return
                
            if request.path.startswith('/api/'):
                return jsonify({"error": "Platform is under maintenance. Please try again later."}), 503
            
            return render_template('errors/maintenance.html'), 503
    except Exception:
        # DB might not be initialized during initial setup/migration
        pass


from app.models.finance import CMSContent
@bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    # Fetch CMS content
    cms_title = CMSContent.query.filter_by(key='homepage_title', is_published=True).first()
    cms_subtitle = CMSContent.query.filter_by(key='homepage_subtitle', is_published=True).first()
    
    context = {
        'homepage_title': cms_title.value if cms_title else 'Smarter Investing with <span class="text-primary">AI Insights</span>',
        'homepage_subtitle': cms_subtitle.value if cms_subtitle else 'Finance Insight Agent combines real-time market data, comprehensive news analysis, and AI-driven insights to help you make informed financial decisions.'
    }
    
    return render_template('index.html', **context)

@bp.route('/dashboard')
@login_required
def dashboard():
    # We will fetch latest search history and watchlists for the dashboard
    recent_searches = SearchHistory.query.filter_by(user_id=current_user.id).order_by(SearchHistory.searched_at.desc()).limit(5).all()
    watchlists = Watchlist.query.filter_by(user_id=current_user.id).order_by(Watchlist.added_at.desc()).all()
    
    return render_template('dashboard.html', 
                           recent_searches=recent_searches,
                           watchlists=watchlists)

@bp.route('/stock/<symbol>')
@login_required
def stock_detail(symbol):
    symbol = symbol.upper()
    is_watchlisted = Watchlist.query.filter_by(user_id=current_user.id, symbol=symbol).first() is not None
    return render_template('stock_detail.html', symbol=symbol, is_watchlisted=is_watchlisted)

@bp.route('/watchlist')
@login_required
def watchlist():
    return render_template('watchlist.html')

@bp.route('/news')
@login_required
def news():
    return render_template('news.html')

@bp.route('/portfolio')
@login_required
def portfolio():
    return render_template('portfolio.html')

@bp.route('/compare')
@login_required
def compare():
    return render_template('comparison.html')

@bp.route('/alerts')
@login_required
def alerts():
    return render_template('alerts.html')

@bp.route('/tools')
@login_required
def tools():
    return render_template('tools.html')

@bp.route('/academy')
@login_required
def academy():
    return render_template('academy.html')

@bp.route('/reports')
@login_required
def reports():
    return render_template('reports.html')

@bp.route('/paper-trade')
@login_required
def paper_trade():
    return render_template('paper_trading.html')

@bp.route('/screener')
@login_required
def screener():
    return render_template('screener.html')

@bp.route('/goals')
@login_required
def goals():
    return render_template('goals.html')

@bp.route('/workspace')
@login_required
def workspace():
    return render_template('workspace.html')
