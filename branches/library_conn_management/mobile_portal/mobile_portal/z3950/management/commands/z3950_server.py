from django.core.management.base import NoArgsCommand

from mobile_portal.z3950.conn_manager import Z3950ConnectionManager

class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list
    help = "Runs the Z3950 Connection Manager"

    requires_model_validation = False


    def handle_noargs(self, **options):
        connection_manager = Z3950ConnectionManager()
        
        try:
            connection_manager.get_server().serve_forever()
        except (SystemExit, KeyboardInterrupt):
            connection_manager.leaving()
        