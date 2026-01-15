from functools import wraps
from flask import flash, redirect, url_for, abort
from flask_login import current_user


def admin_required(f):
    """
    Decorator to restrict route access to admin users only.
    Requires user to be authenticated and have 'admin' role.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('main.login'))
        
        if current_user.role != 'admin':
            flash('Access denied. Admin privileges required.', 'error')
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function


def vendor_required(f):
    """
    Decorator to restrict route access to vendor users only.
    Requires user to be authenticated and have 'vendor' role.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('main.login'))
        
        if current_user.role != 'vendor':
            flash('Access denied. Vendor privileges required.', 'error')
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function


def user_required(f):
    """
    Decorator to restrict route access to regular users only.
    Requires user to be authenticated and have 'user' role.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('main.login'))
        
        if current_user.role != 'user':
            flash('Access denied. User privileges required.', 'error')
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function
