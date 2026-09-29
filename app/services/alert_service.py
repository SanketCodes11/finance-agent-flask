import logging
from datetime import datetime, timezone
from app import db
from app.models.finance import Alert
from app.services.finance_service import get_multiple_stock_quotes

logger = logging.getLogger(__name__)

def check_active_alerts(app):
    """
    Checks all active alerts against current stock prices.
    Designed to be run by a background scheduler or worker thread.
    """
    with app.app_context():
        # Get all active alerts
        active_alerts = Alert.query.filter_by(is_active=True).all()
        if not active_alerts:
            return

        # Extract unique symbols
        symbols = list(set([alert.symbol for alert in active_alerts]))
        
        # Batch fetch prices
        try:
            quotes = get_multiple_stock_quotes(symbols)
        except Exception as e:
            logger.error(f"Alert check failed to fetch quotes: {str(e)}")
            return

        triggered_count = 0
        for alert in active_alerts:
            quote = quotes.get(alert.symbol)
            if not quote or 'price' not in quote or quote['price'] is None:
                logger.warning(f"No price available for {alert.symbol} during alert check.")
                continue

            current_price = quote['price']
            is_triggered = False

            condition = alert.condition.upper()
            if condition == 'ABOVE' and current_price >= alert.target_price:
                is_triggered = True
            elif condition == 'BELOW' and current_price <= alert.target_price:
                is_triggered = True

            if is_triggered:
                alert.is_active = False
                alert.triggered_at = datetime.now(timezone.utc)
                logger.info(f"Alert TRIGGERED: {alert.symbol} went {alert.condition} {alert.target_price} (Current: {current_price}) for User {alert.user_id}")
                triggered_count += 1
                
        if triggered_count > 0:
            try:
                db.session.commit()
            except Exception as e:
                logger.error(f"Failed to commit triggered alerts: {str(e)}")
                db.session.rollback()
