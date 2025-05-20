# Simple entry point to start the application
import os
import sys
from django.core.wsgi import get_wsgi_application
from flask import Flask, send_from_directory

# Add the music_player directory to Python path
sys.path.insert(0, os.path.abspath("music_player"))

# Set environment variables if not already set
if "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = "sqlite:///db.sqlite3"

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'music_player.settings')

# Create a Flask app to handle media file serving
flask_app = Flask(__name__)

@flask_app.route('/media/<path:path>')
def serve_media(path):
    """Serve media files"""
    media_root = os.path.join(os.path.abspath("."), 'music_player', 'media')
    return send_from_directory(media_root, path)

# Get the WSGI application and wrap it with Flask for media handling
django_app = get_wsgi_application()

class MediaHandlingMiddleware:
    def __init__(self, django_app, flask_app):
        self.django_app = django_app
        self.flask_app = flask_app
        
    def __call__(self, environ, start_response):
        path = environ.get('PATH_INFO', '')
        if path.startswith('/media/'):
            return self.flask_app(environ, start_response)
        return self.django_app(environ, start_response)

# Combined app that handles both Django and media files
app = MediaHandlingMiddleware(django_app, flask_app)

if __name__ == "__main__":
    # For local development
    from django.core.management import execute_from_command_line
    execute_from_command_line(["manage.py", "runserver", "0.0.0.0:5000"])
