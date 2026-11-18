from django.core.asgi import get_asgi_application

from config.env import configure

configure()
application = get_asgi_application()
