from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app.services.finance_service import get_stock_quote
from app.models.finance import VirtualAccount, VirtualPosition, VirtualOrder
from app import db
from decimal import Decimal
import logging
from datetime import datetime, timezone

bp = Blueprint('paper_trade', __name__)
logger = logging.getLogger(__name__)

@bp.route('/account', methods=['GET'])
@login_required
def get_account():
    account = VirtualAccount.query.filter_by(user_id=current_user.id).first()
    if not account:
        account = VirtualAccount(
            user_id=current_user.id,
            initial_balance=Decimal('1000000.00'),
            current_cash=Decimal('1000000.00')
        )
        db.session.add(account)
        db.session.commit()

    positions = VirtualPosition.query.filter_by(account_id=account.id).all()
    holdings = []
    total_market_value = Decimal('0.0')
    
    for pos in positions:
        quote = get_stock_quote(pos.symbol)
        if quote and 'price' in quote:
            current_price = Decimal(str(quote['price']))
        else:
            current_price = pos.avg_price # Fallback
            
        market_value = pos.quantity * current_price
        total_market_value += market_value
        unrealized_pl = market_value - (pos.quantity * pos.avg_price)
        
        holdings.append({
            'symbol': pos.symbol,
            'quantity': float(pos.quantity),
            'avg_price': float(pos.avg_price),
            'current_price': float(current_price),
            'market_value': float(market_value),
            'unrealized_pl': float(unrealized_pl),
            'return_pct': float((current_price - pos.avg_price) / pos.avg_price * 100) if pos.avg_price > 0 else 0
        })
        
    return jsonify({
        'initial_balance': float(account.initial_balance),
        'current_cash': float(account.current_cash),
        'portfolio_value': float(total_market_value),
        'total_value': float(account.current_cash + total_market_value),
        'holdings': holdings
    })

@bp.route('/order', methods=['POST'])
@login_required
def execute_order():
    data = request.json
    symbol = data.get('symbol', '').upper().strip()
    order_type = data.get('order_type', '').upper()
    try:
        quantity = Decimal(str(data.get('quantity', 0)))
    except (ValueError, TypeError, __import__('decimal').InvalidOperation):
        return jsonify({'error': 'Invalid quantity'}), 400

    if not symbol or order_type not in ['BUY', 'SELL'] or quantity <= 0:
        return jsonify({'error': 'Invalid order parameters'}), 400

    # Ensure account exists
    account = VirtualAccount.query.filter_by(user_id=current_user.id).first()
    if not account:
        return jsonify({'error': 'Virtual account not found. Please load the dashboard first.'}), 404

    # Fetch live price
    quote = get_stock_quote(symbol)
    if not quote or 'price' not in quote:
        return jsonify({'error': f'Failed to retrieve live market data for {symbol}'}), 400
    
    execution_price = Decimal(str(quote['price']))
    transaction_value = quantity * execution_price

    try:
        if order_type == 'BUY':
            # Conditional atomic update for cash deduction
            updated = VirtualAccount.query.filter(
                VirtualAccount.id == account.id,
                VirtualAccount.current_cash >= transaction_value
            ).update({
                'current_cash': VirtualAccount.current_cash - transaction_value
            })
            
            if not updated:
                return jsonify({'error': 'Insufficient virtual cash for this transaction'}), 400
                
            # Update or create position
            pos = VirtualPosition.query.filter_by(account_id=account.id, symbol=symbol).with_for_update().first()
            if pos:
                total_cost = (pos.quantity * pos.avg_price) + transaction_value
                pos.quantity += quantity
                pos.avg_price = total_cost / pos.quantity
            else:
                pos = VirtualPosition(
                    account_id=account.id,
                    symbol=symbol,
                    quantity=quantity,
                    avg_price=execution_price
                )
                db.session.add(pos)
                
        elif order_type == 'SELL':
            # Conditional atomic update for quantity deduction
            updated = VirtualPosition.query.filter(
                VirtualPosition.account_id == account.id,
                VirtualPosition.symbol == symbol,
                VirtualPosition.quantity >= quantity
            ).update({
                'quantity': VirtualPosition.quantity - quantity
            })
            
            if not updated:
                db.session.rollback()
                return jsonify({'error': 'Insufficient shares to sell'}), 400
                
            # Add cash
            VirtualAccount.query.filter_by(id=account.id).update({
                'current_cash': VirtualAccount.current_cash + transaction_value
            })
            
            # Clean up empty position
            VirtualPosition.query.filter(
                VirtualPosition.account_id == account.id,
                VirtualPosition.symbol == symbol,
                VirtualPosition.quantity <= 0
            ).delete()

        # Record the order
        order = VirtualOrder(
            account_id=account.id,
            symbol=symbol,
            order_type=order_type,
            quantity=quantity,
            execution_price=execution_price,
            transaction_value=transaction_value
        )
        db.session.add(order)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Successfully executed {order_type} for {quantity} shares of {symbol} at {execution_price:.2f}',
            'execution_price': float(execution_price),
            'transaction_value': float(transaction_value)
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Paper trading order failed: {e}")
        return jsonify({'error': 'Transaction failed due to an internal error. Rolled back.'}), 500

@bp.route('/history', methods=['GET'])
@login_required
def get_history():
    account = VirtualAccount.query.filter_by(user_id=current_user.id).first()
    if not account:
        return jsonify([])
        
    orders = VirtualOrder.query.filter_by(account_id=account.id)\
        .order_by(VirtualOrder.timestamp.desc()).limit(50).all()
        
    return jsonify([{
        'id': o.id,
        'symbol': o.symbol,
        'order_type': o.order_type,
        'quantity': float(o.quantity),
        'execution_price': float(o.execution_price),
        'transaction_value': float(o.transaction_value),
        'status': o.status,
        'timestamp': o.timestamp.isoformat()
    } for o in orders])

from app.models.finance import VirtualWalletTransaction

@bp.route('/wallet', methods=['POST'])
@login_required
def manage_wallet():
    data = request.json
    action = data.get('action', '').upper()
    try:
        amount = Decimal(str(data.get('amount', 0)))
    except (ValueError, TypeError, __import__('decimal').InvalidOperation):
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
        
    transactions = VirtualWalletTransaction.query.filter_by(account_id=account.id)\
        .order_by(VirtualWalletTransaction.timestamp.desc()).limit(50).all()
        
    return jsonify([{
        'id': t.id,
        'type': t.transaction_type,
        'amount': float(t.amount),
        'balance': float(t.resulting_balance),
        'description': t.description,
        'timestamp': t.timestamp.isoformat()
    } for t in transactions])
