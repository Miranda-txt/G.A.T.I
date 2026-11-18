from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q


class IdentityBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None
        User = get_user_model()
        # Não escolhe silenciosamente entre identificadores ambíguos.
        matches = list(User.objects.filter(Q(username__iexact=username) | Q(email__iexact=username))[:2])
        if len(matches) != 1:
            User().set_password(password)
            return None
        user = matches[0]
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
