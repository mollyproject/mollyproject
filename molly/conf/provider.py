from celery.task import PeriodicTask
from celery.app import current_app


class Provider(object):
    def __init__(self, *args, **kwargs):
        self.class_path = None
        self.verbose_name = None
        self.app = current_app()

    def __call__(self):
        return self

    @classmethod
    def register_tasks(cls, *args, **kwargs):
        """Constructor, looks for decorated tasks and registers them with Celery,
        this is done in a non-standard way as Celery tasks can only be functions, not methods.
        """
        ins = cls(*args, **kwargs)
        class_path = "%s.%s" % (cls.__module__, cls.__name__)
        ins.class_path = class_path
        for name, fun in cls.__dict__.items():
            try:
                kwargs = fun.task['initial_metadata']
                run_every = fun.task['run_every']
                task_name = "%s.%s" % (class_path, name)
                def t(self, **kwargs):
                    meth = getattr(self.instance, self.method_name)
                    return meth(**self.metadata)
                task = type(task_name, (BatchTask,), {'run': t})
                task.run_every = run_every
                task.instance = ins
                task.method_name = name
                self.app.tasks.register(task)
            except Exception as e:
                continue
        return ins

class BatchTask(PeriodicTask):
    abstract = True
    def __init__(self):
        self.metadata = {}

    def after_return(self, status, value, *args, **kwargs):
        if value: self.metadata = value
