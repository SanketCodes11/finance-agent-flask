import threading
import time
import os
import logging
from app.services.alert_service import check_active_alerts

logger = logging.getLogger(__name__)

def run_scheduler(app):
    while True:
        try:
            check_active_alerts(app)
        except Exception as e:
            logger.error(f"Alert scheduler error: {e}")
        # Sleep for 60 seconds
        time.sleep(60)

def start_alert_scheduler(app):
    # Avoid running multiple threads if reloader is active
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.debug:
        thread = threading.Thread(target=run_scheduler, args=(app,), daemon=True)
        thread.start()
        logger.info("Alert background scheduler started.")
