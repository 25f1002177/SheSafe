import os
from app import create_app, db
from sqlalchemy import text

app = create_app()

def debug():
    with app.app_context():
        print("Testing database connection and queries...")
        try:
            from app.models import Vendor, VendorImage
            # Test simple vendor query
            v = Vendor.query.first()
            if v:
                print(f"Found vendor: {v.business_name}")
                # Test accessing images
                try:
                    imgs = v.images
                    print(f"Vendor has {len(imgs)} images")
                    if imgs:
                        print(f"First image URL: {imgs[0].image_url}")
                        # Try accessing new column
                        try:
                            data = imgs[0].image_data
                            print(f"First image data length: {len(data) if data else 0}")
                        except Exception as e:
                            print(f"ERROR accessing image_data: {e}")
                except Exception as e:
                    print(f"ERROR accessing images relationship: {e}")
            else:
                print("No vendors found.")
        except Exception as e:
            print(f"CRITICAL ERROR in debug: {e}")

if __name__ == "__main__":
    debug()
