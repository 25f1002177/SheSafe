from app import create_app, db
from app.models import Vendor, VendorImage

app = create_app()
with app.app_context():
    vendor = Vendor.query.get(5)
    if not vendor:
        print("Vendor 5 not found.")
    else:
        print(f"Vendor: {vendor.business_name}")
    with open('db_dump.txt', 'w') as f:
        vendors = Vendor.query.all()
        f.write("--- VENDORS ---\n")
        for v in vendors:
            f.write(f"Vendor ID: {v.id}, User ID: {v.user_id}, Name: {v.business_name}\n")
        
        images = VendorImage.query.all()
        f.write("\n--- IMAGES ---\n")
        for img in images:
            f.write(f"Img ID: {img.id}, Vendor ID: {img.vendor_id}, URL: {img.image_url}\n")
    print("DB info dumped to db_dump.txt")
