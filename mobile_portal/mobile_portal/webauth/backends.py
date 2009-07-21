from django.contrib.auth.models import User

class WebauthBackend:
    def authenticate(self, webauth_user):
        return webauth_user.user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

