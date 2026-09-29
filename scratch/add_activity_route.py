import os

with open('app/routes/admin.py', 'r', encoding='utf-8') as f:
    content = f.read()

route_code = '''
from sqlalchemy import text
import math

@bp.route('/activity')
@login_required
@admin_required
def activity():
    """Live Activity & Audit Center."""
    page = request.args.get('page', 1, type=int)
    search_user = request.args.get('user', '').strip()
    search_event = request.args.get('event', '').strip()
    per_page = 20
    
    # Base unified query
    base_query = """
    SELECT 
        u.username,
        u.email,
        a.user_id,
        a.event_type,
        a.details,
        a.ip_address,
        a.event_time,
        a.source
    FROM (
        SELECT admin_id as user_id, action as event_type, details, ip_address, timestamp as event_time, 'Admin Log' as source FROM admin_audit_log
        UNION ALL
        SELECT user_id, 'login' as event_type, user_agent as details, ip_address, login_time as event_time, 'Login' as source FROM login_history
        UNION ALL
        SELECT user_id, 'stock_search' as event_type, symbol as details, NULL as ip_address, searched_at as event_time, 'Search' as source FROM search_history
        UNION ALL
        SELECT user_id, event_type, details, ip_address, timestamp as event_time, 'Activity' as source FROM activity_log
    ) a
    JOIN user u ON u.id = a.user_id
    """
    
    count_query = """
    SELECT COUNT(*) FROM (
        SELECT admin_id as user_id, action as event_type FROM admin_audit_log
        UNION ALL
        SELECT user_id, 'login' as event_type FROM login_history
        UNION ALL
        SELECT user_id, 'stock_search' as event_type FROM search_history
        UNION ALL
        SELECT user_id, event_type FROM activity_log
    ) a
    JOIN user u ON u.id = a.user_id
    """
    
    params = {}
    where_clauses = []
    
    if search_user:
        where_clauses.append("(u.username LIKE :user OR u.email LIKE :user)")
        params['user'] = f"%{search_user}%"
        
    if search_event:
        where_clauses.append("a.event_type LIKE :event")
        params['event'] = f"%{search_event}%"
        
    if where_clauses:
        where_str = " WHERE " + " AND ".join(where_clauses)
        base_query += where_str
        count_query += where_str
        
    # Get total records safely
    with db.engine.connect() as conn:
        total_records = conn.execute(text(count_query), params).scalar()
        
    total_pages = math.ceil(total_records / per_page)
    
    # Add ordering and pagination
    base_query += " ORDER BY a.event_time DESC LIMIT :limit OFFSET :offset"
    params['limit'] = per_page
    params['offset'] = (page - 1) * per_page
    
    # Get rows
    activities = []
    with db.engine.connect() as conn:
        result = conn.execute(text(base_query), params)
        activities = [dict(zip(result.keys(), row)) for row in result]
        
    return render_template('admin/activity.html', 
                           activities=activities,
                           page=page,
                           total_pages=total_pages,
                           total_records=total_records,
                           search_user=search_user,
                           search_event=search_event)
'''

if '@bp.route(\'/activity\')' not in content:
    content += '\n' + route_code
    with open('app/routes/admin.py', 'w', encoding='utf-8') as f:
        f.write(content)
