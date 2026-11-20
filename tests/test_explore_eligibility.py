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
        real = sorted(n for n in names if n.startswith(('Real', 'Seed')))
        self.assertEqual(real, ['Real Far Chennai', 'Real Kharagpur', 'Real Kolkata'])
        self.assertIn('The New Tikka', names)  # presentation listing, same map and ranking

    def test_demo_mode_only_seeds(self):
        self.assertEqual(listed(self.c, '/explore?area=ashoka'), ['Seed Haryana'])
        self.assertNotIn('The New Tikka', listed(self.c, '/explore?area=ashoka'))

    def test_no_radius_cutoff_data_kept(self):
        self.assertIn('Real Far Chennai', listed(self.c, '/explore'))


class Booking(T):
    def test_presentation_booking_flow_pay_at_location(self):
        from app.models import Booking as B
        r = self.c.get('/demo/venue/kgp-1'); self.assertEqual(r.status_code, 200)
        self.assertIn('Book a visit', r.get_data(as_text=True))
        r = self.c.post('/demo/book/kgp-1', data={'visit_date': '2026-11-25T10:30', 'payment_mode': 'pay_at_location'})
        self.assertEqual(r.status_code, 302)
        r = self.c.get(r.headers['Location']); html = r.get_data(as_text=True)
        self.assertIn('Booking confirmed', html); self.assertIn('data:image/png;base64', html)
        hist = self.c.get('/user/dashboard?tab=history').get_data(as_text=True)
        self.assertIn('The New Tikka', hist); self.assertIn('View QR Pass', hist)
        self.assertEqual(B.query.count(), 0)  # nothing written to production tables

    def test_pass_and_bad_token(self):
        self.c.post('/demo/book/kgp-1', data={'visit_date': '2026-11-25T10:30', 'payment_mode': 'pay_at_location'})
        self.assertEqual(self.c.get('/demo/pass?t=bad').status_code, 403)


class Paid(T):
    def test_paid_callback_hands_off_without_session(self):
        import os, hmac, hashlib
        from unittest import mock
        os.environ['RAZORPAY_KEY_ID'] = 'rzp_test_x'; os.environ['RAZORPAY_KEY_SECRET'] = 'sek'
        with mock.patch('app.routes.razorpay_create_order', return_value={'id': 'order_X1'}):
            r = self.c.post('/demo/book/kgp-2', data={'visit_date': '2026-11-25T10:30', 'payment_mode': 'app'})
        self.assertIn('/demo/pay?t=', r.headers['Location'])
        tok = r.headers['Location'].split('t=')[1]
        self.assertIn('Pay with Razorpay', self.c.get(r.headers['Location']).get_data(as_text=True))
        sig = hmac.new(b'sek', b'order_X1|pay_Y2', hashlib.sha256).hexdigest()
        anon = self.app.test_client()  # cross-site POST carries no session
        r2 = anon.post('/demo/pay/callback?t=' + tok, data={'razorpay_order_id': 'order_X1', 'razorpay_payment_id': 'pay_Y2', 'razorpay_signature': sig})
        self.assertIn('/demo/confirm?t=', r2.headers['Location'])
        r3 = self.c.get(r2.headers['Location']); self.assertEqual(r3.status_code, 302)
        self.assertIn('Paid', self.c.get(r3.headers['Location']).get_data(as_text=True))
        bad = anon.post('/demo/pay/callback?t=' + tok, data={'razorpay_order_id': 'order_X1', 'razorpay_payment_id': 'pay_Y2', 'razorpay_signature': 'x'})
        self.assertIn('/demo/pay?t=', bad.headers['Location'])
