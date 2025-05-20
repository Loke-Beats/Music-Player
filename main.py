# Simple entry point to start the application
import os
import sys
from django.core.wsgi import get_wsgi_application

# Add the music_player directory to Python path
sys.path.insert(0, os.path.abspath("music_player"))

# Set environment variables if not already set
if "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = "sqlite:///db.sqlite3"

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'music_player.settings')

# Get the WSGI application
app = get_wsgi_application()

if __name__ == "__main__":
    # For local development
    from django.core.management import execute_from_command_line
    execute_from_command_line(["manage.py", "runserver", "0.0.0.0:5000"])
