from celery.app import current_app
from molly.conf.celery_util import init_providers
from djcelery.admin import PeriodicTaskAdmin


def run_now(modeladmin, request, queryset):
    app = current_app()
    for pt in queryset:
        try:
            app.tasks[pt.task].apply_async()
        except KeyError:
            init_providers()
            app.tasks[pt.task].apply_async()
run_now.short_description = "Place this task on queue to run now."


class RunnablePeriodicTaskAdmin(PeriodicTaskAdmin):
    actions = [run_now]
