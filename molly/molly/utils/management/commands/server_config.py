import os, sys

from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.template import loader, Context
from django.utils.importlib import import_module
from django.conf import settings

class Command(BaseCommand):
    help = 'Generates an Apache config'

    option_list = BaseCommand.option_list + (
        make_option('-m', '--module',
            action='store',
            dest='module',
            default='modpython',
            help='The Apache module to target (modpython or modwsgi)'),
        make_option('--ip',
            action='store',
            dest='server_ip',
            default=None,
            help='The IP of the server'),
        make_option('--host',
            action='store',
            dest='server_name',
            default=None,
            help='The hostname of the server'),
        make_option('--cert',
            action='store',
            dest='cert',
            default=None,
            help='The hostname of the server'),
        make_option('--cert-key',
            action='store',
            dest='cert_key',
            default=None,
            help='The hostname of the server'),
        )

    def handle(self, *args, **options):
        template = loader.get_template('utils/apache.conf')

        django_settings_module = os.environ['DJANGO_SETTINGS_MODULE']
        project = import_module(django_settings_module.split('.')[0])
        import django, molly

        use_https = any(app.secure for app in settings.APPLICATIONS)

        sys_path = map(os.path.normpath, [
            os.path.join(project.__path__[0], '..'),
        ] + filter(lambda x:x != '', sys.path))

        project_path = os.path.normpath(os.path.join(project.__path__[0], '..'))
        if project_path not in sys_path:
            sys_path.insert(0, project_path)

        sys_path = [p for i,p in enumerate(sys_path) if p not in sys_path[:i]]

        context = Context({
            'project_root': os.path.abspath(project.__path__[0]),
            'django_root': os.path.abspath(django.__path__[0]),
            'sys_path': sys_path,
            'use_https': use_https,
            'server_ip': self.get_server_ip(options),
            'django_settings_module': django_settings_module,
            'server_name': options.get('server_name'),
            'ssl_cert_file': os.path.abspath(options['cert']) if options['cert'] else None,
            'ssl_cert_key_file': os.path.abspath(options['cert_key']) if options['cert_key'] else None,
        })

        print template.render(context)

    def get_server_ip(self, options):
        if options.get('server_ip'):
            return options['server_ip']
        try:
            return settings.SERVER_IP
        except AttributeError:
            return '_default_'
