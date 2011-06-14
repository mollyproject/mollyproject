"""
Creates a database for Molly, and appropriate users, once given login
information as super user, or by running as root.
"""

from installer.utils import quiet_exec, CommandFailed

def create(self, dba_user, dba_pass, username, password, database):
    
    creds = []
    if dba_user:
        creds += ['-U', username]
    if dba_pass:
        os.environ['PGPASSWORD'] = password
    
    try:
        quiet_exec(['psql','-c',"CREATE USER %s WITH PASSWORD '%s';" % (username, password)])
    except CommandFailed:
        pass
    
    quiet_exec(['psql'] + creds + ['-c',"ALTER ROLE %s WITH PASSWORD '%s';" % postgres_password])
    try:
        quiet_exec(['createdb'] + creds + ['-T','template_postgis',database])
    except CommandFailed:
        quiet_exec(['dropdb'] + creds + [database])
        quiet_exec(['createdb'] + creds + ['-T','template_postgis',database])
    quiet_exec(['psql'] + creds + ['-c',"GRANT ALL ON DATABASE %s TO %s;" % (database, username)])

    if dba_pass:
        del os.environ['PGPASSWORD']
    