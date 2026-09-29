import os
import math
from flask import Blueprint, render_template, request, Response, current_app, abort
from sqlalchemy import inspect, text
from app import db

bp = Blueprint('admin_db', __name__)

def check_auth(username, password):
    """Check if a username/password combination is valid."""
    admin_user = os.environ.get('ADMIN_USERNAME', 'admin')
    admin_pass = os.environ.get('ADMIN_PASSWORD', 'admin123')
    return username == admin_user and password == admin_pass

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Admin Login Required"'}
    )

def requires_auth(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        # Prevent access in production
        is_prod = current_app.config.get('ENV') == 'production' or os.environ.get('FLASK_ENV') == 'production'
        if is_prod:
            abort(404)
            
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

# Define columns that should never be shown in the UI
SENSITIVE_COLUMNS = ['password_hash', 'password', 'api_key', 'token', 'secret']

@bp.route('/admin/db')
@requires_auth
def index():
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    
    table_name = request.args.get('table')
    if not table_name and tables:
        table_name = tables[0]
        
    page = request.args.get('page', 1, type=int)
    search = request.args.get('q', '').strip()
    per_page = 20
    
    columns = []
    rows = []
    total_pages = 0
    total_records = 0
    
    if table_name and table_name in tables:
        # Get column names, filtering out sensitive ones
        all_columns = inspector.get_columns(table_name)
        columns = [col['name'] for col in all_columns if col['name'] not in SENSITIVE_COLUMNS]
        
        query_str = f"SELECT {', '.join(columns)} FROM {table_name}"
        count_query_str = f"SELECT COUNT(*) FROM {table_name}"
        params = {}
        
        if search:
            search_clauses = []
            for col in columns:
                search_clauses.append(f"CAST({col} AS TEXT) LIKE :search")
            if search_clauses:
                where_clause = " WHERE " + " OR ".join(search_clauses)
                query_str += where_clause
                count_query_str += where_clause
                params['search'] = f"%{search}%"
                
        # Get total records safely
        with db.engine.connect() as conn:
            total_records = conn.execute(text(count_query_str), params).scalar()
            
        total_pages = math.ceil(total_records / per_page)
        
        # Add pagination
        query_str += " LIMIT :limit OFFSET :offset"
        params['limit'] = per_page
        params['offset'] = (page - 1) * per_page
        
        # Get rows
        with db.engine.connect() as conn:
            result = conn.execute(text(query_str), params)
            rows = [dict(zip(columns, row)) for row in result]
            
    return render_template('admin/db_viewer.html', 
                           tables=tables, 
                           current_table=table_name,
                           columns=columns,
                           rows=rows,
                           page=page,
                           total_pages=total_pages,
                           total_records=total_records,
                           search=search)
