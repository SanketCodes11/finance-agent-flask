import os

path = os.path.abspath('app/api/finance.py')
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Add Alert import if not present
if 'from app.models.finance import Watchlist, SearchHistory, PortfolioItem, Alert' not in content:
    content = content.replace('from app.models.finance import Watchlist, SearchHistory, PortfolioItem', 'from app.models.finance import Watchlist, SearchHistory, PortfolioItem, Alert')

alert_routes = """
@bp.route('/alerts', methods=['GET', 'POST'])
@login_required
def manage_alerts():
    if request.method == 'GET':
        alerts = Alert.query.filter_by(user_id=current_user.id).all()
        return jsonify([{'id': a.id, 'symbol': a.symbol, 'condition': a.condition, 'target_price': a.target_price, 'is_active': a.is_active} for a in alerts])
    
    data = request.get_json()
    new_alert = Alert(
        user_id=current_user.id,
        symbol=data['symbol'],
        condition=data['condition'],
        target_price=data['target_price']
    )
    db.session.add(new_alert)
    db.session.commit()
    return jsonify({'success': True, 'id': new_alert.id})

@bp.route('/alerts/<int:alert_id>', methods=['DELETE'])
@login_required
def delete_alert(alert_id):
    alert = Alert.query.filter_by(id=alert_id, user_id=current_user.id).first()
    if not alert:
        return jsonify({'error': 'Not found'}), 404
    db.session.delete(alert)
    db.session.commit()
    return jsonify({'success': True})
"""

if "def manage_alerts()" not in content:
    content += "\n" + alert_routes
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Added alert routes.")
else:
    print("Routes already exist.")
