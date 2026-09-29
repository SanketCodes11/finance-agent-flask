import yfinance as yf
from app.models.finance import StockCache
from app import db
from datetime import datetime, timezone
import logging
from decimal import Decimal
import threading

logger = logging.getLogger(__name__)

# Prevent overlapping background refresh jobs
_refresh_lock = threading.Lock()

STARTER_UNIVERSE = [
    # Prominent US Stocks
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK-B', 'LLY', 'V',
    'JPM', 'UNH', 'WMT', 'JNJ', 'MA', 'PG', 'AVGO', 'HD', 'CVX', 'MRK',
    'KO', 'PEP', 'COST', 'ABBV', 'ADBE', 'MCD', 'CSCO', 'CRM', 'BAC', 'ACN',
    'TMO', 'LIN', 'ABT', 'NFLX', 'DHR', 'AMD', 'TXN', 'CMCSA', 'NKE', 'INTC',
    'DIS', 'PFE', 'VZ', 'WFC', 'QCOM', 'IBM', 'PM', 'COP', 'HON', 'INTU',
    
    # Prominent Indian Stocks (NSE)
    'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'ICICIBANK.NS', 'INFY.NS', 'ITC.NS', 'SBIN.NS', 'BHARTIARTL.NS',
    'BAJFINANCE.NS', 'L&T.NS', 'HINDUNILVR.NS', 'KOTAKBANK.NS', 'AXISBANK.NS', 'LT.NS', 'ASIANPAINT.NS', 'MARUTI.NS',
    'HCLTECH.NS', 'SUNPHARMA.NS', 'TITAN.NS', 'ULTRACEMCO.NS', 'TATASTEEL.NS', 'NTPC.NS', 'POWERGRID.NS', 'BAJAJFINSV.NS',
    'ONGC.NS', 'M&M.NS', 'COALINDIA.NS', 'WIPRO.NS', 'JSWSTEEL.NS', 'GRASIM.NS', 'HDFCLIFE.NS', 'ADANIPORTS.NS',
    'SBILIFE.NS', 'TECHM.NS', 'TATAMOTORS.NS', 'INDUSINDBK.NS', 'BAJAJ-AUTO.NS', 'HINDALCO.NS', 'EICHERMOT.NS',
    'DRREDDY.NS', 'DIVISLAB.NS', 'CIPLA.NS', 'APOLLOHOSP.NS', 'BRITANNIA.NS', 'HEROMOTOCO.NS', 'TATACONSUM.NS',
]

def seed_stock_universe():
    """Ensure starter symbols exist in the DB."""
    existing = set(s[0] for s in db.session.query(StockCache.symbol).all())
    added = 0
    for sym in STARTER_UNIVERSE:
        if sym not in existing:
            # Basic defaults
            exchange = 'NSE' if sym.endswith('.NS') else 'US'
            sc = StockCache(symbol=sym, exchange=exchange)
            db.session.add(sc)
            added += 1
    
    if added > 0:
        db.session.commit()
        logger.info(f"Seeded {added} new symbols into StockCache.")
        
def refresh_stock_cache(app, batch_size=20):
    """
    Safely fetches and updates cache data for all stored symbols.
    Ensures only one refresh runs at a time.
    """
    if not _refresh_lock.acquire(blocking=False):
        logger.warning("Cache refresh is already running.")
        return False
        
    def _refresh_task(app_context):
        try:
            with app_context:
                # Fetch all symbols to update
                stocks = StockCache.query.all()
                symbols = [s.symbol for s in stocks]
                
                logger.info(f"Starting refresh of {len(symbols)} symbols...")
                
                for i in range(0, len(symbols), batch_size):
                    batch = symbols[i:i+batch_size]
                    try:
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
                        
                    except Exception as batch_err:
                        logger.error(f"Error in batch refresh: {batch_err}")
                        db.session.rollback()
                        
            logger.info("Stock cache refresh completed.")
        except Exception as e:
            logger.error(f"Critical error in refresh task: {e}")
        finally:
            _refresh_lock.release()

    thread = threading.Thread(target=_refresh_task, args=(app.app_context(),))
    thread.daemon = True
    thread.start()
    return True
