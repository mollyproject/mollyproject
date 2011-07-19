"""
Creates a database for Molly, and appropriate users, once given login
information as super user, or by running as root.
"""

import os

from molly.installer.utils import quiet_exec, CommandFailed

def create(dba_user, dba_pass, username, password, database):
    
    creds = []
    if dba_user:
        creds += ['-U', dba_user]
    if dba_pass:
        os.environ['PGPASSWORD'] = dba_pass
    
    try:
        quiet_exec(['psql'] + creds + ['-c',"CREATE USER %s WITH PASSWORD '%s';" % (username, password)], 'dbcreate')
    except CommandFailed:
        pass
    
    quiet_exec(['psql'] + creds + ['-c',"ALTER ROLE %s WITH PASSWORD '%s';" % (username, password)], 'dbcreate')
    try:
        quiet_exec(['createdb'] + creds + ['-T','template_postgis',database], 'dbcreate')
    except CommandFailed:
        quiet_exec(['dropdb'] + creds + [database], 'dbcreate')
        quiet_exec(['createdb'] + creds + ['-T','template_postgis',database], 'dbcreate')
    quiet_exec(['psql'] + creds + ['-c',"GRANT ALL ON DATABASE %s TO %s;" % (database, username)], 'dbcreate')

    if dba_pass:
        del os.environ['PGPASSWORD']
    