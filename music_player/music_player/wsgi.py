"""
WSGI config for music_player project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'music_player.settings')

application = get_wsgi_application()
