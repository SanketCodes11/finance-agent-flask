with open('app/templates/screener.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix Bug A endpoint
content = content.replace("fetch('/api/watchlist/add'", "fetch('/api/watchlist'")

# Improve addToWatchlist JSON parsing safety
old_js = """
        fetch('/api/watchlist', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
            },
            body: JSON.stringify({ symbol: symbol })
        })
        .then(res => res.json())
        .then(data => {
"""

new_js = """
        fetch('/api/watchlist', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
            },
            body: JSON.stringify({ symbol: symbol })
        })
        .then(async res => {
            const contentType = res.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                const text = await res.text();
                throw new Error(res.status === 401 ? 'Unauthorized. Please login.' : 'Server returned an invalid non-JSON response.');
            }
            return res.json();
        })
        .then(data => {
"""
content = content.replace(old_js, new_js)

# Fix Bug B polling
old_refresh = """
    function triggerRefresh() {
        const btn = document.getElementById('refreshBtn');
        const originalText = btn.innerHTML;
        btn.innerHTML = `<span class="spinner-border spinner-border-sm me-1"></span> Starting...`;
        btn.disabled = true;

        fetch('/api/screener/refresh', {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
            }
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                btn.innerHTML = `<i class="fa-solid fa-check text-success me-1"></i> Running`;
                setTimeout(() => {
                    btn.innerHTML = originalText;
                    btn.disabled = false;
                }, 3000);
            } else {
                throw new Error(data.message || 'Failed to start refresh.');
            }
        })
        .catch(err => {
            alert('Error: ' + err.message);
            btn.innerHTML = originalText;
            btn.disabled = false;
        });
    }
"""

new_refresh = """
    let refreshInterval = null;

    function pollRefreshStatus() {
        const btn = document.getElementById('refreshBtn');
        fetch('/api/screener/refresh/status')
        .then(res => res.json())
        .then(data => {
            if (data.is_running) {
                btn.innerHTML = `<span class="spinner-border spinner-border-sm me-1"></span> Updating Database...`;
                btn.disabled = true;
                if (!refreshInterval) {
                    refreshInterval = setInterval(pollRefreshStatus, 3000);
                }
            } else {
                if (refreshInterval) {
                    clearInterval(refreshInterval);
                    refreshInterval = null;
                    btn.innerHTML = `<i class="fa-solid fa-check text-success me-1"></i> Refreshed!`;
                    setTimeout(() => {
                        btn.innerHTML = `<i class="fa-solid fa-rotate-right me-1"></i> Refresh Data`;
                        btn.disabled = false;
                    }, 2000);
                    loadResults(1); // Reload table with new data
                } else {
                    btn.innerHTML = `<i class="fa-solid fa-rotate-right me-1"></i> Refresh Data`;
                    btn.disabled = false;
                }
            }
        });
    }

    // Call once on load in case it's already running
    document.addEventListener('DOMContentLoaded', () => {
        pollRefreshStatus();
    });

    function triggerRefresh() {
        const btn = document.getElementById('refreshBtn');
        btn.innerHTML = `<span class="spinner-border spinner-border-sm me-1"></span> Starting...`;
        btn.disabled = true;

        fetch('/api/screener/refresh', {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
            }
        })
        .then(async res => {
            const ct = res.headers.get('content-type');
            if (!ct || !ct.includes('application/json')) throw new Error('Invalid response');
            return res.json();
        })
        .then(data => {
            if (data.success || res.status === 429) {
                pollRefreshStatus();
            } else {
                throw new Error(data.message || data.error || 'Failed to start refresh.');
            }
        })
        .catch(err => {
            alert('Error: ' + err.message);
            btn.innerHTML = `<i class="fa-solid fa-rotate-right me-1"></i> Refresh Data`;
            btn.disabled = false;
        });
    }
"""
content = content.replace(old_refresh, new_refresh)

with open('app/templates/screener.html', 'w', encoding='utf-8') as f:
    f.write(content)
