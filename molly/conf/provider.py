from celery.task import PeriodicTask


class Provider(object):
    def __init__(self, *args, **kwargs):
        self.class_path = None
        self.verbose_name = None

    def __call__(self):
        return self

    @classmethod
    def register_tasks(cls, *args, **kwargs):
        """Constructor, looks for decorated tasks and registers them with Celery,
        this is done in a non-standard way as Celery tasks can only be functions, not methods.
        """
        class_path = "%s.%s" % (cls.__module__, cls.__name__)
        ins = cls(*args, **kwargs)
        ins.class_path = class_path
        for name, fun in cls.__dict__.items():
            if hasattr(fun, 'task'):
                run_every = fun.task['run_every']
                name = "%s.%s" % (class_path, name)
                def run(self, **kwargs):
                    meth = getattr(self.provider, self.name.split('.')[-1])
                    return meth(**self.metadata)
                def init(self, provider=ins, run_every=run_every, metadata=fun.task['initial_metadata']):
                    self.provider = provider
                    self.run_every = run_every
                    self.metadata = metadata
                    super(BatchTask, self).__init__()
                type(name, (BatchTask,), {'__init__': init,
                    'run': run,
                    '__module__': cls.__module__,
                    'name': name,
                    })
        return ins


class BatchTask(PeriodicTask):
    """Subclass of Celery's PeriodicTask which handles a local
    cache of metadata.
    """
    abstract = True
    def after_return(self, status, value, *args, **kwargs):
        if value: self.metadata = value

def task(run_every=None, initial_metadata={}):
    def dec(fun):
        fun.task = {'run_every': run_every,
                'initial_metadata':initial_metadata}
        return fun
    return dec
