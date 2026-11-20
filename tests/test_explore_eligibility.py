"""Isolated fixtures (in-memory sqlite). Never touches live data."""
import json, re, unittest
from app import create_app, db
from app.models import User, Vendor


def mk(name, email, lat, lng, verified=True, active=True):
    u = User(name=name, email=email, role='vendor'); u.set_password('x')
    db.session.add(u); db.session.commit()
    v = Vendor(user_id=u.id, business_name=name, latitude=lat, longitude=lng, address='addr',
               is_verified=verified, is_active=active)
    db.session.add(v); db.session.commit()


def listed(client, url):
    html = client.get(url).get_data(as_text=True)
    blob = re.search(r'id="vendors-json" type="application/json">(.*?)</script>', html, re.S).group(1)
    return [v['name'] for v in json.loads(blob)]


class T(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.ctx = self.app.app_context(); self.ctx.push()
        db.create_all()
        u = User(name='c', email='c@example.org', role='user'); u.set_password('x')
        db.session.add(u); db.session.commit()
        mk('Real Kolkata', 'a@real.org', 22.57, 88.36)
        mk('Real Kharagpur', 'b@real.org', 22.31, 87.31)
        mk('Real Far Chennai', 'c@real.org', 13.08, 80.27)
        mk('Real Unverified', 'd@real.org', 22.31, 87.32, verified=False)
        mk('Real Inactive', 'e@real.org', 22.31, 87.33, active=False)
        mk('Seed Haryana', 's@shesafe.com', 28.95, 77.09)
        self.c = self.app.test_client()
        with self.c.session_transaction() as s:
            s['_user_id'] = str(u.id); s['_fresh'] = True

    def tearDown(self):
        db.session.remove(); db.drop_all(); self.ctx.pop()

    def test_primary_excludes_seeds_unverified_inactive(self):
        names = listed(self.c, '/explore')
        self.assertEqual(sorted(names), ['Real Far Chennai', 'Real Kharagpur', 'Real Kolkata'])

    def test_demo_mode_only_seeds(self):
        self.assertEqual(listed(self.c, '/explore?area=ashoka'), ['Seed Haryana'])

    def test_no_radius_cutoff_data_kept(self):
        self.assertIn('Real Far Chennai', listed(self.c, '/explore'))
