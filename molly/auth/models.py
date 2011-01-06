try:
    raise ImportError
    import cPickle as pickle
except ImportError:
    import pickle

from django.db import models
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from molly.conf import app_by_local_name

class UserIdentifier(models.Model):
    user = models.ForeignKey(User)
    namespace = models.CharField(max_length=32)
    value = models.CharField(max_length=128)

    updated = models.DateTimeField(auto_now_add=True)

    @classmethod
    def get(cls, user, namespace):
        try:
            identifier = cls.objects.get(user=user, namespace=namespace)
            return identifier.value
        except cls.DoesNotExist:
            return None

    @classmethod
    def set(cls, user, namespace, value):
        try:
            identifer = cls.objects.get(user=user, namespace=namespace)
        except cls.DoesNotExist:
            identifer = cls(user=user, namespace=namespace)
        identifer.value = value
        identifer.save()

class UserSession(models.Model):
    user = models.ForeignKey(User)
    secure_session_key = models.CharField(max_length=40, unique=True)

    device_name = models.TextField()
    last_used = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('user', 'device_name', 'secure_session_key',)

class ExternalServiceToken(models.Model):
    user = models.ForeignKey(User)
    namespace = models.CharField(max_length=32)
    authorized = models.BooleanField(default=False)
    value = models.TextField()

    @property
    def service_name(self):
        return app_by_local_name(self.namespace).title

    @property
    def service_url(self):
        return reverse(self.namespace + ':index')

    @classmethod
    def get(cls, user, namespace, default=None):
        try:
            token = cls.objects.get(user=user, namespace=namespace)
            return pickle.loads(str(token.value))
        except cls.DoesNotExist:
            return default

    @classmethod
    def set(cls, user, namespace, value, authorized = None):
        try:
            token = cls.objects.get(user=user, namespace=namespace)
        except cls.DoesNotExist:
            token = cls(user=user, namespace=namespace)
        if authorized is not None:
            token.authorized = authorized
        token.value = pickle.dumps(value)
        token.save()

    @classmethod
    def remove(cls, user, namespace):
        cls.objects.filter(user=user, namespace=namespace).delete()
