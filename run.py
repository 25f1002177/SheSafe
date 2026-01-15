import os
from app import create_app

# Get configuration from environment or use default
config_name = os.environ.get('FLASK_CONFIG', 'default')
app = create_app(config_name)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
