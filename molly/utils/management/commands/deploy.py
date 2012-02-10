import os
from optparse import make_option

from django.core.management import call_command
from django.core.management.base import NoArgsCommand

class Command(NoArgsCommand):
    
    option_list = NoArgsCommand.option_list + (
        make_option('--develop',
            action='store_true',
            dest='develop',
            default=False,
            help='Create symlinks, rather than copy, existing media, then start the dev server'),
        ) + (
        make_option('--skip-cron',
            action='store_true',
            dest='skip_cron',
            default=False,
            help='Skip creating a crontab'),
        )
    
    def handle_noargs(self, skip_cron, develop, **options):
        call_command('sync_and_migrate')
        try:
            from molly.wurfl import wurfl_data
        except ImportError:
            no_wurfl = True
        else:
            no_wurfl = False
        if no_wurfl or not develop:
            call_command('update_wurfl')
        call_command('generate_markers', lazy=True)
        call_command('collectstatic', interactive=False, link=develop)
        # Forcing compression because it seems to not compress *sometimes* even if files
        # have been changed...
        call_command('synccompress')
        call_command('synccompress', force=True)
        if not skip_cron:
            call_command('create_crontab', write_system_cron=(os.name != 'nt'))
        if develop:
            call_command('runserver')

