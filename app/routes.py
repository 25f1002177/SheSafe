from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User
from app.decorators import admin_required, vendor_required, user_required

main = Blueprint('main', __name__)


@main.route('/')
def index():
    """Home page route."""
    return render_template('index.html')


@main.route('/register', methods=['GET', 'POST'])
def register():
    """User registration route."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        role = request.form.get('role', 'user')
        
        # Validation
        if not all([name, email, password, confirm_password]):
            flash('All fields are required.', 'error')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
            return render_template('register.html')
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return render_template('register.html')
        
        # Create new user
        user = User(name=name, email=email, role=role)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('main.login'))
    
    return render_template('register.html')


@main.route('/login', methods=['GET', 'POST'])
def login():
    """User login route."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not all([email, password]):
            flash('Email and password are required.', 'error')
            return render_template('login.html')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash(f'Welcome back, {user.name}!', 'success')
            
            # Redirect to next page or dashboard
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.dashboard'))
        else:
            flash('Invalid email or password.', 'error')
            return render_template('login.html')
    
    return render_template('login.html')


@main.route('/logout')
@login_required
def logout():
    """User logout route."""
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('main.index'))


@main.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard route - redirects to role-specific dashboard."""
    if current_user.role == 'admin':
        return redirect(url_for('main.admin_dashboard'))
    elif current_user.role == 'vendor':
        return redirect(url_for('main.vendor_dashboard'))
    else:
        return redirect(url_for('main.user_dashboard'))


@main.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """Admin dashboard (admin only)."""
    # Get all users for admin overview
    all_users = User.query.all()
    user_count = User.query.count()
    admin_count = User.query.filter_by(role='admin').count()
    vendor_count = User.query.filter_by(role='vendor').count()
    regular_user_count = User.query.filter_by(role='user').count()
    
    return render_template('admin_dashboard.html', 
                         user=current_user,
                         all_users=all_users,
                         user_count=user_count,
                         admin_count=admin_count,
                         vendor_count=vendor_count,
                         regular_user_count=regular_user_count)


@main.route('/vendor/dashboard')
@vendor_required
def vendor_dashboard():
    """Vendor dashboard (vendor only)."""
    return render_template('vendor_dashboard.html', user=current_user)


@main.route('/user/dashboard')
@user_required
def user_dashboard():
    """User dashboard (regular users only)."""
    return render_template('user_dashboard.html', user=current_user)
