import sys

from django.core.management.base import NoArgsCommand

from molly.batch_processing import run_batch

class Command(NoArgsCommand):
    help = "Runs a batch job"

    def handle(self, *args, **options):
        run_batch(*args[0:3])