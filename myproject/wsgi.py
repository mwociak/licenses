import os
from django.core.wsgi import get_wsgi_application

# Ustawienie ścieżki do pliku ustawień Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings")

# Tworzymy obiekt WSGI, którego będzie używał Gunicorn
application = get_wsgi_application()
