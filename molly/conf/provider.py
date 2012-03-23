from celery.task import PeriodicTask, Task


class Provider(object):

    def __call__(self):
        return self

    @classmethod
    def register_tasks(cls, *args, **kwargs):
        """Constructor, looks for decorated tasks and registers them with Celery,
        this is done in a non-standard way as Celery tasks can only be functions, not methods.
        """
        ins = cls(*args, **kwargs)
        for attr_name in dir(cls):
            if callable(getattr(cls, attr_name)):
                fun = getattr(cls, attr_name)
            else:
                continue
            if hasattr(fun, 'task'):
                # This is a decorated method
                run_every = fun.task['run_every']
                name = "%s.%s.%s" % (cls.__module__, cls.__name__, attr_name)
                new_attr_name = '__task_%s' % attr_name
                if run_every:
                    base = PeriodicTask
                    def run(self, **kwargs):
                        meth = getattr(self.provider, self.true_method)
                        return meth(**self.metadata)
                else:
                    base = Task
                    def run(self, *args, **kwargs):
                        meth = getattr(self.provider, self.true_method)
                        return meth(*args, **kwargs)
                def __call__(self, *args, **kwargs):
                    meth = getattr(self.provider, self.true_method)
                    return meth(*args, **kwargs)
                def __init__(self, provider=ins, run_every=run_every,
                        metadata=fun.task['initial_metadata'], base=base):
                    self.provider = provider
                    self.run_every = run_every
                    self.metadata = metadata
                t = type(name, (base,), {'__init__': __init__,
                    '__call__': __call__,
                    'run': run,
                    '__module__': cls.__module__,
                    'name': name,
                    'true_method': new_attr_name,
                    })
                setattr(ins, new_attr_name, getattr(ins, attr_name))
                setattr(ins, attr_name, t())
        return ins


class BatchTask(PeriodicTask):
    """Subclass of Celery's PeriodicTask which handles a local
    cache of metadata.
    """
    abstract = True

    def after_return(self, status, value, *args, **kwargs):
        if value:
            self.metadata = value


def task(run_every=None, initial_metadata={}):
    def dec(fun):
        fun.task = {'run_every': run_every,
                'initial_metadata': initial_metadata}
        return fun
    return dec
