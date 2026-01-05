"""
SmartFridge Application Entry Point

Development server runner with debug mode.
For production, use wsgi.py with Gunicorn.
"""
import os
from app import create_app

# Create application instance
app = create_app(os.getenv('FLASK_CONFIG', 'development'))

if __name__ == '__main__':
    # Run development server
    app.run(
        host=os.getenv('FLASK_HOST', '127.0.0.1'),
        port=int(os.getenv('FLASK_PORT', 5000)),
        debug=app.config.get('DEBUG', True)
    )
