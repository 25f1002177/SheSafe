from app import create_app, db
from app.models import Vendor
import os

app = create_app()

def migrate():
    with app.app_context():
        # List of desired vendors and their images
        mappings = [
            {
                "old_name": "Savoy Greens Rest Stop",
                "new_name": "Highway Dhaba",
                "img": "static/img/verified/dhaba_verified.png"
            },
            {
                "old_name": "Green Chick Chop Kundli",
                "new_name": "Golden Hut",
                "img": "static/img/verified/restaurant_verified.png"
            },
            {
                "old_name": "Domino's Customer Safe Zone",
                "new_name": "Petrol Pump",
                "img": "static/img/verified/petrol_pump_verified.png"
            },
            {
                "old_name": "Parker Mall Management",
                "new_name": "Galaxy Hospital",
                "img": "static/img/verified/hospital_verified.png"
            }
        ]
        
        for m in mappings:
            vendor = Vendor.query.filter_by(business_name=m['old_name']).first()
            if not vendor:
                # Try to find by partial name or just take any other
                vendor = Vendor.query.filter(Vendor.business_name.like(f"%{m['new_name']}%")).first()
            
            if vendor:
                vendor.business_name = m['new_name']
                vendor.thumbnail_url = m['img']
                vendor.is_verified = True
                vendor.is_active = True
                print(f"Updated vendor: {vendor.business_name} with image {m['img']}")
            else:
                print(f"Could not find vendor for {m['old_name']} or {m['new_name']}")
        
        db.session.commit()
        print("Migration complete.")

if __name__ == "__main__":
    migrate()
