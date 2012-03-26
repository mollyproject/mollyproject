from settings import *
from molly.conf.applications import init_providers


# Celery configuration
CELERYBEAT_SCHEDULER = "djcelery.schedulers.DatabaseScheduler"
CELERYD_CONCURRENCY = 1

# Initialise all our providers. This registers the tasks with Celery.
# This *must* run for your Celery tasks to appear in djcelery/celerybeat
init_providers()
