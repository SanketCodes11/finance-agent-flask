import os

file_path = 'app/routes/admin.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

route_code = '''
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
    virtual_orders = VirtualOrder.query.filter_by(account_id=virtual_account.id).order_by(VirtualOrder.created_at.desc()).limit(10).all() if virtual_account else []
    
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
                           recent_logins=recent_logins)
'''

if "@bp.route('/users/<int:user_id>')" not in content:
    content += route_code
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
