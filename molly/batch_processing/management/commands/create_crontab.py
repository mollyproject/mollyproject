from optparse import make_option
from StringIO import StringIO
from subprocess import Popen, PIPE, call
import errno
import os
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
            make_option('--write-system-cron',
                action='store_true',
                dest='write_system_cron',
                default=False,
                help=(
                    "Write a system cronfile and link it to /etc/cron.d. "
                    "This option and --pipe-to-crontab are mutually "
                    "exclusive, so don't call both")),
            )
    
    def handle(self, *args, **options):
        if options['pipe_to_crontab'] and options['write_system_cron']:
            raise RuntimeError("Can't use --pipe-to-crontab and --write-system-cron together")
        if options['pipe_to_crontab']:
            f = StringIO()
        elif options['write_system_cron']:
            # Write a cronfile to ~/.cron
            homedir = os.getenv('USERPROFILE') or os.getenv('HOME')
            outdir = os.path.join(homedir, '.cron')
            try:
                os.mkdir(outdir)
            except OSError as e:
                # Just ignore if the directory already exists
                if e.errno != errno.EEXIST:
                    raise e
            filename = os.path.join(outdir, 'molly.cron')
            if os.path.exists(filename):
                os.remove(filename)
            f = open(filename, 'w')
            
            # Try to make our cron file owned by root and symlink it
            print "Attempting to give root ownership of %(filename)s and symlink it to /etc/cron.d/" % { 'filename': filename }
            cmd = "sudo sh -c 'chown root %(filename)s && ln -sf %(filename)s /etc/cron.d/'" % { 'filename': filename }
            returncode = call(cmd, shell=True)
            if returncode:
                print("Couldn't install your cronfile. File written to %(filename)s, try running:\n\n\t%(cmd)s" % {
                    'filename': filename,
                    'cmd': cmd,
                })
            
        elif len(args) == 0:
            f = sys.stdout
        else:
            f = open(args[0], 'w')
        
        create_crontab(f, include_user=options['write_system_cron'])
        
        if options['pipe_to_crontab']:
            cron = Popen('crontab', stdin=PIPE)
            cron.communicate(input=f.getvalue())
