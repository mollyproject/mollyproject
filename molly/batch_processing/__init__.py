import getpass
import simplejson
import os
import os.path
import imp
import sys
from subprocess import call, check_call
from datetime import datetime, timedelta

from django.conf import settings

from molly.conf import all_apps, app_by_local_name, app_by_application_name
from molly.batch_processing.models import Batch
from molly.utils.misc import get_norm_sys_path

def load_batches():
    batch_details = []
    for app in all_apps():
        for provider in app.providers:
            for method_name in dir(provider):
                method = getattr(provider, method_name)
                if not getattr(method, 'is_batch', False):
                    continue
                    
                batch_details.append({
                    'title': method.__doc__ or provider.class_path,
                    'local_name': app.local_name,
                    'provider_name': provider.class_path,
                    'method_name': method_name,
                    'cron_stmt': method.cron_stmt,
                    'initial_metadata': method.initial_metadata,
                })

    batches = set()
    for batch_detail in batch_details:
        batch, created = Batch.objects.get_or_create(
            local_name = batch_detail['local_name'],
            provider_name = batch_detail['provider_name'],
            method_name = batch_detail['method_name'],
            defaults = {'title': batch_detail['title'],
                        'cron_stmt': batch_detail['cron_stmt'],
                        '_metadata': simplejson.dumps(batch_detail['initial_metadata'])})
        batches.add(batch)
    for batch in Batch.objects.all():
        if not batch in batches:
            batch.delete()

def run_batch(local_name, provider_name, method_name, tee_to_stdout=True):
    # This will force the loading of the molly.utils app, attaching its log
    # handler lest the batch logs anything that needs e-mailing.
    app_by_application_name('molly.utils')
    
    batch = Batch.objects.get(
        local_name=local_name,
        provider_name=provider_name,
        method_name=method_name)

    batch.run(tee_to_stdout)

    return batch.log

def _escape(s):
    return s.replace('\\', '\\\\').replace('"', '\\"')

if os.name == 'nt':
    def create_crontab(filename):
        def next_hour(minute):
            if datetime.now().time().minute < int(minute):
                return datetime.now().hour
            else:
                return str((datetime.now() + timedelta(hours=1)).hour).rjust(2, '0')
        
        load_batches()
        
        # Use the Windows task scheduler to create tasks
        # http://support.microsoft.com/kb/814596
        for batch in Batch.objects.all():
            # Delete any old scheduling of this task
            call(['schtasks', '/delete', '/f', '/tn', batch.provider_name])
            
            # Try and convert a cron statement into a Windows one...
            minute, hour, day, month, dow = batch.cron_stmt.split()
            
            # This doesn't capture all cases, but it does capture the ones
            # that ship with Molly, and most common ones. Please report any
            # bugs that affect you at issues.mollyproject.org
            if month != '*':
                args = ['/sc', 'MONTHLY']
                args += ['/m', ','.join(map(lambda mon: {
                    '1': 'JAN',
                    '2': 'FEB',
                    '3': 'MAR',
                    '4': 'APR',
                    '5': 'MAY',
                    '6': 'JUN',
                    '7': 'JUL',
                    '8': 'AUG',
                    '9': 'SEP',
                    '10': 'OCT',
                    '11': 'NOV',
                    '12': 'DEC',
                }.get(mon, mon), month.split(',')))]
                args += ['/d', day,
                         '/st', '%s:%s:00' % (hour.rjust(2, '0'), minute.rjust(2, '0'))]
            
            elif day != '*':
                args = ['/sc', 'MONTHLY',
                        '/d', day,
                        '/st', '%s:%s:00' % (hour.rjust(2, '0'), minute.rjust(2, '0'))]
            
            elif dow != '*':
                args = ['/sc', 'WEEKLY',
                        '/d', {
                             '0': 'SUN',
                             '1': 'MON',
                             '2': 'TUE',
                             '3': 'WED',
                             '4': 'THU',
                             '5': 'FRI',
                             '6': 'SAT',
                             '7': 'SUN',
                         }.get(dow, dow.upper()),
                        '/st', '%s:%s:00' % (hour.rjust(2, '0'), minute.rjust(2, '0'))]
            
            elif hour != '*':
                if '/' in hour or ',' in hour:
                    if '/' in hour:
                        times, frequency = hour.split('/')
                        times = times.split('-')[0]
                    else:
                        times, second = hour.split(',')[:2]
                        frequency = str(int(second) - int(times))
                    
                    args = ['/sc', 'HOURLY',
                            '/mo', frequency,
                            '/st', '%s:%s:00' % (next_hour(minute), minute.rjust(2, '0'))]
                
                else:
                    args = ['/sc', 'DAILY',
                            '/st', '%s:%s:00' % (hour.rjust(2, '0'), minute.rjust(2, '0'))]
            
            elif minute != '*':
                if '/' in minute or ',' in minute:
                    if '/' in minute:
                        times, frequency = minute.split('/')
                        times = times.split('-')[0]
                    else:
                        times, second = minute.split(',')[:2]
                        frequency = str(int(second) - int(times))
                    
                    args = ['/sc', 'MINUTE',
                            '/mo', frequency,
                            '/st', '%s:%s:00' % (next_hour(times), times.rjust(2, '0'))]
                    
                else:
                    # Can't guarantee when on the hour this runs, from what I
                    # can see?
                    args = ['/sc', 'HOURLY',
                            '/st', '%s:%s:00' % (next_hour(minute), minute.rjust(2, '0'))]
            
            else:
                args = ['/sc', 'MINUTE']
            
            try:
                project_path = imp.find_module(os.environ['DJANGO_SETTINGS_MODULE'].split('.')[0])[1]
            except ImportError:
                project_path = os.path.dirname(imp.find_module('settings')[1])
            
            command = "'%s' '%s' run_batch '%s' '%s' '%s'" % (
                os.path.join(os.path.dirname(sys.executable), 'pythonw.exe'),
                os.path.abspath(os.path.join(project_path, 'manage.py')),
                batch.local_name,
                batch.provider_name,
                batch.method_name,
                )
            
            # Create a new task
            check_call(['schtasks', '/create',
                        '/tn', batch.provider_name, # Task name
                        '/tr', command, # Command to run
                        ] + args)
    
else:

    def create_crontab(filename, include_user=False):
        """
        If include_user is True, generates a cron file with a user column,
        suitable for use in /etc/cron.d
        """
        load_batches()
    
        sys_path = get_norm_sys_path()
    
        f = open(filename, 'w') if isinstance(filename, basestring) else filename
        f.write("# Generated by Molly. Do not edit by hand, or else your changes\n")
        f.write("# will be overwritten.\n\n")
        f.write('MAILTO="%s"\n' % ','.join(l[1] for l in settings.ADMINS))
        f.write("DJANGO_SETTINGS_MODULE=%s\n" % os.environ['DJANGO_SETTINGS_MODULE'])
        f.write("PYTHONPATH=%s\n\n" % ':'.join(sys_path))
    
        for batch in Batch.objects.all():
            if not batch.enabled:
                continue
            
            line_args = {
                'time': batch.cron_stmt.ljust(20),
                'user': '',
                'python': sys.executable,
                'run_batch': os.path.abspath(os.path.join(os.path.dirname(__file__), 'scripts', 'run_batch.py')),
                'batch_local_name': _escape(batch.local_name),
                'batch_provider_name': _escape(batch.provider_name),
                'batch_method_name': _escape(batch.method_name),
            }
            if include_user:
                line_args['user'] = getpass.getuser()
            
            f.write(
                '%(time)s %(user)s %(python)s %(run_batch)s '
                '"%(batch_local_name)s" "%(batch_provider_name)s" '
                '"%(batch_method_name)s"\n' % line_args)

        f.close()
