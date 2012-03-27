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
                        return meth(*args)
                def __call__(self, *args, **kwargs):
                    meth = getattr(self.provider, self.true_method)
                    return meth(*args)
                def __init__(self, provider=ins, run_every=run_every,
                        metadata=fun.task['initial_metadata'], base=base):
                    self.provider = provider
                    self.run_every = run_every
                    self.metadata = metadata
                    base.__init__(self)  # Only 1 base class, so this is safe.
                t = type(name, (base,), {'__init__': __init__,
                    '__call__': __call__,
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
    cache of metadata.
    """
    abstract = True

    def after_return(self, status, value, *args, **kwargs):
        if value:
            self.metadata = value


def task(run_every=None, initial_metadata={}):
    """Sets a .task attribute on each function decorated, this indictes
    this function should be registered as a task with Celery

    TODO: Extend this functionality to implement a wrapping function to
    capture the kwargs passed through by celery.
    """
    def dec(fun):
        fun.task = {'run_every': run_every,
                'initial_metadata': initial_metadata}
        return fun
    return dec
