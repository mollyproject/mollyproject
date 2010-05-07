import simplejson

from django.db import models

class Batch(models.Model):
    title = models.TextField()
    local_name = models.TextField()
    provider_name = models.TextField()
    method_name = models.TextField()
    cron_stmt = models.TextField()
    enabled = models.BooleanField(default=True)

    _metadata = models.TextField(default='null')
    last_run = models.DateTimeField(null=True, blank=True)

    def get_metadata(self):
        try:
            return self.__metadata
        except AttributeError:
            self.__metadata = simplejson.loads(self._metadata)
            return self.__metadata
    def set_metadata(self, metadata):
        self.__metadata = metadata
    metadata = property(get_metadata, set_metadata)

    def save(self, *args, **kwargs):
        try:
            self._metadata = simplejson.dumps(self.__metadata)
        except AttributeError:
            pass
        super(Batch, self).save(*args, **kwargs)
