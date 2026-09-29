import yfinance as yf
import pandas as pd
from datetime import datetime, date, timedelta, timezone
from app.models.finance import PortfolioTransaction, PortfolioItem
import logging
import threading
import time

logger = logging.getLogger(__name__)

# Cache historical data for 1 hour to prevent Yahoo Finance rate limits
# Key: (symbol, start_date_str, end_date_str) -> (timestamp, data_dict)
price_cache = {}
cache_lock = threading.Lock()

def fetch_historical_prices(symbol, start_date_str, end_date_str):
    """
    Fetches historical daily close prices for a symbol.
    Forward fills missing data (weekends, holidays).
    Returns a dict mapping string dates (YYYY-MM-DD) to float prices.
    """
    cache_key = (symbol, start_date_str, end_date_str)
    with cache_lock:
        if cache_key in price_cache:
            entry_time, data = price_cache[cache_key]
            if time.time() - entry_time < 3600:
                return data

    try:
        # Add 1 day to end_date to ensure it's inclusive in yf
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d') + timedelta(days=1)
        df = yf.download(symbol, start=start_date_str, end=end_date.strftime('%Y-%m-%d'), progress=False)
        
        if df.empty:
            with cache_lock:
                price_cache[cache_key] = (time.time(), {})
            return {}
            
        # Extract 'Close' column. Handle multi-index if yfinance returns it.
        if isinstance(df.columns, pd.MultiIndex):
            close_series = df['Close'][symbol]
        else:
            close_series = df['Close']
            
        # Reindex to include all calendar days (to fill weekends/holidays)
        all_days = pd.date_range(start=start_date_str, end=end_date_str, freq='D')
        close_series.index = close_series.index.tz_localize(None) # Remove tz for alignment
        
        # Filter duplicates if any
        close_series = close_series[~close_series.index.duplicated(keep='first')]
        
        # Reindex and forward fill
        reindexed = close_series.reindex(all_days, method='ffill')
        
        # Drop any remaining NaNs (e.g., if the first few days were holidays before IPO)
        reindexed = reindexed.bfill()
        
        # Convert to dict { 'YYYY-MM-DD': price }
        result = {k.strftime('%Y-%m-%d'): float(v) for k, v in reindexed.items() if pd.notna(v)}
        
        with cache_lock:
            price_cache[cache_key] = (time.time(), result)
            
        return result
    except Exception as e:
        logger.error(f"Error fetching historical prices for {symbol}: {e}")
        return {}

def calculate_portfolio_history(user_id, period='1M'):
    """
    Replays the user's transactions chronologically to build a daily portfolio value time series.
    """
    transactions = PortfolioTransaction.query.filter_by(user_id=user_id).order_by(PortfolioTransaction.transaction_date.asc(), PortfolioTransaction.id.asc()).all()
    
    if not transactions:
        return {
            'labels': [], 'market_values': [], 'invested_capital': [],
            'metrics': {'absolute_return': 0, 'percentage_return': 0, 'peak_value': 0, 'max_drawdown': 0}
        }
        
    first_tx_date = transactions[0].transaction_date
    today = date.today()
    
    # Determine output start date based on period
    if period == '1M':
        output_start = today - timedelta(days=30)
    elif period == '3M':
        output_start = today - timedelta(days=90)
    elif period == '6M':
        output_start = today - timedelta(days=180)
    elif period == '1Y':
        output_start = today - timedelta(days=365)
    else: # ALL
        output_start = first_tx_date
        
    # We must process from the first transaction date, even if output_start is later.
    process_start = min(first_tx_date, output_start)
    
    symbols = list(set(tx.symbol for tx in transactions))
    
    # Fetch price data
    price_data = {}
    for sym in symbols:
        price_data[sym] = fetch_historical_prices(sym, process_start.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d'))
        
    # Replay ledger
    holdings = {sym: 0.0 for sym in symbols}
    invested = {sym: 0.0 for sym in symbols}
    
    # Group transactions by date
    tx_by_date = {}
    for tx in transactions:
        d_str = tx.transaction_date.strftime('%Y-%m-%d')
        if d_str not in tx_by_date:
            tx_by_date[d_str] = []
        tx_by_date[d_str].append(tx)
        
    all_days = pd.date_range(start=process_start, end=today, freq='D')
    
    labels = []
    market_values = []
    invested_capital_series = []
    
    peak_value = 0.0
    max_drawdown = 0.0
    
    total_invested = 0.0
    
    for current_date in all_days:
        d_str = current_date.strftime('%Y-%m-%d')
        
        # Apply transactions for this day
        if d_str in tx_by_date:
            for tx in tx_by_date[d_str]:
                if tx.transaction_type == 'BUY':
                    holdings[tx.symbol] += float(tx.quantity)
                    cost = float(tx.quantity) * float(tx.price)
                    invested[tx.symbol] += cost
                    total_invested += cost
                elif tx.transaction_type == 'SELL':
                    qty_sold = float(tx.quantity)
                    if holdings[tx.symbol] > 0:
                        ratio = qty_sold / holdings[tx.symbol]
                        ratio = min(ratio, 1.0)
                        deducted_cost = invested[tx.symbol] * ratio
                        
                        holdings[tx.symbol] -= qty_sold
                        if holdings[tx.symbol] < 1e-6:
                            holdings[tx.symbol] = 0.0
                            
                        invested[tx.symbol] -= deducted_cost
                        total_invested -= deducted_cost
                        
        # Calculate end-of-day market value
        eod_value = 0.0
        for sym in symbols:
            if holdings[sym] > 0:
                price = price_data.get(sym, {}).get(d_str)
                if price is None:
                    past_prices = [p for d, p in price_data.get(sym, {}).items() if d <= d_str]
                    price = past_prices[-1] if past_prices else 0.0
                eod_value += holdings[sym] * price
                
        # Update peak and drawdown
        if eod_value > peak_value:
            peak_value = eod_value
            
        if peak_value > 0:
            drawdown = (peak_value - eod_value) / peak_value
            if drawdown > max_drawdown:
                max_drawdown = drawdown
                
        # Only save output if >= output_start
        if current_date.date() >= output_start:
            labels.append(d_str)
            market_values.append(round(eod_value, 2))
            invested_capital_series.append(round(total_invested, 2))
            
    if not market_values:
        return {
            'labels': [], 'market_values': [], 'invested_capital': [],
            'metrics': {'absolute_return': 0, 'percentage_return': 0, 'peak_value': 0, 'max_drawdown': 0}
        }
        
    final_value = market_values[-1]
    final_invested = invested_capital_series[-1]
    
    absolute_return = final_value - final_invested
    percentage_return = (absolute_return / final_invested * 100) if final_invested > 0 else 0.0
    
    return {
        'labels': labels,
        'market_values': market_values,
        'invested_capital': invested_capital_series,
        'metrics': {
            'absolute_return': round(absolute_return, 2),
            'percentage_return': round(percentage_return, 2),
            'peak_value': round(peak_value, 2),
            'max_drawdown': round(max_drawdown * 100, 2)
        }
    }
