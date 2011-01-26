import sys

from django.core.management.base import NoArgsCommand

from molly.batch_processing import create_crontab

class Command(NoArgsCommand):
    help = "Generates a crontab"

    def handle(self, *args, **options):
        if len(args) == 0:
            f = sys.stdout
        else:
            f = open(args[0], 'w')
            
        create_crontab(f)