import sys
import os

# Add the project root to sys.path
sys.path.append(os.getcwd())

from app import create_app, db
from app.models import Vendor

app = create_app()

def check_vendors():
    with app.app_context():
        vendors = Vendor.query.filter_by(is_verified=True, is_active=True).all()
        print(f"COUNT_VERIFIED_ACTIVE: {len(vendors)}")
        for v in vendors:
            print(f"VENDOR|ID:{v.id}|NAME:{v.business_name}|VER:{v.is_verified}|ACT:{v.is_active}|LAT:{v.latitude}|LNG:{v.longitude}")

if __name__ == "__main__":
    check_vendors()
