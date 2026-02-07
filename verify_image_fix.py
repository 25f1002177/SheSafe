import os
from app import create_app, db
from flask import url_for

app = create_app()
app.config['SERVER_NAME'] = 'localhost'

with app.app_context():
    # Test route for a dummy image
    filename = 'test_image.jpg'
    
    # 1. Test URL Generation
    generated_url = url_for('main.serve_uploads', filename=filename)
    print(f"Generated URL: {generated_url}")
    expected_url = f"/uploads/{filename}"
    if generated_url == expected_url:
        print("PASS: URL generation matches expected /uploads/ path.")
    else:
        print(f"FAIL: Expected {expected_url}, got {generated_url}")

    # 2. Test Route Behavior logic
    # We can't easily test the actual download without a running server, 
    # but we can verify the logic in routes.py by inspection or mocking.
    from app.routes import serve_uploads
    import unittest.mock as mock

    print("\nVerifying serve_uploads logic...")
    with mock.patch('os.environ.get') as mock_env:
        with mock.patch('flask.send_from_directory') as mock_send:
            # Test Vercel path
            mock_env.return_value = '1'
            serve_uploads(filename)
            mock_send.assert_called_with('/tmp/uploads', filename)
            print("PASS: Vercel mode uses /tmp/uploads")

            # Test Local path (mocking env to return None for VERCEL)
            mock_env.return_value = None
            serve_uploads(filename)
            # It should call with the local static/uploads path
            args, kwargs = mock_send.call_args
            if 'static' in args[0] and 'uploads' in args[0]:
                print(f"PASS: Local mode uses static uploads path: {args[0]}")
            else:
                print(f"FAIL: Unexpected local path: {args[0]}")
