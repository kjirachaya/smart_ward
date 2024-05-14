"""
ASGI config for smart_ward project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

# import os

# import socketio
# from django.core.asgi import get_asgi_application
# from patient.sockets import sio

# # import django
# # django.setup()

# # from django.core.management import call_command

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_ward.settings')
# django_asgi_app = get_asgi_application()

# application = socketio.ASGIApp(sio, django_asgi_app)

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_ward.settings')
django_asgi_app = get_asgi_application()


# its important to make all other imports below this comment
import socketio
from patient.sockets import sio


application = socketio.ASGIApp(sio, django_asgi_app)

