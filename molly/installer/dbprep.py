"""
Creates a postgis template, and optionally provides a default security
configuration for Molly in Postgres
"""

import os
from distutils.errors import DistutilsSetupError

from molly.installer.utils import quiet_exec
from molly.installer.sysprep import POSTGIS_PATH, SPATIAL_REF_SYS_PATH, PG_HBA_PATH

def create_postgis_template(username, password):
    # Setup PostGIS
    print "Configuring PostGIS...",
    sys.stdout.flush()
    
    creds = []
    if username:
        creds += ['-U', username]
    if password:
        os.environ['PGPASSWORD'] = password
    
    # Create the template spatial database.
    quiet_exec(['createdb','-E','UTF8'] + creds + ['template_postgis'])
    
    # Adding PLPGSQL language support.
    quiet_exec(['createlang'] + creds + ['-d','template_postgis','plpgsql'])
    
    # Loading the PostGIS SQL routines
    quiet_exec(['psql'] + creds + ['-d','template_postgis','-f',POSTGIS_PATH])
    quiet_exec(['psql'] + creds + ['-d','template_postgis','-f',SPATIAL_REF_SYS_PATH])
    quiet_exec(['psql'] + creds + ['-d','postgres','-c',"UPDATE pg_database SET datistemplate='true' WHERE datname='template_postgis';"])
    
    # Enabling users to alter spatial tables.
    quiet_exec(['psql'] + creds + ['-d','template_postgis','-c','GRANT ALL ON geometry_columns TO PUBLIC;'])
    quiet_exec(['psql'] + creds + ['-d','template_postgis','-c','GRANT ALL ON spatial_ref_sys TO PUBLIC;'])
    
    if password:
        del os.environ['PGPASSWORD']
    
    print "DONE!"

def configure_pg_hba():
    if os.getuid() != 0:
        raise DistutilsSetupError('You must run this script as root')
    
    print "WARNING! This will override your pg_hba.conf - press return only if"
    print "you want to continue, else press Ctrl+C to exit."
    raw_input()
    print
    print "Configuring Postgres...",
    sys.stdout.flush()
    
    pg_hba = open(PG_HBA_PATH, 'w')
    pg_hba.write("""
# This file was written by the Molly installer
local   molly       molly                             md5
host    molly       molly       127.0.0.1/32          md5
host    molly       molly       ::1/128               md5

# "local" is for Unix domain socket connections only
local   all         all                               ident
# IPv4 local connections:
host    all         all         127.0.0.1/32          ident
# IPv6 local connections:
host    all         all         ::1/128               ident
""")
    pg_hba.close()
    
    quiet_exec(['/etc/init.d/%s' % POSTGRES_SERVICE, 'restart'])
    print "DONE!"
    print
    print "This has configured Postgres to allow the user 'molly' to connect to"
    print "the database called 'molly' from localhost only. Please call your"
    print "database and user molly in the dbcreate function."