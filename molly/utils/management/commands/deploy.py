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
        )

    def handle_noargs(self, develop, **options):
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
        call_command('collectstatic', interactive=False, link=(develop and os.name != 'nt'))
        # Forcing compression because it seems to not compress *sometimes* even if files
        # have been changed...
        call_command('synccompress')
        call_command('synccompress', force=True)
        if develop:
            call_command('runserver')
