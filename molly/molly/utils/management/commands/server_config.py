import os

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

        context = Context({
            'project_import_root': os.path.normpath(os.path.join(project.__path__[0], '..')),
            'project_root': project.__path__[0],
            'django_root': django.__path__[0],
            'molly_import_root': os.path.normpath(os.path.join(molly.__path__[0], '..')),
            'use_https': use_https,
            'server_ip': self.get_server_ip(options),
            'django_settings_module': django_settings_module,
            'server_name': options.get('server_name'),
            'ssl_cert_file': os.path.abspath(options.get('cert', '')),
            'ssl_cert_key_file': os.path.abspath(options.get('cert_key', '')),
        })

        print template.render(context)

    def get_server_ip(self, options):
        if options.get('server_ip'):
            return options['server_ip']
        try:
            return settings.SERVER_IP
        except AttributeError:
            return '_default_'