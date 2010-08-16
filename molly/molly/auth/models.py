try:
    import cPickle as pickle
except ImportError:
    import pickle

from django.db import models
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
    secure_session_key = models.CharField(max_length=40)

    device_name = models.TextField()
    last_used = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('user', 'device_name', 'secure_session_key',)

class ExternalServiceToken(models.Model):
    user = models.ForeignKey(User)
    namespace = models.CharField(max_length=32)
    value = models.TextField()

    @property
    def service_name(self):
        try:
            return app_by_local_name(self.namespace).title
        except Exception, e:
            print self.namespace, type(e), e
            raise

    @classmethod
    def get(cls, user, namespace, default=None):
        try:
            token = cls.objects.get(user=user, namespace=namespace)
            return pickle.loads(str(token.value))
        except cls.DoesNotExist:
            return default

    @classmethod
    def set(cls, user, namespace, value):
        try:
            token = cls.objects.get(user=user, namespace=namespace)
        except cls.DoesNotExist:
            token = cls(user=user, namespace=namespace)
        token.value = pickle.dumps(value)
        token.save()

    @classmethod
    def remove(cls, user, namespace):
        cls.objects.filter(user=user, namespace=namespace).delete()
