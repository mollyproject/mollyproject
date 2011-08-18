from optparse import make_option
from StringIO import StringIO
from subprocess import Popen, PIPE
import sys

from django.core.management.base import NoArgsCommand

from molly.batch_processing import create_crontab

class Command(NoArgsCommand):
    help = "Generates a crontab"
    
    option_list = NoArgsCommand.option_list + (
            make_option('--pipe-to-crontab',
                action='store_true',
                dest='pipe_to_crontab',
                default=False,
                help='Pipe the cron output directly to the crontab command'),
            )
    
    def handle(self, *args, **options):
        if options['pipe_to_crontab']:
            f = StringIO()
        elif len(args) == 0:
            f = sys.stdout
        else:
            f = open(args[0], 'w')
        
        create_crontab(f)
        
        if options['pipe_to_crontab']:
            cron = Popen('crontab', stdin=PIPE)
            cron.communicate(input=f.getvalue())
