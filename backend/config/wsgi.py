from django.core.wsgi import get_wsgi_application

from config.env import configure

configure()
application = get_wsgi_application()
