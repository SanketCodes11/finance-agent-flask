from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user
from app.models.finance import StockCache, Watchlist
from app.services.screener_service import refresh_stock_cache, seed_stock_universe
from app import db
import logging
from sqlalchemy import asc, desc

bp = Blueprint('screener', __name__)
logger = logging.getLogger(__name__)

@bp.route('/results', methods=['GET'])
@login_required
def get_results():
    try:
        # Seed if empty (just a safety check for first run)
        if db.session.query(StockCache).count() == 0:
            seed_stock_universe()
            
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        if per_page > 100:
            per_page = 100
            
        query = StockCache.query
        
        # Filters
        exchange = request.args.get('exchange')
        if exchange:
            query = query.filter(StockCache.exchange == exchange.upper())
            
        sector = request.args.get('sector')
        if sector:
            query = query.filter(StockCache.sector == sector)
            
        min_price = request.args.get('min_price', type=float)
        if min_price is not None:
            query = query.filter(StockCache.price >= min_price)
            
        max_price = request.args.get('max_price', type=float)
        if max_price is not None:
            query = query.filter(StockCache.price <= max_price)
            
        min_cap = request.args.get('min_cap', type=float)
        if min_cap is not None:
            query = query.filter(StockCache.market_cap >= min_cap)
            
        max_cap = request.args.get('max_cap', type=float)
        if max_cap is not None:
            query = query.filter(StockCache.market_cap <= max_cap)
            
        min_pe = request.args.get('min_pe', type=float)
        if min_pe is not None:
            query = query.filter(StockCache.pe_ratio >= min_pe)
            
        max_pe = request.args.get('max_pe', type=float)
        if max_pe is not None:
            query = query.filter(StockCache.pe_ratio <= max_pe)
            
        min_vol = request.args.get('min_vol', type=int)
        if min_vol is not None:
            query = query.filter(StockCache.volume >= min_vol)
            
        search = request.args.get('search')
        if search:
            search_term = f"%{search}%"
            query = query.filter((StockCache.symbol.ilike(search_term)) | (StockCache.company_name.ilike(search_term)))
            
        # Sorting
        sort_by = request.args.get('sort_by', 'market_cap')
        sort_order = request.args.get('sort_order', 'desc')
        
        valid_sorts = {
            'symbol': StockCache.symbol,
            'price': StockCache.price,
            'market_cap': StockCache.market_cap,
            'pe_ratio': StockCache.pe_ratio,
            'volume': StockCache.volume
        }
        
        sort_col = valid_sorts.get(sort_by, StockCache.market_cap)
        
        if sort_order == 'asc':
            query = query.order_by(sort_col.asc().nulls_last())
        else:
            query = query.order_by(sort_col.desc().nulls_last())
            
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Determine watchlisted status for the user to show correctly in UI
        user_watchlisted = set(w.symbol for w in Watchlist.query.filter_by(user_id=current_user.id).all())
        
        results = []
        for item in pagination.items:
            results.append({
                'symbol': item.symbol,
                'company_name': item.company_name,
                'exchange': item.exchange,
                'sector': item.sector,
                'price': float(item.price) if item.price is not None else None,
                'market_cap': float(item.market_cap) if item.market_cap is not None else None,
                'pe_ratio': float(item.pe_ratio) if item.pe_ratio is not None else None,
                'volume': item.volume,
                'last_updated': item.last_updated.isoformat() if item.last_updated else None,
                'is_watchlisted': item.symbol in user_watchlisted
            })
            
        # Fetch distinct sectors for filter dropdowns
        sectors = [s[0] for s in db.session.query(StockCache.sector).distinct().filter(StockCache.sector.isnot(None)).all()]
            
        return jsonify({
            'results': results,
            'page': pagination.page,
            'pages': pagination.pages,
            'total': pagination.total,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev,
            'sectors': sorted(sectors)
        })
    except Exception as e:
        logger.error(f"Screener results error: {e}")
        return jsonify({'error': 'Failed to retrieve screener data.'}), 500

@bp.route('/refresh', methods=['POST'])
@login_required
def trigger_refresh():
    try:
        # Initial seed if empty
        if db.session.query(StockCache).count() == 0:
            seed_stock_universe()
            
        started = refresh_stock_cache(current_app._get_current_object())
        if started:
            return jsonify({'success': True, 'message': 'Cache refresh started in background.'})
        else:
            return jsonify({'success': False, 'message': 'Refresh is already in progress.'}), 429
    except Exception as e:
        logger.error(f"Failed to start refresh: {e}")
        return jsonify({'error': 'Failed to trigger refresh.'}), 500

@bp.route('/refresh/status', methods=['GET'])
@login_required
def get_refresh_status():
    from app.services.screener_service import _refresh_lock
    return jsonify({'is_running': _refresh_lock.locked()})
