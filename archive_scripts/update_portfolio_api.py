import os
import re

path = os.path.abspath('app/api/finance.py')
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Add PortfolioTransaction if missing
if 'PortfolioTransaction' not in content:
    content = content.replace('Alert', 'Alert, PortfolioTransaction')

# We'll replace the block from @bp.route('/portfolio' to the end of update_portfolio_item
start_marker = "@bp.route('/portfolio', methods=['GET', 'POST'])"
end_marker = "@bp.route('/alerts', methods=['GET', 'POST'])"

new_portfolio_code = """@bp.route('/portfolio', methods=['GET', 'POST'])
@login_required
def manage_portfolio():
    if request.method == 'GET':
        items = PortfolioItem.query.filter_by(user_id=current_user.id).order_by(PortfolioItem.added_at.desc()).all()
        # Only show items with quantity > 0
        items = [item for item in items if item.quantity > 0]
        symbols = list(set([item.symbol for item in items]))
        
        quotes = get_multiple_stock_quotes(symbols)
        
        result = []
        for item in items:
            quote = quotes.get(item.symbol)
            
            # Use current market data if available, fallback to DB
            current_price = quote.get('price') if quote else None
            current_value = current_price * item.quantity if current_price else None
            total_cost = item.purchase_price * item.quantity
            
            # Only calculate unrealized P/L if we have a current price
            unrealized_pl = None
            unrealized_pl_pct = None
            if current_value is not None:
                unrealized_pl = current_value - total_cost
                if total_cost > 0:
                    unrealized_pl_pct = (unrealized_pl / total_cost) * 100
                else:
                    unrealized_pl_pct = 0
            
            result.append({
                'id': item.id,
                'symbol': item.symbol,
                'company_name': quote.get('name') if quote else item.company_name,
                'quantity': item.quantity,
                'purchase_price': item.purchase_price,
                'purchase_date': item.purchase_date.strftime('%Y-%m-%d') if item.purchase_date else None,
                'total_cost': total_cost,
                'current_price': current_price,
                'current_value': current_value,
                'unrealized_pl': unrealized_pl,
                'unrealized_pl_pct': unrealized_pl_pct,
                'currency': quote.get('currency') if quote else item.currency,
                'error': 'Could not fetch current live data' if not quote else None
            })
        return jsonify(result)

    elif request.method == 'POST':
        data = request.get_json()
        if not data or 'symbol' not in data or 'quantity' not in data:
            return jsonify({'error': 'Symbol and quantity are required'}), 400
            
        transaction_type = data.get('transaction_type', 'BUY').upper()
        if transaction_type not in ['BUY', 'SELL']:
            return jsonify({'error': 'Invalid transaction type'}), 400

        try:
            quantity = float(data['quantity'])
            price = float(data.get('purchase_price') or data.get('price', 0))
            if quantity <= 0 or price <= 0:
                raise ValueError()
        except ValueError:
            return jsonify({'error': 'Quantity and price must be > 0'}), 400
            
        symbol = data['symbol'].upper()
        
        # Verify symbol and get company info if BUY
        company_name = symbol
        currency = 'USD'
        if transaction_type == 'BUY':
            try:
                quote = get_stock_quote(symbol)
                company_name = quote.get('name', symbol)
                currency = quote.get('currency', 'USD')
            except Exception:
                return jsonify({'error': 'Invalid symbol or data unavailable'}), 400
            
        purchase_date = datetime.now(timezone.utc).date()
        if data.get('purchase_date'):
            try:
                purchase_date = datetime.strptime(data['purchase_date'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

        # Handle accounting
        item = PortfolioItem.query.filter_by(user_id=current_user.id, symbol=symbol).first()
        
        realized_pl = None
        
        if transaction_type == 'BUY':
            if item:
                # Calculate new average cost
                total_cost = (item.quantity * item.purchase_price) + (quantity * price)
                new_quantity = item.quantity + quantity
                item.purchase_price = total_cost / new_quantity
                item.quantity = new_quantity
            else:
                item = PortfolioItem(
                    user_id=current_user.id,
                    symbol=symbol,
                    company_name=company_name,
                    quantity=quantity,
                    purchase_price=price,
                    purchase_date=purchase_date,
                    currency=currency
                )
                db.session.add(item)
        elif transaction_type == 'SELL':
            if not item or item.quantity < quantity:
                return jsonify({'error': 'Not enough shares to sell'}), 400
            
            realized_pl = (price - item.purchase_price) * quantity
            item.quantity -= quantity
            if item.quantity == 0:
                db.session.delete(item)
                
        # Record transaction
        tx = PortfolioTransaction(
            user_id=current_user.id,
            symbol=symbol,
            transaction_type=transaction_type,
            quantity=quantity,
            price=price,
            transaction_date=purchase_date,
            realized_pl=realized_pl
        )
        db.session.add(tx)
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'Transaction {transaction_type} successful'})

@bp.route('/portfolio/transactions', methods=['GET'])
@login_required
def get_transactions():
    txs = PortfolioTransaction.query.filter_by(user_id=current_user.id).order_by(PortfolioTransaction.transaction_date.desc(), PortfolioTransaction.created_at.desc()).all()
    result = []
    for t in txs:
        result.append({
            'id': t.id,
            'symbol': t.symbol,
            'type': t.transaction_type,
            'quantity': t.quantity,
            'price': t.price,
            'date': t.transaction_date.strftime('%Y-%m-%d'),
            'realized_pl': t.realized_pl,
            'total_value': t.quantity * t.price
        })
    return jsonify(result)

@bp.route('/portfolio/<int:item_id>', methods=['PUT', 'DELETE'])
@login_required
def update_portfolio_item(item_id):
    item = PortfolioItem.query.filter_by(id=item_id, user_id=current_user.id).first()
    if not item:
        return jsonify({'error': 'Holding not found'}), 404
        
    if request.method == 'PUT':
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid payload'}), 400
            
        if 'quantity' in data:
            try:
                new_q = float(data['quantity'])
                if new_q < 0: raise ValueError()
                item.quantity = new_q
            except:
                return jsonify({'error': 'Invalid quantity'}), 400
        if 'purchase_price' in data:
            try:
                new_p = float(data['purchase_price'])
                if new_p < 0: raise ValueError()
                item.purchase_price = new_p
            except:
                return jsonify({'error': 'Invalid purchase price'}), 400
                
        db.session.commit()
        return jsonify({'success': True})
        
    elif request.method == 'DELETE':
        db.session.delete(item)
        db.session.commit()
        return jsonify({'success': True})

"""

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx != -1 and end_idx != -1:
    new_content = content[:start_idx] + new_portfolio_code + "\n" + content[end_idx:]
    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Updated portfolio routes successfully.")
else:
    print("Could not find markers to replace.")
