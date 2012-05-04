try:
    import json
except ImportError:
    import simplejson as json

from django.conf import settings
from djcelery.models import PeriodicTask as PerodicTaskModel
from celery.task import PeriodicTask, Task
from celery.app import current_app


class Provider(object):

    def __call__(self):
        return self

    @classmethod
    def register_tasks(cls, *args, **kwargs):
        """Constructor, looks for decorated tasks and registers them with Celery,
        this is done in a non-standard way as Celery tasks can only be functions, not methods.

        Tasks with the run_every option set are subclasses of BatchTask which
        handles storing a cache of metadata between each task execution.
        """
        ins = cls(*args, **kwargs)
        for attr_name in dir(cls):
            if callable(getattr(cls, attr_name)):
                fun = getattr(cls, attr_name)
            else:
                continue
            if hasattr(fun, 'task'):
                # This is a decorated method
                periodic_task = 'run_every' in fun.task
                name = "%s.%s.%s" % (cls.__module__, cls.__name__, attr_name)
                new_attr_name = '__task_%s' % attr_name
                if periodic_task:
                    base = BatchTask

                    def run(self, **kwargs):
                        meth = getattr(self.provider, self.true_method)
                        metadata = self.get_metadata()
                        try:
                            return meth(**metadata)
                        except Exception, exc:
                            self.get_logger().warning(
                                    "Exception raised, retrying: %s" % exc)
                            self.retry(exc=exc, countdown=self.default_retry_delay,
                                    max_retries=self.max_retries)
                else:
                    base = Task

                    def run(self, *args, **kwargs):
                        meth = getattr(self.provider, self.true_method)
                        try:
                            return meth(*args)
                        except Exception, exc:
                            self.get_logger().warning(
                                    "Exception raised, retrying: %s" % exc)
                            self.retry(exc=exc, countdown=self.default_retry_delay,
                                    max_retries=self.max_retries)

                def __init__(self, provider=ins, base=base, kwargs=fun.task):
                    self.provider = provider
                    self.metadata = kwargs.get('initial_metadata', dict())
                    self.run_every = kwargs.get('run_every', None)
                    base.__init__(self)  # Only 1 base class, so this is safe.
                    self.default_retry_delay = kwargs.get('default_retry_delay',
                            settings.CELERY_RETRY_DELAY)
                    self.max_retries = kwargs.get('max_retries',
                            settings.CELERY_MAX_RETRIES)
                t = type(name, (base,), {'__init__': __init__,
                    '__module__': cls.__module__,
                    'run': run,
                    'name': name,
                    'true_method': new_attr_name,
                    })
                # We rename the decorated method to __task_<method_name>
                # and set the old method to the Task instance.
                setattr(ins, new_attr_name, getattr(ins, attr_name))
                setattr(ins, attr_name, t())
        return ins


class BatchTask(PeriodicTask):
    """Subclass of Celery's PeriodicTask which handles a local
    cache of metadata. This metadata is stored in the kwargs field on the
    djcelery.PeriodicTask model as JSON encoded kwargs.

    Our task metadata represents the return values from each task execution.
    This means you can cache (for example an ETag - see OSM provider) between
    task runs and save making uncecessary calls. Metadata is provided as the
    keyword arguments to all BatchTasks

    Tasks decorated which don't specify 'run_every' cannot store metadata.
    """
    abstract = True

    def get_metadata(self):
        """Metadata getter, the null value for metadata is an empty dict"""
        pt = PerodicTaskModel.objects.get(task=self.name)
        metadata = pt.kwargs or self.metadata
        if metadata:
            return json.loads(metadata)
        else:
            return {}

    def set_metadata(self, metadata, expires=None):
        PerodicTaskModel.objects.filter(task=self.name).update(
                kwargs=json.dumps(metadata))

    def after_return(self, status, value, *args, **kwargs):
        if value and isinstance(value, dict):
            try:
                self.set_metadata(value)
            except:
                self.get_logger().exception("Unable to store metadata.")


def task(**kwargs):
    """Sets a .task attribute on each function decorated, this indictes
    this function should be registered as a task with Celery

    TODO: Extend this functionality to implement a wrapping function to
    capture the kwargs passed through by celery.
    """
    def dec(fun):
        fun.task = kwargs
        return fun
    return dec


def queue_post_save(cls):
    """Overrides the save method, attempts to find the correct provider and
    schedule all periodic tasks to run on that provider.
    Use case: Add/Edit a Feed object and update the feeds

    NOTE: We use update_last_modified so we don't recursively queue this task
    """
    original_save = cls.save

    def save(self, update_last_modified=False, *arg, **kwargs):
        if not update_last_modified:
            app = current_app()
            provider = self.provider.split('.')[-1]
            for task in app.tasks:
                try:
                    if not app.tasks[task].run_every and task.find(provider) != -1:
                        app.tasks[task].apply_async(args=(self,))
                except:
                    pass
        return original_save(self, *arg, **kwargs)
    cls.save = save
    return cls
