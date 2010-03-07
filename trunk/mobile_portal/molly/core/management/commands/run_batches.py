from django.core.management.base import NoArgsCommand

from molly.conf import applications

def struct_to_datetime(s):
    return datetime.fromtimestamp(time.mktime(s))

class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list
    help = "Updates blog articles on the desktop site"

    requires_model_validation = True

    def handle_noargs(self, **options):
        for application in applications:
            print application
            print applications[application].batches
