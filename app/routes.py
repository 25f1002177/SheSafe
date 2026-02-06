from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User
from app.decorators import admin_required, vendor_required, user_required
import os

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
    """Authenticated user homepage."""
    from app.models import Vendor
    vendors = Vendor.query.filter_by(is_verified=True, is_active=True).all()
    return render_template('welcome.html', vendors=vendors)


@main.route('/landing')
def landing():
    """Explicit landing page for guests."""
    from app.models import Vendor
    vendors = Vendor.query.filter_by(is_verified=True, is_active=True).all()
    return render_template('landing.html', vendors=vendors)


@main.route('/explore')
@login_required
def explore():
    """Explore page with Google Maps."""
    from app.models import Vendor
    vendors = Vendor.query.filter_by(is_verified=True, is_active=True).all()
    return render_template('explore.html', vendors=vendors)


@main.route('/ask-ai')
@login_required
def ask_ai():
    """Ask AI page."""
    return render_template('ask_ai.html')


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
        
        # Security: Prevent admin registration via form
        if role not in ['user', 'vendor']:
            role = 'user'
        
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
            
            print(f"DEBUG: Login successful, redirecting to {user.role} dashboard")  # Debug
            
            # Redirect to next page or dashboard
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            
            if user.role == 'admin':
                print("DEBUG: Redirecting to admin dashboard")  # Debug
                return redirect(url_for('main.admin_dashboard'))
            elif user.role == 'vendor':
                return redirect(url_for('main.vendor_dashboard'))
            else:
                return redirect(url_for('main.welcome_home'))
        else:
            print("DEBUG: Login failed - invalid credentials")  # Debug
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




@main.route('/vendor/dashboard')
@vendor_required
def vendor_dashboard():
    """Vendor dashboard (vendor only)."""
    return render_template('vendor_dashboard.html', user=current_user)


@main.route('/user/dashboard')
@user_required
def user_dashboard():
    """User dashboard (regular users only) - Shows nearby verified vendors."""
    from app.models import Vendor
    # Fetch verified and active vendors to show on the map/list
    verified_vendors = Vendor.query.filter_by(is_verified=True, is_active=True).all()
    # Serialize for JS
    vendors_json = [v.to_dict() for v in verified_vendors]
    return render_template('user_dashboard.html', user=current_user, vendors=verified_vendors, vendors_json=vendors_json)


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
        
        category = request.form.get('category')
        
        # Validation
        if not all([business_name, latitude, longitude, address, category]):
            flash('Business name, location, address, and category are required.', 'error')
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
            category=category,
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

    uploaded_count = 0
    for file in files:
        if file and '.' in file.filename and \
           file.filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'webp'}:
            
            # Create unique filename to avoid collisions
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            
            # Save file
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(file_path)
            
            # Save to database (store the relative URL for easy serving)
            img_url = f"uploads/{unique_filename}"
            new_image = VendorImage(vendor_id=current_user.vendor_profile.id, image_url=img_url)
            db.session.add(new_image)
            uploaded_count += 1
            
    if uploaded_count > 0:
        db.session.commit()
        flash(f'Successfully uploaded {uploaded_count} images.', 'success')
    else:
        flash('No valid images uploaded.', 'error')
        
    return redirect(url_for('main.vendor_dashboard'))


@main.route('/book/<int:vendor_id>', methods=['POST'])
@user_required
def book_vendor(vendor_id):
    """Handle vendor booking for users."""
    from app.models import Vendor, Booking
    from datetime import datetime
    
    vendor = Vendor.query.get_or_404(vendor_id)
    
    visit_date_str = request.form.get('visit_date')
    payment_mode = request.form.get('payment_mode', 'pay_at_location')
    amount = float(request.form.get('amount', 0))
    
    if not visit_date_str:
        flash('Please select a visit date.', 'error')
        return redirect(url_for('main.user_dashboard'))
    
    try:
        visit_date = datetime.strptime(visit_date_str, '%Y-%m-%dT%H:%M')
    except ValueError:
        flash('Invalid date format.', 'error')
        return redirect(url_for('main.user_dashboard'))

    new_booking = Booking(
        user_id=current_user.id,
        vendor_id=vendor.id,
        visit_date=visit_date,
        payment_mode=payment_mode,
        amount=amount,
        status='pending'
    )
    
    db.session.add(new_booking)
    db.session.commit()
    
    flash('Booking request sent successfully!', 'success')
    return redirect(url_for('main.booking_confirmation', booking_id=new_booking.id))


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
    
    booking.status = 'completed'
    db.session.commit()
    
    flash('Booking marked as completed. The user can now leave a review!', 'success')
    return redirect(url_for('main.vendor_dashboard'))

@main.route('/update-db-schema')
def update_db_schema():
    """Temporary route to update database schema."""
    from sqlalchemy import text
    try:
        with db.engine.connect() as conn:
            conn.execute(text("ALTER TABLE vendors ADD COLUMN IF NOT EXISTS category VARCHAR(50) DEFAULT 'Washroom' NOT NULL"))
            conn.commit()
        return "Schema updated successfully! Added 'category' column."
    except Exception as e:
        return f"Error updating schema: {str(e)}"

@main.route('/create-admin')
def create_admin():
    """Secret route to create admin user. Call with ?token=YOUR_SECRET_TOKEN"""
    import os
    secret_token = os.environ.get('ADMIN_CREATE_TOKEN', 'default-secret-change-me')
    provided_token = request.args.get('token', '')

    if provided_token != secret_token:
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

    return f"Admin created! Email: {admin_email}, Password: {admin_password}"

@main.route('/admin/users')
@admin_required
def admin_users():
    """Admin user management page."""
    try:
        from app.models import User, Booking, Feedback
        
        search_query = request.args.get('search', '')
        filter_type = request.args.get('filter', 'all')
        
        # Base query - exclude admins and vendors
        base_query = User.query.filter(db.or_(User.role == 'user', User.role.is_(None)))
        
        # Apply search
        if search_query:
            search = f"%{search_query}%"
            try:
                search_id = int(search_query)
                base_query = base_query.filter(
                    db.or_(
                        User.name.ilike(search),
                        User.email.ilike(search),
                        User.id == search_id
                    )
                )
            except ValueError:
                base_query = base_query.filter(
                    db.or_(
                        User.name.ilike(search),
                        User.email.ilike(search)
                    )
                )
        
        # Get all users matching criteria
        all_users = base_query.order_by(User.id.desc()).all()
        
        # Build a list of user dictionaries to avoid modifying SQLAlchemy instances
        users_data = []
        for u in all_users:
            # Get bookings count
            bookings_count = db.session.query(db.func.count(Booking.id)).filter_by(user_id=u.id).scalar() or 0
            
            # Get average rating safely - join through bookings since Feedback doesn't have user_id
            avg_result = db.session.query(db.func.avg(Feedback.overall_rating)).\
                join(Booking, Feedback.booking_id == Booking.id).\
                filter(Booking.user_id == u.id).scalar()
            avg_rating = round(float(avg_result), 1) if avg_result else 0
            
            users_data.append({
                'id': u.id,
                'name': u.name,
                'email': u.email,
                'role': u.role,
                'bookings_count': bookings_count,
                'average_rating': avg_rating,
                'is_verified': True,
                'is_flagged': False
            })
        
        flagged_users = []
        if filter_type == 'flagged':
            # Show first 3 users as flagged for demo
            flagged_users = users_data[:3]
            for f in flagged_users:
                f['is_flagged'] = True
                f['flag_reason'] = 'Review Needed'
        
        return render_template('admin_users.html',
                             user=current_user,
                             users=users_data,
                             all_users=users_data,
                             flagged_users=flagged_users,
                             search_query=search_query,
                             filter_type=filter_type)
    except Exception as e:
        flash(f'Error loading users: {str(e)}', 'error')
        return redirect(url_for('main.admin_dashboard'))

@main.route('/admin/user/<int:user_id>')
@admin_required
def admin_user_detail(user_id):
    """Admin user detail page."""
    try:
        from app.models import User, Booking, Feedback, Vendor
        target_user = User.query.get_or_404(user_id)
        
        # Get bookings with vendor eagerly loaded
        bookings = db.session.query(Booking).options(
            db.joinedload(Booking.vendor)
        ).filter_by(user_id=user_id).order_by(Booking.booking_time.desc()).all()
        
        # Get feedbacks through bookings (Feedback -> Booking -> User)
        feedbacks = db.session.query(Feedback).join(Booking).filter(Booking.user_id == user_id).all()
        
        # Calculate average rating
        avg_rating = 0
        if feedbacks:
            avg_rating = sum(f.overall_rating for f in feedbacks) / len(feedbacks)
        
        return render_template('admin_user_detail.html', 
                             user=current_user, 
                             target_user=target_user,
                             bookings=bookings,
                             feedbacks=feedbacks,
                             average_rating=round(avg_rating, 1))
    except Exception as e:
        flash(f'Error loading user: {str(e)}', 'error')
        return redirect(url_for('main.admin_users'))
