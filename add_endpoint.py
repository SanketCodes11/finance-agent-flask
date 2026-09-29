with open('app/api/finance.py', 'r') as f:
    content = f.read()

if 'from app.services.portfolio_analytics_service' not in content:
    content = content.replace('from app.services.finance_service import', 'from app.services.portfolio_analytics_service import calculate_portfolio_history\nfrom app.services.finance_service import')
    with open('app/api/finance.py', 'w') as f:
        f.write(content)

api_str = '''
@bp.route('/portfolio/historical', methods=['GET'])
@login_required
def get_portfolio_historical():
    period = request.args.get('period', '1M').upper()
    valid_periods = ['1M', '3M', '6M', '1Y', 'ALL']
    if period not in valid_periods:
        period = '1M'
    
    try:
        data = calculate_portfolio_history(current_user.id, period)
        return jsonify(data)
    except Exception as e:
        import logging
        logging.error(f"Historical portfolio error: {e}")
        return jsonify({'error': 'Failed to calculate historical portfolio data.'}), 500
'''

if '/portfolio/historical' not in content:
    with open('app/api/finance.py', 'a') as f:
        f.write(api_str)
    print("Added /portfolio/historical endpoint")
else:
    print("Endpoint already exists")
