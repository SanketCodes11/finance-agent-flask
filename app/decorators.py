from functools import wraps
from flask import abort, current_app
from flask_login import current_user

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin or not current_user.is_active:
            # Return 403 Forbidden instead of redirecting, as this is a secure admin area
            abort(403)
        return f(*args, **kwargs)
    return decorated_function
