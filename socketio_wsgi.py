import os
from django.core.wsgi import get_wsgi_application
from django_socketio import SocketIO

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

application = SocketIO(get_wsgi_application())
