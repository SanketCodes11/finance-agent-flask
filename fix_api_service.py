import re

# 1. Update app/api/screener.py to add status endpoint
with open('app/api/screener.py', 'r', encoding='utf-8') as f:
    api_content = f.read()

status_endpoint = """
@bp.route('/refresh/status', methods=['GET'])
@login_required
def get_refresh_status():
    from app.services.screener_service import _refresh_lock
    return jsonify({'is_running': _refresh_lock.locked()})
"""

if '/refresh/status' not in api_content:
    api_content += status_endpoint
    with open('app/api/screener.py', 'w', encoding='utf-8') as f:
        f.write(api_content)

# 2. Update app/services/screener_service.py to use yf.download for speed
with open('app/services/screener_service.py', 'r', encoding='utf-8') as f:
    service_content = f.read()

old_refresh = """                    try:
                        tickers = yf.Tickers(' '.join(batch))
                        
                        for sym in batch:
                            try:
                                ticker = tickers.tickers[sym]
                                
                                # We must handle possible API rate limit failures gently
                                fast = getattr(ticker, 'fast_info', {})
                                info = ticker.info if hasattr(ticker, 'info') else {}
                                
                                # Get DB object
                                sc = StockCache.query.filter_by(symbol=sym).first()
                                if not sc:
                                    continue
                                
                                # Update fields safely
                                sc.company_name = info.get('shortName') or info.get('longName') or sc.company_name
                                sc.sector = info.get('sector') or sc.sector
                                
                                # Prefer fast_info for market numbers
                                if 'lastPrice' in fast and fast['lastPrice'] is not None:
                                    sc.price = Decimal(str(fast['lastPrice']))
                                elif info.get('currentPrice') is not None:
                                    sc.price = Decimal(str(info.get('currentPrice')))
                                    
                                if 'marketCap' in fast and fast['marketCap'] is not None:
                                    sc.market_cap = Decimal(str(fast['marketCap']))
                                elif info.get('marketCap') is not None:
                                    sc.market_cap = Decimal(str(info.get('marketCap')))
                                    
                                if info.get('trailingPE') is not None:
                                    sc.pe_ratio = Decimal(str(info.get('trailingPE')))
                                    
                                if 'lastVolume' in fast and fast['lastVolume'] is not None:
                                    sc.volume = int(fast['lastVolume'])
                                elif info.get('volume') is not None:
                                    sc.volume = int(info.get('volume'))
                                    
                                sc.last_updated = datetime.now(timezone.utc)
                                
                            except Exception as e:
                                logger.error(f"Error processing {sym} during refresh: {e}")
                                
                        db.session.commit()
                        logger.info(f"Refreshed batch {i//batch_size + 1}")
                        
                    except Exception as batch_err:"""

new_refresh = """                    try:
                        import numpy as np
                        import pandas as pd
                        
                        # Use yf.download for extremely fast bulk price/volume fetching
                        # This returns a DataFrame with MultiIndex columns (Price, Ticker)
                        dl_data = yf.download(batch, period="1d", group_by="ticker", threads=True, progress=False)
                        
                        # Fallback for info fields
                        tickers = yf.Tickers(' '.join(batch))
                        
                        for sym in batch:
                            try:
                                sc = StockCache.query.filter_by(symbol=sym).first()
                                if not sc:
                                    continue
                                    
                                # 1. Extract Price and Volume from the bulk download DataFrame
                                if not dl_data.empty:
                                    try:
                                        # If only 1 ticker in batch, yfinance returns flat columns, otherwise MultiIndex
                                        if len(batch) == 1:
                                            sym_data = dl_data
                                        else:
                                            sym_data = dl_data[sym] if sym in dl_data.columns.levels[0] else None
                                            
                                        if sym_data is not None and not sym_data.empty:
                                            close_val = sym_data['Close'].iloc[-1]
                                            vol_val = sym_data['Volume'].iloc[-1]
                                            
                                            if pd.notna(close_val):
                                                sc.price = Decimal(str(float(close_val)))
                                            if pd.notna(vol_val):
                                                sc.volume = int(vol_val)
                                    except Exception as dl_e:
                                        logger.warning(f"Failed to parse bulk download for {sym}: {dl_e}")

                                # 2. Extract Market Cap, PE, Sector via fast_info/info
                                ticker = tickers.tickers[sym]
                                fast = getattr(ticker, 'fast_info', {})
                                info = ticker.info if hasattr(ticker, 'info') else {}
                                
                                sc.company_name = info.get('shortName') or info.get('longName') or sc.company_name
                                sc.sector = info.get('sector') or sc.sector
                                
                                # Fallback price if download failed
                                if sc.price is None:
                                    if 'lastPrice' in fast and pd.notna(fast['lastPrice']):
                                        sc.price = Decimal(str(fast['lastPrice']))
                                    elif info.get('currentPrice') is not None:
                                        sc.price = Decimal(str(info.get('currentPrice')))
                                        
                                if 'marketCap' in fast and pd.notna(fast['marketCap']):
                                    sc.market_cap = Decimal(str(fast['marketCap']))
                                elif info.get('marketCap') is not None:
                                    sc.market_cap = Decimal(str(info.get('marketCap')))
                                    
                                if info.get('trailingPE') is not None:
                                    sc.pe_ratio = Decimal(str(info.get('trailingPE')))
                                    
                                if sc.volume is None:
                                    if 'lastVolume' in fast and pd.notna(fast['lastVolume']):
                                        sc.volume = int(fast['lastVolume'])
                                    elif info.get('volume') is not None:
                                        sc.volume = int(info.get('volume'))
                                        
                                sc.last_updated = datetime.now(timezone.utc)
                                
                            except Exception as e:
                                logger.error(f"Error processing {sym} during refresh: {e}")
                                
                        db.session.commit()
                        logger.info(f"Refreshed batch {i//batch_size + 1}")
                        
                    except Exception as batch_err:"""

if "dl_data = yf.download" not in service_content:
    service_content = service_content.replace(old_refresh, new_refresh)
    with open('app/services/screener_service.py', 'w', encoding='utf-8') as f:
        f.write(service_content)

