# Stock Screener Bug Fix Report

## Overview
This report documents the root causes and implemented fixes for the two bugs reported on the Stock Screener page. The application was inspected and patched without modifying any database tables, removing features, or altering the application architecture.

## Bug A: Watchlist JSON Parsing Error
**Symptom:**
Clicking "Add to Watchlist" on the Screener page resulted in an alert: `Unexpected token '<', "<!DOCTYPE..." is not valid JSON.`

**Root Cause:**
1. The frontend JavaScript in `screener.html` was incorrectly configured to send `POST` requests to `/api/watchlist/add`.
2. The actual API endpoint defined in `app/api/finance.py` is strictly `/api/watchlist`.
3. Because the `/api/watchlist/add` route did not exist, Flask triggered a `404 Not Found` error.
4. The 404 error handler returned the HTML template `errors/404.html` (starting with `<!DOCTYPE html>`).
5. The `fetch` promise blindly attempted to parse this HTML string via `res.json()`, causing a JavaScript SyntaxError.

**Fix:**
1. Changed the `fetch` URL in `screener.html` from `/api/watchlist/add` to the correct endpoint `/api/watchlist`.
2. Hardened the JSON parsing logic in `screener.html`. It now explicitly checks `res.headers.get('content-type')` for `application/json`. If an HTML error page is returned (e.g. 401 Unauthorized or 500 Server Error), it throws a safe error string instead of crashing.

## Bug B: Screener Metrics Showing Dashes (`--`)
**Symptom:**
The screener table displayed 96 stocks, but `Price`, `Market Cap`, `P/E`, and `Volume` all rendered as dashes (`--`).

**Root Cause:**
1. **Initial Seed Assumption:** When the database is empty, the server automatically seeds 96 starter stocks. However, these rows are inserted with `NULL` (None) for all financial metrics to prevent slowing down the initial startup.
2. **Missing UI Refresh Trigger:** The UI successfully loaded these 96 stocks but displayed dashes for `NULL` values. The user was expected to manually click "Refresh Data" to trigger a background fetch, but the UI gave no indication that a refresh was mandatory.
3. **Asynchronous UI Disconnect:** Even when a user clicked "Refresh Data", the backend spawned a background thread to fetch data via `yfinance`. The UI button spun for 3 seconds and then stopped, falsely implying completion. The table data was never re-fetched from the server to display the newly populated numbers.
4. **Performance Issues:** The original `yfinance` logic fetched ticker details sequentially, which was extremely slow and prone to rate-limiting failures, meaning the background thread often timed out or took up to a minute.

**Fix:**
1. **Bulk Download Optimization:** Rewrote `app/services/screener_service.py` to utilize `yf.download(batch, ...)` for fetching live Price and Volume data for all stocks simultaneously in a fraction of a second.
2. **Automatic UI Polling:** Updated `screener.html` to periodically ping a newly created `/api/screener/refresh/status` endpoint. The "Refresh Data" button now accurately reflects the true status of the background thread.
3. **Auto-Reload:** Once the backend thread finishes updating the SQLite database, the frontend automatically triggers `loadResults(1)` to repaint the table with the fresh, valid numbers without requiring a full browser refresh.
4. **Safe NaN Handling:** Ensure `pandas.isna()` checks prevent invalid math errors (`NaN`) from crashing the database commits.

## Local Verification Steps
1. Start the Flask server: `flask run`
2. Navigate to `http://localhost:5000/screener`.
3. If this is a fresh setup, you will see dashes initially.
4. Click **Refresh Data**. Notice the button stays in the "Updating Database..." state until the backend actually finishes.
5. Watch the table seamlessly auto-reload populated with accurate Prices, Market Caps, P/E ratios, and Volumes.
6. Click **Watch** next to a stock and verify it safely updates to a green "Added" state without any alert popups.
