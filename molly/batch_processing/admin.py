import threading

from models import Batch
from django.contrib import admin
from django.utils.translation import ugettext as _

def run_batch(modeladmin, request, queryset):
    for batch in queryset:
        if not batch.currently_running:
            batch.pending = True
            batch.save()
        thread = threading.Thread(target=batch.run)
        thread.daemon = True
        thread.start()
run_batch.short__description = _("Run selected batch jobs")

class BatchAdmin(admin.ModelAdmin):
    list_display = ['title', 'cron_stmt', 'enabled', 'last_run',
                    'last_run_failed', 'pending', 'currently_running']
    ordering = ['title']
    actions = [run_batch]

admin.site.register(Batch, BatchAdmin)
