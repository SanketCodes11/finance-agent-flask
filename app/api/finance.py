from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app.services.portfolio_analytics_service import calculate_portfolio_history
from app.services.finance_service import get_stock_quote, get_stock_history, get_financial_news, search_stocks
from app.models.finance import Watchlist, SearchHistory, PortfolioItem, Alert, PortfolioTransaction, PlatformSetting
from app import db
import yfinance as yf
from datetime import datetime, timezone

bp = Blueprint('api', __name__)

@bp.route('/stock/autocomplete', methods=['GET'])
@login_required
def autocomplete_stock():
    query = request.args.get('q', '').strip()
    if len(query) < 2:
        return jsonify([])
    try:
        results = search_stocks(query)
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/stock/search', methods=['GET'])
@login_required
def search_stock():
    symbol = request.args.get('q', '').strip().upper()
    if not symbol:
        return jsonify({'error': 'Symbol is required'}), 400
        
    try:
        quote_data = get_stock_quote(symbol)
        
        # Save to search history
        existing = SearchHistory.query.filter_by(user_id=current_user.id, symbol=symbol).first()
        if not existing:
            new_search = SearchHistory(user_id=current_user.id, symbol=symbol)
            db.session.add(new_search)
        else:
            existing.searched_at = db.func.now()
        db.session.commit()
        
        return jsonify(quote_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@bp.route('/stock/history', methods=['GET'])
@login_required
def stock_history():
    symbol = request.args.get('symbol', '').strip().upper()
    period = request.args.get('period', '1mo')
    
    if not symbol:
        return jsonify({'error': 'Symbol is required'}), 400
        
    try:
        history_data = get_stock_history(symbol, period)
        import logging
        logging.info(f"API /stock/history SUCCESS: symbol={symbol}, period={period}, candles={len(history_data.get('timestamps', []))}")
        return jsonify(history_data)
    except Exception as e:
        import logging
        logging.error(f"API /stock/history ERROR: symbol={symbol}, period={period}, error={str(e)}")
        return jsonify({'error': str(e)}), 400

@bp.route('/market_indices', methods=['GET'])
@login_required
def market_indices():
    symbols = ['^GSPC', '^NSEI', '^DJI', '^IXIC']
    try:
        from app.services.finance_service import get_multiple_stock_quotes
        quotes = get_multiple_stock_quotes(symbols)
        result = []
        for sym in symbols:
            if sym in quotes:
                # Rename the symbols for better UI display
                name = quotes[sym].get('name')
                if sym == '^GSPC': name = 'S&P 500'
                elif sym == '^NSEI': name = 'NIFTY 50'
                elif sym == '^DJI': name = 'Dow Jones'
                elif sym == '^IXIC': name = 'NASDAQ'
                
                result.append({
                    'symbol': sym,
                    'name': name,
                    'price': quotes[sym].get('price'),
                    'change': quotes[sym].get('change'),
                    'change_percent': quotes[sym].get('change_percent')
                })
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

from app.services.portfolio_analytics_service import calculate_portfolio_history
from app.services.finance_service import get_stock_quote, get_stock_history, get_financial_news, search_stocks, get_multiple_stock_quotes

@bp.route('/watchlist', methods=['GET', 'POST', 'DELETE'])
@login_required
def manage_watchlist():
    if request.method == 'GET':
        items = Watchlist.query.filter_by(user_id=current_user.id).order_by(Watchlist.added_at.desc()).all()
        symbols = [item.symbol for item in items]
        
        quotes = get_multiple_stock_quotes(symbols)
        
        result = []
        for item in items:
            quote = quotes.get(item.symbol)
            if quote:
                result.append({
                    'symbol': item.symbol,
                    'name': quote.get('name') or item.company_name,
                    'price': quote.get('price'),
                    'change': quote.get('change'),
                    'change_percent': quote.get('change_percent'),
                    'currency': quote.get('currency') or item.currency,
                    'inr_price': quote.get('inr_price'),
                    'exchange': quote.get('exchange') or item.exchange
                })
            else:
                # Fallback to DB info
                result.append({
                    'symbol': item.symbol,
                    'name': item.company_name,
                    'currency': item.currency,
                    'exchange': item.exchange,
                    'error': 'Could not fetch current live data'
                })
        return jsonify(result)
        
    elif request.method == 'POST':
        data = request.get_json()
        if not data or 'symbol' not in data:
            return jsonify({'error': 'Symbol is required'}), 400
            
        symbol = data['symbol'].upper()
        if Watchlist.query.filter_by(user_id=current_user.id, symbol=symbol).first():
            return jsonify({'error': 'Symbol already in watchlist'}), 400
            
        try:
            quote = get_stock_quote(symbol)
            company_name = quote.get('name')
            exchange = quote.get('exchange')
            currency = quote.get('currency')
        except:
            return jsonify({'error': 'Invalid symbol or data unavailable'}), 400
            
        new_item = Watchlist(
            user_id=current_user.id, 
            symbol=symbol,
            company_name=company_name,
            exchange=exchange,
            currency=currency
        )
        db.session.add(new_item)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Added to watchlist'})
        
    elif request.method == 'DELETE':
        data = request.get_json()
        if not data or 'symbol' not in data:
            return jsonify({'error': 'Symbol is required'}), 400
            
        symbol = data['symbol'].upper()
        item = Watchlist.query.filter_by(user_id=current_user.id, symbol=symbol).first()
        if not item:
            return jsonify({'error': 'Symbol not found in watchlist'}), 404
            
        db.session.delete(item)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Removed from watchlist'})

from app.services.portfolio_analytics_service import calculate_portfolio_history
from app.services.finance_service import get_stock_quote, get_stock_history, get_financial_news, search_stocks, get_multiple_stock_quotes, NewsAPIError, NewsNotConfiguredError
from app.services.ai_service import fetch_agent_insight

@bp.route('/news', methods=['GET'])
@login_required
def get_news():
    query = request.args.get('q', 'finance')
    try:
        news = get_financial_news(query)
        return jsonify({'articles': news})
    except NewsNotConfiguredError as e:
        return jsonify({'error': str(e), 'not_configured': True}), 503
    except NewsAPIError as e:
        return jsonify({'error': str(e)}), 502
    except Exception as e:
        return jsonify({'error': 'An unexpected error occurred.'}), 500

@bp.route('/agent/ask', methods=['POST'])
@login_required
def ask_agent():
    settings = PlatformSetting.get_settings()
    if not settings.ai_analyst_enabled and not current_user.is_admin:
        return jsonify({'error': 'AI Analyst is temporarily disabled by the administrator. Please check back later.'}), 403

    data = request.get_json()
    if not data or 'query' not in data:
        return jsonify({'error': 'Query is required'}), 400
        
    query = data['query']
    history = data.get('history', [])
    try:
        insight = fetch_agent_insight(query, history)
        return jsonify({'response': insight})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/portfolio', methods=['GET', 'POST'])
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
            price = float(data.get('purchase_price') if data.get('purchase_price') is not None else data.get('price', 0))
            if quantity <= 0 or price < 0:
                raise ValueError()
        except ValueError:
            return jsonify({'error': 'Quantity must be > 0 and purchase price must be >= 0'}), 400
            
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


@bp.route('/alerts', methods=['GET', 'POST'])
@login_required
def manage_alerts():
    if request.method == 'GET':
        alerts = Alert.query.filter_by(user_id=current_user.id).all()
        return jsonify([{'id': a.id, 'symbol': a.symbol, 'condition': a.condition, 'target_price': a.target_price, 'is_active': a.is_active, 'triggered_at': a.triggered_at.strftime('%Y-%m-%d %H:%M:%S') if a.triggered_at else None} for a in alerts])
    
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
