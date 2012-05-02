import djcelery

from molly.conf.applications import all_apps
from celery.signals import beat_init, worker_init


def init_providers():
    """Calls all the providers which in turns registers any Celery tasks
    attached to that provider.
    """
    for app in all_apps():
        for p in app.providers:
            p()


def celeryd_discover_tasks(sender=None, conf=None, **kwargs):
    init_providers()


def beat_update_schedule(sender=None, conf=None, **kwargs):
    """Calling get_schedule will sync the schedule with any discovered tasks."""
    celeryd_discover_tasks()
    sender.get_scheduler().get_schedule()


def prepare_celery():
    """Runs the djcelery loader which is required to set the correct backend/scheduler
    Then adds some signal callbacks to ensure all tasks are registered correctly.
    """
    djcelery.setup_loader()
    beat_init.connect(beat_update_schedule)
    worker_init.connect(celeryd_discover_tasks)
