"""
SmartFridge WSGI Entry Point

Production-ready WSGI application for use with
Gunicorn, uWSGI, or other WSGI servers.

Usage with Gunicorn:
    gunicorn -w 4 -b 0.0.0.0:8000 wsgi:application
    
Usage with uWSGI:
    uwsgi --http :8000 --wsgi-file wsgi.py --callable application
"""
import os
from app import create_app

# Create the WSGI application
application = create_app(os.getenv('FLASK_CONFIG', 'production'))

# Alias for compatibility with different WSGI servers
app = application
