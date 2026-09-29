from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app.models.finance import FinancialGoal, SearchHistory, LoginHistory, UserSettings
from app import db
import logging
from datetime import date
from dateutil.relativedelta import relativedelta
import math

bp = Blueprint('workspace', __name__)
logger = logging.getLogger(__name__)

# ================================
# MODULE A: GOALS
# ================================

@bp.route('/goals', methods=['GET'])
@login_required
def get_goals():
    goals = FinancialGoal.query.filter_by(user_id=current_user.id).order_by(FinancialGoal.target_date).all()
    results = []
    
    today = date.today()
    
    for g in goals:
        target = float(g.target_amount)
        saved = float(g.current_savings)
        contrib = float(g.monthly_contribution)
        
        remaining = max(0, target - saved)
        progress_pct = (saved / target * 100) if target > 0 else 0
        progress_pct = min(100, progress_pct)
        
        # Months until target date
        months_left = (g.target_date.year - today.year) * 12 + g.target_date.month - today.month
        if g.target_date.day < today.day:
            months_left -= 1
            
        months_left = max(0, months_left)
        
        # Required monthly savings without assuming investment returns
        required_monthly = (remaining / months_left) if months_left > 0 else remaining
        
        # Projected savings at target date via planned monthly contribution
        projected = saved + (contrib * months_left)
        
        # Estimated completion date (if they use monthly contribution)
        est_completion_date = None
        if contrib > 0 and remaining > 0:
            months_needed = math.ceil(remaining / contrib)
            est_completion_date = today + relativedelta(months=months_needed)
            
        results.append({
            'id': g.id,
            'name': g.name,
            'target_amount': target,
            'current_savings': saved,
            'monthly_contribution': contrib,
            'target_date': g.target_date.isoformat(),
            'remaining_amount': remaining,
            'progress_pct': round(progress_pct, 2),
            'months_left': months_left,
            'required_monthly': round(required_monthly, 2),
            'projected_amount': round(projected, 2),
            'est_completion_date': est_completion_date.isoformat() if est_completion_date else None,
            'is_achieved': saved >= target
        })
        
    return jsonify({'goals': results})

@bp.route('/goals', methods=['POST'])
@login_required
def create_goal():
    data = request.get_json() or {}
    
    name = data.get('name')
    target_amount = data.get('target_amount', 0)
    current_savings = data.get('current_savings', 0)
    monthly_contribution = data.get('monthly_contribution', 0)
    target_date_str = data.get('target_date')
    
    if not name or not target_date_str or float(target_amount) <= 0:
        return jsonify({'error': 'Name, Target Date, and a positive Target Amount are required.'}), 400
        
    try:
        t_date = date.fromisoformat(target_date_str)
        if t_date <= date.today():
            return jsonify({'error': 'Target date must be in the future.'}), 400
            
        goal = FinancialGoal(
            user_id=current_user.id,
            name=name,
            target_amount=float(target_amount),
            current_savings=float(current_savings),
            monthly_contribution=float(monthly_contribution),
            target_date=t_date
        )
        db.session.add(goal)
        db.session.commit()
        return jsonify({'success': True, 'goal_id': goal.id})
    except ValueError:
        return jsonify({'error': 'Invalid date format.'}), 400
    except Exception as e:
        logger.error(f"Error creating goal: {e}")
        return jsonify({'error': 'Failed to create goal.'}), 500

@bp.route('/goals/<int:goal_id>', methods=['PUT'])
@login_required
def update_goal(goal_id):
    goal = FinancialGoal.query.filter_by(id=goal_id, user_id=current_user.id).first()
    if not goal:
        return jsonify({'error': 'Goal not found'}), 404
        
    data = request.get_json() or {}
    
    if 'name' in data:
        if not data['name']:
            return jsonify({'error': 'Name cannot be empty.'}), 400
        goal.name = data['name']
        
    if 'target_amount' in data:
        if float(data['target_amount']) <= 0:
            return jsonify({'error': 'Target amount must be positive.'}), 400
        goal.target_amount = float(data['target_amount'])
        
    if 'current_savings' in data:
        goal.current_savings = max(0, float(data['current_savings']))
        
    if 'monthly_contribution' in data:
        goal.monthly_contribution = max(0, float(data['monthly_contribution']))
        
    if 'target_date' in data:
        try:
            t_date = date.fromisoformat(data['target_date'])
            if t_date <= date.today():
                return jsonify({'error': 'Target date must be in the future.'}), 400
            goal.target_date = t_date
        except ValueError:
            return jsonify({'error': 'Invalid date format.'}), 400
            
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/goals/<int:goal_id>', methods=['DELETE'])
@login_required
def delete_goal(goal_id):
    goal = FinancialGoal.query.filter_by(id=goal_id, user_id=current_user.id).first()
    if not goal:
        return jsonify({'error': 'Goal not found'}), 404
        
    db.session.delete(goal)
    db.session.commit()
    return jsonify({'success': True})

# ================================
# MODULE B: WORKSPACE
# ================================

@bp.route('/history/search', methods=['GET'])
@login_required
def get_search_history():
    page = request.args.get('page', 1, type=int)
    hist = SearchHistory.query.filter_by(user_id=current_user.id).order_by(SearchHistory.searched_at.desc()).paginate(page=page, per_page=10, error_out=False)
    
    results = [{'id': h.id, 'symbol': h.symbol, 'searched_at': h.searched_at.isoformat()} for h in hist.items]
    return jsonify({'history': results, 'page': hist.page, 'pages': hist.pages})

@bp.route('/history/search', methods=['DELETE'])
@login_required
def clear_search_history():
    SearchHistory.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/history/login', methods=['GET'])
@login_required
def get_login_history():
    page = request.args.get('page', 1, type=int)
    hist = LoginHistory.query.filter_by(user_id=current_user.id).order_by(LoginHistory.login_time.desc()).paginate(page=page, per_page=10, error_out=False)
    
    results = [{'id': h.id, 'login_time': h.login_time.isoformat(), 'ip_address': h.ip_address, 'user_agent': h.user_agent} for h in hist.items]
    return jsonify({'history': results, 'page': hist.page, 'pages': hist.pages})

@bp.route('/settings', methods=['GET'])
@login_required
def get_settings():
    settings = UserSettings.query.filter_by(user_id=current_user.id).first()
    if not settings:
        settings = UserSettings(user_id=current_user.id)
        db.session.add(settings)
        db.session.commit()
        
    return jsonify({
        'preferred_currency': settings.preferred_currency,
        'theme': settings.theme
    })

@bp.route('/settings', methods=['PUT'])
@login_required
def update_settings():
    settings = UserSettings.query.filter_by(user_id=current_user.id).first()
    if not settings:
        settings = UserSettings(user_id=current_user.id)
        db.session.add(settings)
        
    data = request.get_json() or {}
    
    if 'preferred_currency' in data:
        settings.preferred_currency = data['preferred_currency']
        
    if 'theme' in data:
        settings.theme = data['theme']
        
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/security/password', methods=['POST'])
@login_required
def change_password():
    data = request.get_json() or {}
    current_pass = data.get('current_password')
    new_pass = data.get('new_password')
    
    if not current_pass or not new_pass:
        return jsonify({'error': 'Both current and new passwords are required.'}), 400
        
    if not current_user.check_password(current_pass):
        return jsonify({'error': 'Incorrect current password.'}), 401
        
    if len(new_pass) < 6:
        return jsonify({'error': 'New password must be at least 6 characters long.'}), 400
        
    current_user.set_password(new_pass)
    db.session.commit()
    return jsonify({'success': True})
