import sys
import os
from datetime import time

# Add the project root to sys.path
sys.path.append(os.getcwd())

from app import create_app, db
from app.models import User, Vendor, VendorImage

app = create_app()

def populate():
    with app.app_context():
        # New vendor data based on user request and Google Maps research
        new_vendors = [
            {
                "email": "goldenhut@shesafe.com",
                "name": "Golden Hut",
                "business_name": "Golden Hut Restaurants & Rooms",
                "lat": 28.945581303017335,
                "lng": 77.09604303657157,
                "address": "Opposite Ashoka University, Near Rai NH1, Rai, Sonipat, Haryana 131021",
                "cctv": True,
                "female_staff": True,
                "image": "https://lh3.googleusercontent.com/p/AF1QipONwuyOQooKIAY3UJueWReljlzJ_ZkykQpFmONf=s1600"
            },
            {
                "email": "bollywood@shesafe.com",
                "name": "Bollywood Dhaba",
                "business_name": "Dhaba Bollywood",
                "lat": 28.922467309144793,
                "lng": 77.10397787102141,
                "address": "Stone Chowk, Near 20th Mile, Rajiv Gandhi Education City, Sonipat, Haryana 131029",
                "cctv": True,
                "female_staff": False,
                "image": "https://lh3.googleusercontent.com/p/AF1QipPTyuWEXnWcbaGLE_vl3YRsvkgMlrryhuv8y08Y=s1600"
            }
        ]

        for data in new_vendors:
            # 1. Create User
            user = User.query.filter_by(email=data['email']).first()
            if not user:
                user = User(name=data['name'], email=data['email'], role='vendor')
                user.set_password('password123')
                db.session.add(user)
                db.session.commit()
            
            # 2. Create Vendor Profile
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
                    average_rating=4.9
                )
                if data['female_staff']:
                    vendor.female_staff_start_time = time(8, 0)
                    vendor.female_staff_end_time = time(22, 0)
                db.session.add(vendor)
                db.session.commit()
            
            # 3. Add Vendor Image
            if not VendorImage.query.filter_by(vendor_id=vendor.id, image_url=data['image']).first():
                img = VendorImage(vendor_id=vendor.id, image_url=data['image'])
                db.session.add(img)
        
        db.session.commit()
        print("Successfully added specific vendors with images.")

if __name__ == "__main__":
    populate()
