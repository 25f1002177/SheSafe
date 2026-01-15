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
    from app.models import Vendor
    
    # Get all users for admin overview
    all_users = User.query.all()
    user_count = User.query.count()
    admin_count = User.query.filter_by(role='admin').count()
    vendor_count = User.query.filter_by(role='vendor').count()
    regular_user_count = User.query.filter_by(role='user').count()
    
    # Get all vendors
    all_vendors = Vendor.query.all()
    pending_vendors = Vendor.query.filter_by(is_verified=False).all()
    verified_vendors = Vendor.query.filter_by(is_verified=True).all()
    
    return render_template('admin_dashboard.html', 
                         user=current_user,
                         all_users=all_users,
                         user_count=user_count,
                         admin_count=admin_count,
                         vendor_count=vendor_count,
                         regular_user_count=regular_user_count,
                         all_vendors=all_vendors,
                         pending_vendors=pending_vendors,
                         verified_vendors=verified_vendors)


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


@main.route('/vendor/onboard', methods=['GET', 'POST'])
@vendor_required
def vendor_onboard():
    """Vendor onboarding form."""
    from app.models import Vendor
    from datetime import datetime, time
    
    # Check if vendor already has a profile
    if current_user.vendor_profile:
        flash('You have already completed vendor onboarding.', 'info')
        return redirect(url_for('main.vendor_dashboard'))
    
    if request.method == 'POST':
        business_name = request.form.get('business_name')
        description = request.form.get('description')
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        address = request.form.get('address')
        has_cctv = request.form.get('has_cctv') == 'on'
        has_female_staff = request.form.get('has_female_staff') == 'on'
        female_staff_start_time = request.form.get('female_staff_start_time')
        female_staff_end_time = request.form.get('female_staff_end_time')
        
        # Validation
        if not all([business_name, latitude, longitude, address]):
            flash('Business name, latitude, longitude, and address are required.', 'error')
            return render_template('vendor_onboard.html')
        
        try:
            latitude = float(latitude)
            longitude = float(longitude)
        except ValueError:
            flash('Latitude and longitude must be valid numbers.', 'error')
            return render_template('vendor_onboard.html')
        
        # Parse time fields if female staff is available
        start_time = None
        end_time = None
        if has_female_staff and female_staff_start_time and female_staff_end_time:
            try:
                start_time = datetime.strptime(female_staff_start_time, '%H:%M').time()
                end_time = datetime.strptime(female_staff_end_time, '%H:%M').time()
            except ValueError:
                flash('Invalid time format for staff timing.', 'error')
                return render_template('vendor_onboard.html')
        
        # Create vendor profile
        vendor = Vendor(
            user_id=current_user.id,
            business_name=business_name,
            description=description if description else None,
            latitude=latitude,
            longitude=longitude,
            address=address,
            has_cctv=has_cctv,
            has_female_staff=has_female_staff,
            female_staff_start_time=start_time,
            female_staff_end_time=end_time,
            is_verified=False,
            is_active=False,
            average_rating=0.0
        )
        
        db.session.add(vendor)
        db.session.commit()
        
        flash('Vendor profile created successfully! Your profile is pending verification.', 'success')
        return redirect(url_for('main.vendor_dashboard'))
    
    return render_template('vendor_onboard.html')


@main.route('/admin/vendor/<int:vendor_id>/approve', methods=['POST'])
@admin_required
def approve_vendor(vendor_id):
    """Approve a vendor (admin only)."""
    from app.models import Vendor
    
    vendor = Vendor.query.get_or_404(vendor_id)
    vendor.is_verified = True
    vendor.is_active = True
    
    db.session.commit()
    
    flash(f'Vendor "{vendor.business_name}" has been approved and activated.', 'success')
    return redirect(url_for('main.admin_dashboard'))


@main.route('/admin/vendor/<int:vendor_id>/reject', methods=['POST'])
@admin_required
def reject_vendor(vendor_id):
    """Reject a vendor (admin only)."""
    from app.models import Vendor
    
    vendor = Vendor.query.get_or_404(vendor_id)
    business_name = vendor.business_name
    
    db.session.delete(vendor)
    db.session.commit()
    
    flash(f'Vendor "{business_name}" has been rejected and removed.', 'warning')
    return redirect(url_for('main.admin_dashboard'))


@main.route('/admin/vendor/<int:vendor_id>/disable', methods=['POST'])
@admin_required
def disable_vendor(vendor_id):
    """Disable a vendor (admin only)."""
    from app.models import Vendor
    
    vendor = Vendor.query.get_or_404(vendor_id)
    vendor.is_active = False
    
    db.session.commit()
    
    flash(f'Vendor "{vendor.business_name}" has been disabled.', 'info')
    return redirect(url_for('main.admin_dashboard'))
