import sys

from django.core.management.base import NoArgsCommand

from molly.batch_processing.utils import run_batch

class Command(NoArgsCommand):
    help = "Runs a batch job"

    def handle(self, *args, **options):
        print run_batch(*args[0:3])