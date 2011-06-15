import os
import os.path
import sys

from django.db import transaction
from django.db.utils import DatabaseError
from django.core.management import call_command
from django.core.management.base import NoArgsCommand
from django.conf import settings

from south.models import MigrationHistory

class Command(NoArgsCommand):
    
    can_import_settings = True

    def handle_noargs(self, **options):
        try:
            # This triggers a database lookup, if it fails (table doesn't exist)
            # then it means South hasn't been installed, so we need to do a
            # first sync to work around South's confusion between molly.auth
            # and django.contrib.auth
            savepoint = transaction.savepoint()
            MigrationHistory.objects.all()[0]
        except DatabaseError:
            transaction.savepoint_rollback(savepoint)
            print "Doing first sync..."
            call_command('syncdb', migrate_all=True)
            call_command('migrate', fake=True)
        else:
            print "Doing db sync..."
            call_command('syncdb')
            call_command('migrate')