from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db
from datetime import datetime, timezone


def utcnow():
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


class User(UserMixin, db.Model):
    """User model for authentication."""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')
    
    # Relationship to vendor profile
    vendor_profile = db.relationship('Vendor', backref='user', uselist=False, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set the user's password."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if the provided password matches the hash."""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.email}>'


class Vendor(db.Model):
    """Vendor model for business/service provider information."""
    __tablename__ = 'vendors'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    business_name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    address = db.Column(db.String(500), nullable=False)
    category = db.Column(db.String(255), nullable=False, default='Washroom') 
    has_cctv = db.Column(db.Boolean, default=False, nullable=False)
    has_female_staff = db.Column(db.Boolean, default=False, nullable=False)
    female_staff_start_time = db.Column(db.Time, nullable=True)
    female_staff_end_time = db.Column(db.Time, nullable=True)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=False, nullable=False)
    average_rating = db.Column(db.Float, default=0.0, nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow(), nullable=False)
    
    # Relationship to images
    images = db.relationship('VendorImage', backref='vendor', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert vendor profile to dictionary for JSON serialization."""
        first_image = self.images[0].url if self.images else "https://images.unsplash.com/photo-1590602847861-f357a9332bbc?q=80&w=200&auto=format&fit=crop"
        
        return {
            'id': self.id,
            'business_name': self.business_name,
            'address': self.address,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'category': self.category,
            'has_cctv': self.has_cctv,
            'has_female_staff': self.has_female_staff,
            'average_rating': self.average_rating,
            'image_url': first_image if first_image else "https://images.unsplash.com/photo-1590602847861-f357a9332bbc?q=80&w=200&auto=format&fit=crop"
        }

    def __repr__(self):
        return f'<Vendor {self.business_name}>'

class Booking(db.Model):
    __tablename__ = 'bookings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendors.id'), nullable=False)
    booking_time = db.Column(db.DateTime, default=utcnow(), nullable=False)
    visit_date = db.Column(db.DateTime, nullable=False)
    payment_mode = db.Column(db.String(20), nullable=False) # 'app' or 'pay_at_location'
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending', nullable=False) # 'pending', 'confirmed', 'cancelled', 'completed'
    
    # Relationships
    user = db.relationship('User', backref=db.backref('bookings', lazy=True))
    vendor = db.relationship('Vendor', backref=db.backref('bookings', lazy=True))
    
    def __repr__(self):
        return f'<Booking {self.id} for Vendor {self.vendor_id}>'

class Feedback(db.Model):
    __tablename__ = 'feedbacks'
    
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), unique=True, nullable=False)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendors.id'), nullable=False)
    hygiene_rating = db.Column(db.Integer, nullable=False)
    safety_rating = db.Column(db.Integer, nullable=False)
    staff_behavior_rating = db.Column(db.Integer, nullable=False)
    overall_rating = db.Column(db.Float, nullable=False)
    comments = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=utcnow(), nullable=False)
    
    # Relationships
    booking = db.relationship('Booking', backref=db.backref('feedback', uselist=False))
    vendor = db.relationship('Vendor', backref=db.backref('feedbacks', lazy=True))
    
    def __repr__(self):
        return f'<Feedback {self.id} for Booking {self.booking_id}>'


class VendorImage(db.Model):
    """Model for storing vendor property/washroom images."""
    __tablename__ = 'vendor_images'
    
    id = db.Column(db.Integer, primary_key=True)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendors.id'), nullable=False)
    image_url = db.Column(db.String(255), nullable=True) # URL can be null if only data is used
    image_data = db.Column(db.Text, nullable=True) # Store Base64 data
    uploaded_at = db.Column(db.DateTime, default=utcnow(), nullable=False)
    
    @property
    def url(self):
        """Safely get image URL or Base64 data."""
        # Use getattr to prevent crash if image_data column is missing in DB
        data = getattr(self, 'image_data', None)
        if data:
            return data
        
        # Fallback to stored URL
        if self.image_url:
            return f"/static/{self.image_url}" if not self.image_url.startswith('static/') else f"/{self.image_url}"
        
        return "https://images.unsplash.com/photo-1584622650111-993a426fbf0a?q=80&w=800&auto=format&fit=crop"

    def __repr__(self):
        return f'<VendorImage {self.id}>'
