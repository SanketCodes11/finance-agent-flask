import os

file_path = 'app/api/paper_trading.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

wallet_code = '''
from app.models.finance import VirtualWalletTransaction

@bp.route('/wallet', methods=['POST'])
@login_required
def manage_wallet():
    data = request.json
    action = data.get('action', '').upper()
    try:
        amount = Decimal(str(data.get('amount', 0)))
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid amount'}), 400

    if action not in ['DEPOSIT', 'WITHDRAW'] or amount <= 0:
        return jsonify({'error': 'Invalid action or amount'}), 400

    account = VirtualAccount.query.filter_by(user_id=current_user.id).with_for_update().first()
    if not account:
        return jsonify({'error': 'Virtual account not found.'}), 404

    try:
        if action == 'WITHDRAW':
            if account.current_cash < amount:
                return jsonify({'error': 'Insufficient available cash for withdrawal'}), 400
            account.current_cash -= amount
        elif action == 'DEPOSIT':
            account.current_cash += amount
            account.initial_balance += amount # Treat external injection as adding to initial balance for ROI calculation

        # Record transaction
        wallet_tx = VirtualWalletTransaction(
            account_id=account.id,
            transaction_type=action,
            amount=amount,
            resulting_balance=account.current_cash,
            description=f"User {action.lower()}"
        )
        db.session.add(wallet_tx)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Successfully {action.lower()}ed ${amount:,.2f}',
            'new_balance': float(account.current_cash)
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Wallet transaction failed: {e}")
        return jsonify({'error': 'Transaction failed due to an internal error.'}), 500

@bp.route('/wallet/history', methods=['GET'])
@login_required
def get_wallet_history():
    account = VirtualAccount.query.filter_by(user_id=current_user.id).first()
    if not account:
        return jsonify([])
        
    transactions = VirtualWalletTransaction.query.filter_by(account_id=account.id)\\
        .order_by(VirtualWalletTransaction.timestamp.desc()).limit(50).all()
        
    return jsonify([{
        'id': t.id,
        'type': t.transaction_type,
        'amount': float(t.amount),
        'balance': float(t.resulting_balance),
        'description': t.description,
        'timestamp': t.timestamp.isoformat()
    } for t in transactions])
'''

if "@bp.route('/wallet', methods=['POST'])" not in content:
    content += wallet_code
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
