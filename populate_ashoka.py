import sys
import os
from datetime import time

# Add the project root to sys.path
sys.path.append(os.getcwd())

from app import create_app, db
from app.models import User, Vendor

app = create_app()

def populate():
    with app.app_context():
        # Create a generic vendor user if not exists
        vendor_data = [
            {
                "email": "greenchick@shesafe.com",
                "name": "Highway Diner",
                "business_name": "Highway Diner Safe Zone",
                "lat": 28.9392,
                "lng": 77.1158,
                "address": "TDI City, Kundli, Sonepat, Haryana 131023",
                "cctv": True,
                "female_staff": True,
                "categories": "Washroom, Changing Room"
            },
            {
                "email": "dominos@shesafe.com",
                "name": "Campus Cafe",
                "business_name": "Campus Cafe Safe Zone",
                "lat": 28.9554,
                "lng": 77.1082,
                "address": "Omaxe City, Sonepat, Haryana 131023",
                "cctv": True,
                "female_staff": False,
                "categories": "Washroom, Period Care"
            },
            {
                "email": "savoy@shesafe.com",
                "name": "Savoy Greens",
                "business_name": "Savoy Greens Rest Stop",
                "lat": 28.9351,
                "lng": 77.1189,
                "address": "NH 1, Kundli, Sonepat, Haryana 131023",
                "cctv": True,
                "female_staff": True,
                "categories": "Washroom, Nursing Room"
            },
            {
                "email": "parker@shesafe.com",
                "name": "City Mall",
                "business_name": "City Mall Safe Zone",
                "lat": 28.9375,
                "lng": 77.1165,
                "address": "Parker Mall, NH 1, Kundli, Sonepat, Haryana",
                "cctv": True,
                "female_staff": True,
                "categories": "Washroom, Period Care, Changing Room, Nursing Room"
            }
        ]

        for data in vendor_data:
            user = User.query.filter_by(email=data['email']).first()
            if not user:
                user = User(name=data['name'], email=data['email'], role='vendor')
                user.set_password('password123')
                db.session.add(user)
                db.session.commit()
            
            vendor = Vendor.query.filter_by(user_id=user.id).first()
            if not vendor:
                vendor = Vendor(
                    user_id=user.id,
                    business_name=data['business_name'],
                    latitude=data['lat'],
                    longitude=data['lng'],
                    address=data['address'],
                    has_cctv=data['cctv'],
                    has_female_staff=data['female_staff'],
                    is_verified=True,
                    is_active=True,
                    average_rating=0.0
                )
                if data['female_staff']:
                    vendor.female_staff_start_time = time(9, 0)
                    vendor.female_staff_end_time = time(21, 0)
                db.session.add(vendor)
            vendor.category = data.get('categories', 'Washroom')
        
        db.session.commit()
        print("Successfully populated vendors near Ashoka University.")

if __name__ == "__main__":
    populate()
