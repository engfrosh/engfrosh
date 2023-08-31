from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User


class EmailOrUsernameAuthenticationBackend(BaseBackend):

    def authenticate(self, request, **kwargs):
        if 'username' not in kwargs or 'password' not in kwargs:
            return None
        username = kwargs['username']
        password = kwargs['password']
        try:
            if '@' in username:
                my_user = User.objects.get(email=username)
            else:
                my_user = User.objects.get(username=username)

        except User.DoesNotExist:
            return None
        else:
            if my_user.is_active and my_user.check_password(password):
                return my_user
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
