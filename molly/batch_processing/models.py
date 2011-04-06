import simplejson, traceback, sys, logging
from datetime import datetime
from StringIO import StringIO

from django.db import models

from molly.conf import all_apps, app_by_local_name

logger = logging.getLogger("molly.batch_processing")

class TeeStringIO(StringIO):
    def __init__(self, *args, **kwargs):
        self.other = kwargs.pop('other')
        StringIO.__init__(self, *args, **kwargs)
        
    def write(self, *args, **kwargs):
        self.other.write(*args, **kwargs)
        StringIO.write(self, *args, **kwargs)

class Batch(models.Model):
    title = models.TextField()
    local_name = models.TextField()
    provider_name = models.TextField()
    method_name = models.TextField()
    cron_stmt = models.TextField()
    enabled = models.BooleanField(default=True)

    _metadata = models.TextField(default='null')
    last_run = models.DateTimeField(null=True, blank=True)
    pending = models.BooleanField(default=False)
    currently_running = models.BooleanField(default=False)
    log = models.TextField(blank=True)

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

    def run(self, tee_to_stdout=False):
        if self.currently_running:
            return
        
        try:
            output = TeeStringIO(other=sys.stdout) if tee_to_stdout else StringIO()
            
            self.currently_running = True
            self.pending = False
            self.save()
            
            
            providers = app_by_local_name(self.local_name).providers
            for provider in providers:
                if provider.class_path == self.provider_name:
                    break
            else:
                raise AssertionError
            
            method = getattr(provider, self.method_name)
            
            self.metadata = method(self.metadata, output)
        except Exception, e:
            if output.getvalue():
                output.write("\n\n")
            traceback.print_exc(file=output)
            logger.exception('Batch %r threw an uncaught exception' % self.title)
        finally:
            self.log = output.getvalue()
            self.last_run = datetime.utcnow()
            self.currently_running = False
            self.save()

    def __unicode__(self):
        return self.title