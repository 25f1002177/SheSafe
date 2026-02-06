import sys
import os

# Add the project root to sys.path
sys.path.append(os.getcwd())

from app import create_app, db
from app.models import Vendor
from flask import render_template

app = create_app()

def debug_render():
    with app.app_context():
        vendors = Vendor.query.filter_by(is_verified=True, is_active=True).all()
        print(f"DEBUG: Found {len(vendors)} vendors in DB.")
        
        # Simulate rendering explore.html
        rendered = render_template('explore.html', vendors=vendors)
        start_idx = rendered.find('data-vendors=')
        if start_idx != -1:
            end_idx = rendered.find(' class="hidden">', start_idx)
            data_attr = rendered[start_idx:end_idx]
            print("RENDERED DATA-VENDORS ATTR (EXPLORE):")
            print(data_attr[:500] + "...")
        else:
            print("ERROR: data-vendors not found in rendered explore.html")

        # Simulate rendering welcome.html
        rendered_w = render_template('welcome.html', vendors=vendors)
        start_idx_w = rendered_w.find('data-vendors=')
        if start_idx_w != -1:
            end_idx_w = rendered_w.find(' class="hidden">', start_idx_w)
            data_attr_w = rendered_w[start_idx_w:end_idx_w]
            print("\nRENDERED DATA-VENDORS ATTR (WELCOME):")
            print(data_attr_w[:500] + "...")
        else:
            print("ERROR: data-vendors not found in rendered welcome.html")

if __name__ == "__main__":
    debug_render()
