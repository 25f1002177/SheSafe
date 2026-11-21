from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User
from app.decorators import admin_required, vendor_required, user_required
import os
import qrcode
import io
import base64

main = Blueprint('main', __name__)


@main.route('/')
def index():
    """Home route."""
    if current_user.is_authenticated:
        if current_user.role == 'vendor':
            return redirect(url_for('main.vendor_dashboard'))
        elif current_user.role == 'admin':
            return redirect(url_for('main.admin_dashboard'))
        else:
            return redirect(url_for('main.welcome_home'))
    
    from app.models import Vendor
    vendors = Vendor.query.filter_by(is_verified=True, is_active=True).all()
    return render_template('landing.html', vendors=vendors)


@main.route('/welcome')
@login_required
def welcome_home():
    """Authenticated homepage with a clearly labelled local pitch entry."""
    if request.args.get('area') == 'ashoka':
        from app.models import Vendor
        vendors = Vendor.query.filter_by(is_verified=True, is_active=True).all()
        return render_template('welcome_legacy.html', vendors=vendors)
    from app.demo_catalog import kgp_venues
    return render_template('welcome.html', venues=kgp_venues())


@main.route('/privacy')
def privacy():
    """Privacy policy page."""
    return render_template('privacy.html')


@main.route('/terms')
def terms():
    """Safety terms page."""
    return render_template('terms.html')


@main.route('/landing')
def landing():
    """Explicit landing page for guests."""
    from app.models import Vendor
    vendors = Vendor.query.filter_by(is_verified=True, is_active=True).all()
    return render_template('landing.html', vendors=vendors)


def is_seed_vendor(vendor):
    """True for seeded presentation vendors (accounts created by the populate scripts)."""
    email = (vendor.user.email if vendor.user else '') or ''
    return email.lower().endswith('@shesafe.com')


@main.route('/explore')
@login_required
def explore():
    """Closest verified washroom first (location driven). area=kgp is the real-place discovery
    catalog (not verified, no booking); area=ashoka is the demo listing area."""
    area = request.args.get('area')
    if area == 'kgp':
        from app.demo_catalog import kgp_venues
        return render_template('explore.html', venues=kgp_venues())
    from app.models import Vendor
    candidates = Vendor.query.filter_by(is_verified=True, is_active=True).all()
    is_demo = (area == 'ashoka')
    # Seeded presentation listings (accounts on the shesafe.com demo domain) are shown only in
    # explicit demo mode. Primary results use genuine verified vendors only.
    vendors = [v for v in candidates if is_seed_vendor(v) == is_demo]
    # Presentation listings (real nearby places with sample ratings) share the same map and
    # nearest-first ranking as vendors. They are plain listings: no booking and no verified badge.
    from app.demo_catalog import kgp_venues
    listings = [] if is_demo else kgp_venues()
    return render_template('explore_legacy.html', vendors=vendors, listings=listings, forced_area=is_demo)


@main.route('/demo/venue/<slug>')
@login_required
def kgp_demo_venue(slug):
    from flask import abort
    from app.demo_catalog import kgp_venues
    venue = next((v for v in kgp_venues() if v['slug'] == slug), None)
    if venue is None:
        abort(404)
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo
    default_visit = (datetime.now(ZoneInfo('Asia/Kolkata')) + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M')
    return render_template('demo_venue.html', venue=venue, default_visit=default_visit, fee=DEMO_BOOKING_FEE_INR)


@main.route('/ask-ai')
@login_required
def ask_ai():
    """Ask AI page. Hidden (404) unless an AI provider key is configured server-side."""
    import os
    ai_enabled = os.environ.get('AI_ENABLED') == '1' and any(
        os.environ.get(k) for k in ('GEMINI_API_KEY', 'OPENROUTER_API_KEY', 'NVIDIA_API_KEY', 'SILICONFLOW_API_KEY'))
    if not ai_enabled:
        return render_template('ask_ai_unavailable.html'), 200
    return render_template('ask_ai.html')


@main.route('/register', methods=['GET', 'POST'])
def register():
    """User registration route."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'GET' and request.args.get('role') == 'vendor':
        return redirect(url_for('main.register_vendor'))
    if request.method == 'GET' and request.args.get('role') == 'user':
        return redirect(url_for('main.register_customer'))
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        role = request.form.get('role', 'user')
        
        # Security: Prevent admin registration via form
        if role not in ['user', 'vendor']:
            role = 'user'
        
        # Validation
        if not all([name, email, password, confirm_password]):
            flash('All fields are required.', 'error')
            return _register_page(role)
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return _register_page(role)
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
            return _register_page(role)
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return _register_page(role)
        
        # Create new user
        user = User(name=name, email=email, role=role)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('main.login'))
    
    return render_template('register_choice.html')


@main.route('/register/customer')
def register_customer():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return _register_page('user')


@main.route('/register/vendor')
def register_vendor():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return _register_page('vendor')


def _register_page(role):
    return render_template('register.html', role=role if role in ('user', 'vendor') else 'user')


@main.route('/login', methods=['GET', 'POST'])
def login():
    """User login route."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        print(f"DEBUG: Login attempt - Email: {email}")  # Debug
        
        if not all([email, password]):
            flash('Email and password are required.', 'error')
            return render_template('login.html')
        
        user = User.query.filter_by(email=email).first()
        
        print(f"DEBUG: User found: {user is not None}")  # Debug
        if user:
            print(f"DEBUG: User role: {user.role}")  # Debug
            print(f"DEBUG: Password check: {user.check_password(password)}")  # Debug
        
        if user and user.check_password(password):
            login_user(user)
            flash(f'Welcome back, {user.name}!', 'success')
            
            # Redirect to next page or dashboard; only same-site paths are honored
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/') and not next_page.startswith('//'):
                return redirect(next_page)
            
            if user.role == 'admin':
                return redirect(url_for('main.admin_dashboard'))
            elif user.role == 'vendor':
                return redirect(url_for('main.vendor_dashboard'))
            else:
                return redirect(url_for('main.welcome_home'))
                
        flash('Invalid email or password.', 'error')
        
    return render_template('login.html')


@main.route('/login/google')
def login_google():
    """Start Google OAuth sign-in."""
    if not current_app.config.get('GOOGLE_OAUTH_ENABLED'):
        flash('Google sign-in is not available right now. Please use email.', 'info')
        return redirect(url_for('main.login'))
    import secrets
    state = secrets.token_urlsafe(24)
    session['google_oauth_state'] = state
    # Role intent only applies when this sign-in creates a brand-new account.
    session['google_role_intent'] = 'vendor' if request.args.get('role') == 'vendor' else 'user'
    params = {
        'client_id': current_app.config['GOOGLE_CLIENT_ID'],
        'redirect_uri': url_for('main.auth_google_callback', _external=True),
        'response_type': 'code',
        'scope': 'openid email profile',
        'state': state,
        'prompt': 'select_account',
    }
    from urllib.parse import urlencode
    return redirect('https://accounts.google.com/o/oauth2/v2/auth?' + urlencode(params))


@main.route('/auth/google/callback')
def auth_google_callback():
    """Complete Google OAuth sign-in: verify, find-or-create user, log in."""
    if not current_app.config.get('GOOGLE_OAUTH_ENABLED'):
        return redirect(url_for('main.login'))
    if request.args.get('state') != session.pop('google_oauth_state', None):
        flash('Sign-in could not be verified. Please try again.', 'error')
        return redirect(url_for('main.login'))
    code = request.args.get('code')
    if not code:
        flash('Google sign-in was cancelled.', 'info')
        return redirect(url_for('main.login'))
    import requests
    try:
        token_resp = requests.post('https://oauth2.googleapis.com/token', data={
            'code': code,
            'client_id': current_app.config['GOOGLE_CLIENT_ID'],
            'client_secret': current_app.config['GOOGLE_CLIENT_SECRET'],
            'redirect_uri': url_for('main.auth_google_callback', _external=True),
            'grant_type': 'authorization_code',
        }, timeout=10)
        token_resp.raise_for_status()
        access_token = token_resp.json().get('access_token')
        info_resp = requests.get('https://openidconnect.googleapis.com/v1/userinfo',
                                 headers={'Authorization': f'Bearer {access_token}'}, timeout=10)
        info_resp.raise_for_status()
        info = info_resp.json()
    except Exception:
        current_app.logger.exception('Google OAuth exchange failed')
        flash('Google sign-in failed. Please use email or try again.', 'error')
        return redirect(url_for('main.login'))

    email = (info.get('email') or '').strip().lower()
    if not email or not info.get('email_verified', False):
        flash('Google did not share a verified email address.', 'error')
        return redirect(url_for('main.login'))

    intent = session.pop('google_role_intent', 'user')
    user = User.query.filter_by(email=email).first()
    existing = user is not None
    if not user:
        import secrets as _s
        user = User(name=info.get('name') or email.split('@')[0], email=email, role='vendor' if intent == 'vendor' else 'user')
        user.set_password(_s.token_urlsafe(32))  # password login effectively disabled for this account
        db.session.add(user)
        db.session.commit()
    login_user(user)
    if existing and intent == 'vendor' and user.role == 'user':
        flash('This email already has a customer account, so you are signed in as a customer.', 'info')
    else:
        flash(f'Welcome, {user.name}!', 'success')
    return redirect(url_for('main.dashboard'))


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
        return redirect(url_for('main.welcome_home'))


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


@main.route('/admin/vendors')
@admin_required
def admin_vendors():
    """Admin vendor management page (admin only)."""
    from app.models import Vendor
    
    # Get all vendors
    all_vendors = Vendor.query.all()
    pending_vendors = Vendor.query.filter_by(is_verified=False).all()
    verified_vendors = Vendor.query.filter_by(is_verified=True).all()
    
    return render_template('admin_vendors.html',
                         user=current_user,
                         all_vendors=all_vendors,
                         pending_vendors=pending_vendors,
                         verified_vendors=verified_vendors)




@main.route('/admin/users')
@admin_required
def admin_users():
    """Admin user management page (admin only)."""
    from app.models import Booking, Feedback
    
    # Get search query and filter
    search_query = request.args.get('search', '').strip()
    filter_type = request.args.get('filter', 'all')
    
    # Base query
    query = User.query
    
    # Apply search filter
    if search_query:
        query = query.filter(
            (User.name.ilike(f'%{search_query}%')) |
            (User.email.ilike(f'%{search_query}%'))
        )
    
    # Apply type filter
    if filter_type == 'flagged':
        # For now, just show all users. You can add flagging logic later
        pass
    
    # Get all users
    users = query.all()
    
    # Add booking count and average rating to each user
    for user in users:
        user.bookings_count = Booking.query.filter_by(user_id=user.id).count()
        
        # Get average rating safely - join through bookings since Feedback doesn't have user_id
        avg_result = db.session.query(db.func.avg(Feedback.overall_rating)).\
            join(Booking, Feedback.booking_id == Booking.id).\
            filter(Booking.user_id == user.id).scalar()
        user.average_rating = round(float(avg_result), 1) if avg_result else 0
    
    return render_template('admin_users.html',
                         user=current_user,
                         all_users=User.query.all(),
                         users=users,
                         search_query=search_query,
                         filter_type=filter_type)


@main.route('/admin/users/<int:user_id>')
@admin_required
def admin_user_detail(user_id):
    """Admin user detail page (admin only)."""
    from app.models import Booking, Feedback
    
    target_user = User.query.get_or_404(user_id)
    # Use booking_time instead of created_at
    bookings = Booking.query.filter_by(user_id=user_id).order_by(Booking.booking_time.desc()).all()
    
    # Get feedbacks for this user
    feedbacks = Feedback.query.join(Booking).filter(Booking.user_id == user_id).all()
    
    # Calculate average rating
    avg_rating = 0
    if feedbacks:
        avg_rating = sum([f.overall_rating for f in feedbacks]) / len(feedbacks)
        avg_rating = round(avg_rating, 1)
    
    return render_template('admin_user_detail.html',
                         user=current_user,
                         target_user=target_user,
                         bookings=bookings,
                         feedbacks=feedbacks,
                         average_rating=avg_rating)
@main.route('/user/dashboard')
@user_required
def user_dashboard():
    """User dashboard (regular users only): visit history and profile."""
    return render_template('user_dashboard.html', user=current_user, demo_bookings=demo_bookings_for_view())


@main.route('/vendor/<int:vendor_id>')
def vendor_detail(vendor_id):
    """Detailed view for a specific vendor."""
    from app.models import Vendor
    vendor = Vendor.query.get_or_404(vendor_id)
    return render_template('vendor_details.html', vendor=vendor)


@main.route('/for-vendors')
def vendor_landing():
    """Landing page for potential vendor partners."""
    return render_template('vendor_landing.html')


@main.route('/manifest.json')
def manifest():
    return current_app.send_static_file('manifest.json')


@main.route('/service-worker.js')
def service_worker():
    return current_app.send_static_file('service-worker.js')


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
        
        categories = request.form.getlist('categories')
        
        # Validation
        if not all([business_name, latitude, longitude, address, categories]):
            flash('Business name, location, address, and at least one category are required.', 'error')
            return render_template('vendor_onboard.html')
        
        # Check for images (At least 3 required)
        if 'property_images' not in request.files:
            flash('No images provided.', 'error')
            return render_template('vendor_onboard.html')
        
        image_files = request.files.getlist('property_images')
        if len(image_files) < 3:
            flash('At least 3 property images are required.', 'error')
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
        
        # Combine categories into a comma-separated string
        category_str = ", ".join(categories)

        try:
            # Create vendor profile
            vendor = Vendor(
                user_id=current_user.id,
                business_name=business_name,
                description=description if description else None,
                latitude=latitude,
                longitude=longitude,
                address=address,
                category=category_str,
                has_cctv=has_cctv,
                has_female_staff=has_female_staff,
                female_staff_start_time=start_time,
                female_staff_end_time=end_time,
                is_verified=False,
                is_active=False,
                average_rating=0.0
            )
            
            db.session.add(vendor)
            db.session.flush() # Get vendor ID before committing to add images

            # Handle Image Uploads
            from werkzeug.utils import secure_filename
            from app.models import VendorImage
            import uuid

            # Ensure upload folder exists
            upload_folder = current_app.config['UPLOAD_FOLDER']
            is_vercel = os.environ.get('VERCEL') == '1'
            
            if is_vercel:
                upload_folder = '/tmp/uploads'
                
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)

            for file in image_files:
                if file and file.filename != '' and '.' in file.filename and \
                   file.filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']:
                    
                    filename = secure_filename(file.filename)
                    unique_filename = f"{uuid.uuid4().hex}_{filename}"
                    file_path = os.path.join(upload_folder, unique_filename)
                    # Convert to Base64
                    file_content = file.read()
                    import base64
                    base64_data = base64.b64encode(file_content).decode('utf-8')
                    # Guess mime type from extension if file.content_type is empty
                    mime_type = file.content_type if file.content_type else 'image/jpeg'
                    img_data_uri = f"data:{mime_type};base64,{base64_data}"
                    
                    # Reset pointer to save to file system (backup)
                    file.seek(0)
                    file.save(file_path)
                    
                    img_url = f"uploads/{unique_filename}"
                    new_image = VendorImage(vendor_id=vendor.id, image_url=img_url, image_data=img_data_uri)
                    db.session.add(new_image)

            db.session.commit()
            flash('Vendor profile created with images! Your profile is pending verification.', 'success')
            return redirect(url_for('main.vendor_dashboard'))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Onboarding error: {str(e)}")
            flash(f'An error occurred during onboarding: {str(e)}', 'error')
            return render_template('vendor_onboard.html')
    
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


@main.route('/admin/vendor/<int:vendor_id>/delete', methods=['POST'])
@admin_required
def delete_vendor(vendor_id):
    """Delete a vendor and their associated user account (admin only)."""
    from app.models import Vendor
    
    vendor = Vendor.query.get_or_404(vendor_id)
    business_name = vendor.business_name
    associated_user = vendor.user
    
    try:
        # Delete the vendor first (this will cascade to images, bookings, feedbacks)
        db.session.delete(vendor)
        
        # Also delete the user if they are strictly a vendor
        if associated_user and associated_user.role == 'vendor':
            db.session.delete(associated_user)
            
        db.session.commit()
        flash(f'Vendor "{business_name}" and their account have been permanently deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting vendor: {str(e)}', 'error')
        
    return redirect(url_for('main.admin_vendors'))


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


@main.route('/vendor/upload-images', methods=['POST'])
@vendor_required
def upload_images():
    """Handle multi-image uploads for vendors."""
    from werkzeug.utils import secure_filename
    from app.models import VendorImage
    import uuid
    
    if not current_user.vendor_profile:
        flash('Please complete your onboarding first.', 'error')
        return redirect(url_for('main.vendor_onboard'))

    if 'images' not in request.files:
        flash('No images provided.', 'error')
        return redirect(url_for('main.vendor_dashboard'))
    
    files = request.files.getlist('images')
    if not files or files[0].filename == '':
        flash('No images selected.', 'error')
        return redirect(url_for('main.vendor_dashboard'))

    # Ensure upload folder exists
    upload_folder = current_app.config['UPLOAD_FOLDER']
    is_vercel = os.environ.get('VERCEL') == '1'
    if is_vercel:
        upload_folder = '/tmp/uploads'
        
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    uploaded_count = 0
    for file in files:
        if file and '.' in file.filename and \
           file.filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']:
            
            # Create unique filename to avoid collisions
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            
            # Save file
            file_path = os.path.join(upload_folder, unique_filename)
            
            # Convert to Base64
            file_content = file.read()
            import base64
            base64_data = base64.b64encode(file_content).decode('utf-8')
            mime_type = file.content_type if file.content_type else 'image/jpeg'
            img_data_uri = f"data:{mime_type};base64,{base64_data}"
            
            # Reset pointer to save file
            file.seek(0)
            file.save(file_path)
            
            # Save to database (store the relative URL for easy serving)
            img_url = f"uploads/{unique_filename}"
            new_image = VendorImage(vendor_id=current_user.vendor_profile.id, image_url=img_url, image_data=img_data_uri)
            db.session.add(new_image)
            uploaded_count += 1
            
    if uploaded_count > 0:
        db.session.commit()
        flash(f'Successfully uploaded {uploaded_count} images.', 'success')
    else:
        flash('No valid images uploaded.', 'error')
        
    return redirect(url_for('main.vendor_dashboard'))


# Flat demo booking fee (INR) charged when a customer chooses in-app payment.
# The demo has no per-vendor pricing, so the fee is fixed and labelled as a demo fee.
DEMO_BOOKING_FEE_INR = 10


def get_razorpay_auth():
    """Return (key_id, key_secret) from env, or None when not configured."""
    key_id = os.environ.get('RAZORPAY_KEY_ID')
    key_secret = os.environ.get('RAZORPAY_KEY_SECRET')
    if not key_id or not key_secret:
        return None
    # Test-only guard: never create orders or open checkout with a live key.
    if not key_id.startswith('rzp_test_'):
        return None
    return key_id, key_secret


def razorpay_create_order(auth, amount_paise, receipt):
    """Create a Razorpay order via the REST API (no SDK dependency)."""
    import requests as http
    resp = http.post(
        'https://api.razorpay.com/v1/orders',
        auth=auth,
        data={'amount': amount_paise, 'currency': 'INR', 'receipt': receipt, 'payment_capture': 1},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def razorpay_verify_signature(auth, order_id, payment_id, signature):
    """True when the Razorpay checkout callback signature is genuine."""
    import hmac
    import hashlib
    expected = hmac.new(
        auth[1].encode(),
        f'{order_id}|{payment_id}'.encode(),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature or '')


@main.route('/book/<int:vendor_id>', methods=['POST'])
@user_required
def book_vendor(vendor_id):
    """Handle vendor booking for users."""
    from app.models import Vendor, Booking
    from datetime import datetime
    
    vendor = Vendor.query.get_or_404(vendor_id)
    
    visit_date_str = request.form.get('visit_date')
    payment_mode = request.form.get('payment_mode', 'pay_at_location')
    if payment_mode not in ('app', 'pay_at_location'):
        payment_mode = 'pay_at_location'
    
    if not visit_date_str:
        flash('Please select a visit date.', 'error')
        return redirect(url_for('main.user_dashboard'))
    
    try:
        visit_date = datetime.strptime(visit_date_str, '%Y-%m-%dT%H:%M')
    except ValueError:
        flash('Invalid date format.', 'error')
        return redirect(url_for('main.user_dashboard'))

    # Amount is fixed server-side; any client-supplied amount is ignored.
    amount = float(DEMO_BOOKING_FEE_INR) if payment_mode == 'app' else 0.0

    new_booking = Booking(
        user_id=current_user.id,
        vendor_id=vendor.id,
        visit_date=visit_date,
        payment_mode=payment_mode,
        amount=amount,
        status='pending',
        payment_status='unpaid' if payment_mode == 'pay_at_location' else 'created'
    )
    
    db.session.add(new_booking)
    db.session.commit()

    if payment_mode == 'app':
        auth = get_razorpay_auth()
        if auth is None:
            db.session.delete(new_booking)
            db.session.commit()
            flash('Online payment is not available right now. Please choose Pay Later instead.', 'error')
            return redirect(url_for('main.vendor_detail', vendor_id=vendor.id))
        try:
            order = razorpay_create_order(auth, int(amount * 100), f'booking_{new_booking.id}')
            new_booking.razorpay_order_id = order['id']
            db.session.commit()
        except Exception:
            db.session.delete(new_booking)
            db.session.commit()
            flash('Could not start the online payment. Please try again or choose Pay Later.', 'error')
            return redirect(url_for('main.vendor_detail', vendor_id=vendor.id))
        return redirect(url_for('main.pay_booking', booking_id=new_booking.id))
    
    flash('Booking request sent successfully!', 'success')
    return redirect(url_for('main.booking_confirmation', booking_id=new_booking.id))


@main.route('/booking/<int:booking_id>/pay')
@login_required
def pay_booking(booking_id):
    """Checkout page for a booking's in-app payment (Razorpay test mode)."""
    from app.models import Booking
    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id != current_user.id:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('main.index'))
    if booking.payment_mode != 'app':
        return redirect(url_for('main.booking_confirmation', booking_id=booking.id))
    if booking.payment_status == 'paid':
        return redirect(url_for('main.booking_confirmation', booking_id=booking.id))

    auth = get_razorpay_auth()
    if auth is None or not booking.razorpay_order_id:
        flash('Online payment is not available right now. Please try again later.', 'error')
        return redirect(url_for('main.booking_confirmation', booking_id=booking.id))

    return render_template('payment_checkout.html', booking=booking,
                           razorpay_key_id=os.environ.get('RAZORPAY_KEY_ID'))


@main.route('/booking/<int:booking_id>/pay/callback', methods=['POST'])
def pay_booking_callback(booking_id):
    """Verify the Razorpay payment signature server-side, then mark the booking paid.

    No login_required here on purpose: Razorpay's redirect-mode callback arrives as a
    cross-site top-level POST, so the SameSite=Lax session cookie is not attached and a
    login check would bounce a genuine payer. Authenticity comes from the HMAC signature
    over order_id|payment_id plus the stored order id match below; the confirmation page
    it redirects to still requires the owning user's session.
    """
    from app.models import Booking
    booking = Booking.query.get_or_404(booking_id)

    payment_id = request.form.get('razorpay_payment_id', '')
    order_id = request.form.get('razorpay_order_id', '')
    signature = request.form.get('razorpay_signature', '')

    auth = get_razorpay_auth()
    if auth is None or not booking.razorpay_order_id or order_id != booking.razorpay_order_id:
        booking.payment_status = 'failed'
        db.session.commit()
        flash('Payment could not be verified. You have not been charged by us; please try again.', 'error')
        return redirect(url_for('main.pay_booking', booking_id=booking.id))

    if not razorpay_verify_signature(auth, order_id, payment_id, signature):
        booking.payment_status = 'failed'
        db.session.commit()
        flash('Payment verification failed. You have not been charged by us; please try again.', 'error')
        return redirect(url_for('main.pay_booking', booking_id=booking.id))

    booking.payment_status = 'paid'
    booking.razorpay_payment_id = payment_id
    db.session.commit()
    flash('Payment successful! Your booking is confirmed.', 'success')
    return redirect(url_for('main.booking_confirmation', booking_id=booking.id))


@main.route('/booking/confirmation/<int:booking_id>')
@login_required
def booking_confirmation(booking_id):
    """Show booking confirmation/receipt."""
    from app.models import Booking
    booking = Booking.query.get_or_404(booking_id)
    
    # Ensure user can only see their own booking (unless admin)
    if booking.user_id != current_user.id and current_user.role != 'admin':
        flash('Unauthorized access.', 'error')
        return redirect(url_for('main.index'))
        
    return render_template('booking_confirmation.html', booking=booking)


@main.route('/booking/<int:booking_id>/qr')
@login_required
def booking_qr(booking_id):
    """Generate and show QR code for a booking."""
    from app.models import Booking
    booking = Booking.query.get_or_404(booking_id)
    
    # Ensure user can only see their own booking (unless admin or the vendor of the booking)
    is_admin = current_user.role == 'admin'
    is_owner = booking.user_id == current_user.id
    is_vendor = current_user.role == 'vendor' and current_user.vendor_profile and booking.vendor_id == current_user.vendor_profile.id
    
    if not (is_admin or is_owner or is_vendor):
        flash('Unauthorized access.', 'error')
        return redirect(url_for('main.index'))
    
    # QR encodes the vendor verification link so a vendor can scan it with any
    # phone camera and open the verification page directly.
    qr_data = url_for('main.verify_booking', booking_id=booking.id, _external=True)
    
    # Create QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save to bytes buffer
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    qr_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
    
    return render_template('booking_qr.html', booking=booking, qr_code=qr_base64)


@main.route('/booking/<int:booking_id>/feedback', methods=['GET', 'POST'])
@user_required
def submit_feedback(booking_id):
    """Submit feedback for a completed booking."""
    from app.models import Booking, Feedback, Vendor
    
    booking = Booking.query.get_or_404(booking_id)
    
    # 1. Verification: Only the owner can review
    if booking.user_id != current_user.id:
        flash('Unauthorized.', 'error')
        return redirect(url_for('main.user_dashboard'))
    
    # 2. Verification: Only COMPLETED bookings
    if booking.status != 'completed':
        flash('Feedback can only be submitted for completed visits.', 'error')
        return redirect(url_for('main.user_dashboard'))
    
    # 3. Verification: Only one feedback per booking
    if booking.feedback:
        flash('Feedback has already been submitted for this visit.', 'info')
        return redirect(url_for('main.user_dashboard'))
    
    if request.method == 'POST':
        try:
            hygiene = int(request.form.get('hygiene_rating', 5))
            safety = int(request.form.get('safety_rating', 5))
            staff = int(request.form.get('staff_behavior_rating', 5))
            comments = request.form.get('comments', '')
            
            overall = (hygiene + safety + staff) / 3.0
            
            new_feedback = Feedback(
                booking_id=booking.id,
                vendor_id=booking.vendor_id,
                hygiene_rating=hygiene,
                safety_rating=safety,
                staff_behavior_rating=staff,
                overall_rating=overall,
                comments=comments
            )
            
            db.session.add(new_feedback)
            
            # Recalculate Vendor Average Rating
            vendor = booking.vendor
            all_feedbacks = Feedback.query.filter_by(vendor_id=vendor.id).all()
            total_rating = sum([f.overall_rating for f in all_feedbacks]) + overall
            vendor.average_rating = total_rating / (len(all_feedbacks) + 1)
            
            db.session.commit()
            flash('Thank you for your feedback! It helps keep SheSafe reliable.', 'success')
            return redirect(url_for('main.user_dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error submitting feedback: {str(e)}', 'error')
            
    return render_template('feedback_form.html', booking=booking)
@main.route('/booking/<int:booking_id>/complete', methods=['POST'])
@vendor_required
def complete_booking(booking_id):
    """Mark a booking as completed (Vendor only)."""
    from app.models import Booking
    booking = Booking.query.get_or_404(booking_id)
    
    # Ensure vendor owns this booking
    if booking.vendor_id != current_user.vendor_profile.id:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('main.vendor_dashboard'))
    
    if booking.status == 'completed':
        flash('This booking was already verified.', 'info')
        return redirect(url_for('main.vendor_dashboard'))
    if booking.status == 'cancelled':
        flash('This booking was cancelled and cannot be completed.', 'error')
        return redirect(url_for('main.vendor_dashboard'))
    if booking.payment_mode == 'app' and booking.payment_status != 'paid':
        flash('Online payment is not completed for this booking yet. Ask the customer to pay from their booking, or accept the visit as pay-at-venue outside the app.', 'error')
        return redirect(url_for('main.vendor_dashboard'))

    booking.status = 'completed'
    db.session.commit()

    flash('Booking marked as completed. The user can now leave a review!', 'success')
    return redirect(url_for('main.vendor_dashboard'))

@main.route('/booking/<int:booking_id>/verify')
@vendor_required
def verify_booking(booking_id):
    """Vendor-side booking verification page, reached by scanning the booking QR."""
    from app.models import Booking
    booking = Booking.query.get_or_404(booking_id)

    vendor_profile = current_user.vendor_profile
    if not vendor_profile or booking.vendor_id != vendor_profile.id:
        flash('This booking belongs to a different venue.', 'error')
        return redirect(url_for('main.vendor_dashboard'))

    return render_template('verify_booking.html', booking=booking)

@main.route('/vendor/bookings')
@vendor_required
def vendor_bookings():
    """List all bookings for the current vendor."""
    from app.models import Booking
    bookings = (Booking.query
                .filter_by(vendor_id=current_user.vendor_profile.id)
                .order_by(Booking.visit_date.desc())
                .all())
    return render_template('vendor_bookings.html', user=current_user, bookings=bookings)


@main.route('/vendor/edit', methods=['GET', 'POST'])
@vendor_required
def vendor_edit():
    """Edit the current vendor's profile (post-onboarding)."""
    from datetime import datetime
    vendor = current_user.vendor_profile
    if not vendor:
        flash('Please complete vendor onboarding first.', 'info')
        return redirect(url_for('main.vendor_onboard'))

    if request.method == 'POST':
        vendor.business_name = request.form.get('business_name', vendor.business_name)
        vendor.description = request.form.get('description') or None
        vendor.address = request.form.get('address', vendor.address)
        vendor.has_cctv = request.form.get('has_cctv') == 'on'
        vendor.has_female_staff = request.form.get('has_female_staff') == 'on'
        vendor.is_active = request.form.get('is_active') == 'on'

        allowed_categories = ['Washroom', 'Period Care', 'Nursing Room', 'Changing Room']
        categories = [c for c in request.form.getlist('categories') if c in allowed_categories]
        if categories:
            vendor.category = ", ".join(categories)

        fst = request.form.get('female_staff_start_time')
        fet = request.form.get('female_staff_end_time')
        if vendor.has_female_staff and fst and fet:
            try:
                vendor.female_staff_start_time = datetime.strptime(fst, '%H:%M').time()
                vendor.female_staff_end_time = datetime.strptime(fet, '%H:%M').time()
            except ValueError:
                flash('Invalid time format for staff timing.', 'error')
                return render_template('vendor_edit.html', user=current_user, vendor=vendor)
        elif not vendor.has_female_staff:
            vendor.female_staff_start_time = None
            vendor.female_staff_end_time = None

        db.session.commit()
        flash('Profile updated.', 'success')
        return redirect(url_for('main.vendor_dashboard'))

    return render_template('vendor_edit.html', user=current_user, vendor=vendor)


@main.route('/api/ask-ai', methods=['POST'])
@login_required
def api_ask_ai():
    """Server-side AI proxy. Provider keys stay on the server (env vars only). Disabled (404) without a key."""
    import os
    ai_enabled = os.environ.get('AI_ENABLED') == '1' and any(
        os.environ.get(k) for k in ('GEMINI_API_KEY', 'OPENROUTER_API_KEY', 'NVIDIA_API_KEY', 'SILICONFLOW_API_KEY'))
    if not ai_enabled:
        return {'error': 'The AI assistant is not available in this demo.'}, 503
    import json as _json
    import urllib.request
    import urllib.error

    system_prompt = (
        "You are SheSafe AI, a professional and empathetic expert in women's sexual and "
        "urinary health and hygiene. Your tone is supportive, informative, and safe. Your goal "
        "is to provide accurate health information while reminding users that you are an AI and "
        "they should consult a doctor for clinical diagnosis. Particularly answer women sexual "
        "and urinary health and hygeniene related questions."
    )

    data = request.get_json(silent=True) or {}
    prompt = (data.get('prompt') or '').strip()
    if not prompt:
        return {'error': 'Prompt is required.'}, 400

    def _post(url, payload, headers=None, timeout=20):
        req = urllib.request.Request(
            url,
            data=_json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json', **(headers or {})},
            method='POST',
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return _json.loads(resp.read().decode('utf-8'))

    errors = []

    # 1. Gemini (only if a server-side key is configured)
    gemini_key = os.environ.get('GEMINI_API_KEY', '')
    if gemini_key:
        try:
            url = ('https://generativelanguage.googleapis.com/v1beta/models/'
                   'gemini-flash-latest:generateContent?key=' + gemini_key)
            body = {
                'contents': [{'role': 'user', 'parts': [{'text': prompt}]}],
                'generationConfig': {'maxOutputTokens': 1000, 'temperature': 0.5},
                'systemInstruction': {'parts': [{'text': system_prompt}]},
            }
            data = _post(url, body)
            text = (data.get('candidates') or [{}])[0].get('content', {}).get('parts', [{}])[0].get('text')
            if text:
                return {'text': text}
            errors.append('Gemini: empty response')
        except Exception as e:
            errors.append('Gemini: %s' % e)

    # 2. OpenAI-compatible providers
    chat_providers = [
        ('OpenRouter', os.environ.get('OPENROUTER_API_KEY', ''),
         'https://openrouter.ai/api/v1/chat/completions',
         ['google/gemma-2-9b-it:free', 'meta-llama/llama-3.2-3b-instruct:free']),
        ('NVIDIA NIM', os.environ.get('NVIDIA_API_KEY', ''),
         'https://integrate.api.nvidia.com/v1/chat/completions',
         ['meta/llama-3.1-8b-instruct']),
        ('SiliconFlow', os.environ.get('SILICONFLOW_API_KEY', ''),
         'https://api.siliconflow.cn/v1/chat/completions',
         ['Qwen/Qwen2.5-7B-Instruct']),
    ]
    for name, key, url, models in chat_providers:
        if not key:
            continue
        for model in models:
            try:
                body = {
                    'model': model,
                    'messages': [
                        {'role': 'system', 'content': system_prompt},
                        {'role': 'user', 'content': prompt},
                    ],
                    'max_tokens': 1000,
                    'temperature': 0.5,
                }
                data = _post(url, body, headers={'Authorization': 'Bearer ' + key})
                choices = data.get('choices') or []
                text = choices[0].get('message', {}).get('content') if choices else None
                if text:
                    return {'text': text}
                errors.append('%s %s: empty response' % (name, model))
            except Exception as e:
                errors.append('%s %s: %s' % (name, model, e))

    current_app.logger.warning('ask-ai providers failed: %s', '; '.join(errors))
    return {'error': 'The AI assistant is unavailable right now. Please try again later.'}, 502


@main.route('/update-db-schema')
@admin_required
def update_db_schema():
    """Temporary route to update database schema."""
    from sqlalchemy import text
    results = []
    
    # Use independent transactions for each step
    def run_step(conn, sql, description):
        try:
            conn.execute(text(sql))
            conn.commit()
            results.append(f"Successfully {description}")
        except Exception as e:
            conn.rollback()
            results.append(f"Failed {description}: {str(e)}")

    try:
        with db.engine.connect() as conn:
            # 1. Update category column type
            run_step(conn, "ALTER TABLE vendors ALTER COLUMN category TYPE VARCHAR(255)", "updated vendors.category")
            
            # 2. Add image_data to vendor_images
            # We check if it exists first
            try:
                conn.execute(text("SELECT image_data FROM vendor_images LIMIT 1"))
                results.append("Column image_data already exists")
            except Exception:
                conn.rollback() # Transaction aborted by failed select, must rollback
                run_step(conn, "ALTER TABLE vendor_images ADD COLUMN image_data TEXT", "added image_data column")

            # 3. Make image_url nullable
            run_step(conn, "ALTER TABLE vendor_images ALTER COLUMN image_url DROP NOT NULL", "made image_url nullable")
            
        return "<br>".join(results) + "<br><br><b>Schema update attempt complete! Please try the dashboards now.</b>"
    except Exception as e:
        return f"CRITICAL Error connecting to DB: {str(e)}"

@main.route('/create-admin')
def create_admin():
    """Secret route to create admin user. Call with ?token=YOUR_SECRET_TOKEN"""
    import os
    secret_token = os.environ.get('ADMIN_CREATE_TOKEN')
    provided_token = request.args.get('token', '')

    # Fail closed: with no configured token this route is disabled entirely
    if not secret_token or provided_token != secret_token:
        return "Unauthorized", 401

    admin_email = os.environ.get('ADMIN_EMAIL', 'admin@admin.com')
    admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')

    admin = User.query.filter_by(email=admin_email).first()
    if admin:
        return f"Admin user already exists: {admin_email}"

    admin = User(name='Admin', email=admin_email, role='admin')
    admin.set_password(admin_password)
    db.session.add(admin)
    db.session.commit()

    return "Admin created."


@main.route('/admin/revenue')
@admin_required
def admin_revenue():
    """Admin revenue page (admin only)."""
    from app.models import Booking
    
    # Get all completed bookings
    completed_bookings = Booking.query.filter_by(status='completed').order_by(Booking.booking_time.desc()).all()
    
    # Calculate total revenue
    total_revenue = sum([b.amount for b in completed_bookings])
    
    # Group revenue by payment mode
    revenue_by_mode = {}
    for b in completed_bookings:
        revenue_by_mode[b.payment_mode] = revenue_by_mode.get(b.payment_mode, 0) + b.amount
        
    return render_template('admin_revenue.html',
                         user=current_user,
                         bookings=completed_bookings,
                         total_revenue=total_revenue,
                         revenue_by_mode=revenue_by_mode)


@main.route('/admin/settings')
@admin_required
def admin_settings():
    """Admin settings page (admin only)."""
    return render_template('admin_settings.html', user=current_user)



@main.route('/uploads/<path:filename>')
def serve_uploads(filename):
    """Serve uploaded files from /tmp on Vercel or normal static folder."""
    import os
    from flask import send_from_directory
    
    is_vercel = os.environ.get('VERCEL') == '1'
    if is_vercel:
        return send_from_directory('/tmp/uploads', filename)
    
    # Fallback to local static uploads
    upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
    return send_from_directory(upload_folder, filename)

@main.route('/vendor/dashboard')
@vendor_required
def vendor_dashboard():
    """Vendor dashboard (vendor only)."""
    return render_template('vendor_dashboard.html', user=current_user)



# ---------------------------------------------------------------------------
# Presentation bookings for the KGP place listings.
# Isolated from production data: no Vendor/Booking rows are created or changed. State lives in
# the user's signed session cookie plus signed tokens. Payment uses Razorpay TEST mode only.
# ---------------------------------------------------------------------------
def _demo_serializer():
    from itsdangerous import URLSafeTimedSerializer
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'], salt='presentation-booking')


def _demo_venue_or_404(slug):
    from flask import abort
    from app.demo_catalog import kgp_venues
    venue = next((v for v in kgp_venues() if v['slug'] == slug), None)
    if venue is None:
        abort(404)
    return venue


def _demo_save(booking):
    items = [b for b in session.get('demo_bookings', []) if b['id'] != booking['id']]
    items.append(booking)
    session['demo_bookings'] = items[-10:]


def _demo_find(bid):
    return next((b for b in session.get('demo_bookings', []) if b['id'] == bid), None)


def demo_bookings_for_view():
    from datetime import datetime
    out = []
    for b in sorted(session.get('demo_bookings', []), key=lambda x: x['visit'], reverse=True):
        row = dict(b)
        row['visit_dt'] = datetime.fromisoformat(b['visit'])
        out.append(row)
    return out


@main.route('/demo/book/<slug>', methods=['POST'])
@user_required
def demo_book(slug):
    import secrets
    from datetime import datetime
    venue = _demo_venue_or_404(slug)
    try:
        visit = datetime.strptime(request.form.get('visit_date', ''), '%Y-%m-%dT%H:%M')
    except ValueError:
        flash('Please select a visit time.', 'error')
        return redirect(url_for('main.kgp_demo_venue', slug=slug))
    mode = request.form.get('payment_mode', 'pay_at_location')
    if mode not in ('app', 'pay_at_location'):
        mode = 'pay_at_location'
    booking = {'id': secrets.token_hex(3).upper(), 'slug': slug, 'name': venue['name'],
               'visit': visit.isoformat(timespec='minutes'), 'mode': mode,
               'amount': float(DEMO_BOOKING_FEE_INR) if mode == 'app' else 0.0, 'paid': False, 'pid': ''}
    if mode == 'pay_at_location':
        _demo_save(booking)
        return redirect(url_for('main.demo_booking', bid=booking['id']))
    auth = get_razorpay_auth()
    if auth is None:
        flash('Online payment is not available right now. Choose Pay at location.', 'error')
        return redirect(url_for('main.kgp_demo_venue', slug=slug))
    try:
        order = razorpay_create_order(auth, int(booking['amount'] * 100), f"visit_{booking['id']}")
    except Exception:
        flash('Could not start the payment. Please try again or choose Pay at location.', 'error')
        return redirect(url_for('main.kgp_demo_venue', slug=slug))
    token = _demo_serializer().dumps({'b': booking, 'order': order['id']})
    return redirect(url_for('main.demo_pay', t=token))


@main.route('/demo/pay')
@user_required
def demo_pay():
    from itsdangerous import BadData
    try:
        data = _demo_serializer().loads(request.args.get('t', ''), max_age=3600)
    except BadData:
        flash('This payment link expired. Please start again.', 'error')
        return redirect(url_for('main.explore'))
    return render_template('demo_pay.html', booking=data['b'], order_id=data['order'], token=request.args['t'],
                           razorpay_key_id=os.environ.get('RAZORPAY_KEY_ID'), user=current_user)


@main.route('/demo/pay/callback', methods=['POST'])
def demo_pay_callback():
    """Razorpay returns here as a cross-site POST without the session cookie, so this only
    verifies the signature and hands a signed token to the confirm step."""
    from itsdangerous import BadData
    try:
        data = _demo_serializer().loads(request.args.get('t', ''), max_age=3600)
    except BadData:
        return redirect(url_for('main.explore'))
    auth = get_razorpay_auth()
    order_id = request.form.get('razorpay_order_id', '')
    payment_id = request.form.get('razorpay_payment_id', '')
    ok = (auth is not None and order_id == data['order']
          and razorpay_verify_signature(auth, order_id, payment_id, request.form.get('razorpay_signature', '')))
    if not ok:
        flash('Payment could not be verified. Please try again.', 'error')
        return redirect(url_for('main.demo_pay', t=request.args.get('t', '')))
    b = dict(data['b'], paid=True, pid=payment_id)
    return redirect(url_for('main.demo_confirm', t=_demo_serializer().dumps(b)))


@main.route('/demo/confirm')
@user_required
def demo_confirm():
    from itsdangerous import BadData
    try:
        b = _demo_serializer().loads(request.args.get('t', ''), max_age=3600)
    except BadData:
        return redirect(url_for('main.explore'))
    _demo_save(b)
    flash('Payment successful. Your booking is confirmed.', 'success')
    return redirect(url_for('main.demo_booking', bid=b['id']))


@main.route('/demo/booking/<bid>')
@user_required
def demo_booking(bid):
    from flask import abort
    from datetime import datetime
    b = _demo_find(bid)
    if b is None:
        abort(404)
    pass_url = url_for('main.demo_pass', t=_demo_serializer().dumps(b), _external=True)
    qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=8, border=3)
    qr.add_data(pass_url); qr.make(fit=True)
    buf = io.BytesIO(); qr.make_image(fill_color='black', back_color='white').save(buf, format='PNG')
    return render_template('demo_booking.html', b=b, visit=datetime.fromisoformat(b['visit']),
                           qr=base64.b64encode(buf.getvalue()).decode())


def _demo_pass_state(token):
    """Return (state, booking). state: valid | used | expired | invalid."""
    from itsdangerous import BadData, SignatureExpired
    try:
        b = _demo_serializer().loads(token or '', max_age=60 * 60 * 24 * 30)
    except SignatureExpired:
        return 'expired', None
    except BadData:
        return 'invalid', None
    if not isinstance(b, dict) or 'id' not in b or 'name' not in b or 'visit' not in b:
        return 'invalid', None
    if b['id'] in session.get('demo_used', {}):
        return 'used', b
    return 'valid', b


@main.route('/demo/pass', methods=['GET', 'POST'])
def demo_pass():
    from datetime import datetime
    token = request.values.get('t', '')
    state, b = _demo_pass_state(token)
    if request.method == 'POST' and state == 'valid':
        used = dict(session.get('demo_used', {}))
        from zoneinfo import ZoneInfo
        used[b['id']] = datetime.now(ZoneInfo('Asia/Kolkata')).strftime('%d %b %Y, %I:%M %p')
        session['demo_used'] = dict(list(used.items())[-20:])
        return redirect(url_for('main.demo_pass', t=token))
    visit = datetime.fromisoformat(b['visit']) if b else None
    used_at = session.get('demo_used', {}).get(b['id']) if b else None
    code = 200 if state in ('valid', 'used') else 400
    return render_template('demo_pass.html', state=state, b=b, visit=visit, used_at=used_at, token=token), code
