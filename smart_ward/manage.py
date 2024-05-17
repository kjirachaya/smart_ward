#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import uvicorn

def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_ward.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)

def init_socketio():
    os.system('python manage.py runserver_socketio 0.0.0.0:9000')

socketio_thread = Thread(target=init_socketio, args=())
socketio_thread.start()

if __name__ == '__main__':
    #main()
    uvicorn.run("smart_ward.asgi:application", reload=True)

