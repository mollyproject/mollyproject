import ldap, ldap.sasl
import os, re

os.environ['KRB5CCNAME'] = '/tmp/krb5cc_mp2'

def get_oakldap():
    auth = ldap.sasl.gssapi("")
    oakldap = ldap.initialize("ldap://ldap.oak.ox.ac.uk:389")
    oakldap.start_tls_s()
    oakldap.sasl_interactive_bind_s("",auth)
    return oakldap
    
def get_person_data(username):
    oakldap = get_oakldap()
    results = oakldap.search_s( "ou=people,dc=oak,dc=ox,dc=ac,dc=uk",
                         ldap.SCOPE_SUBTREE,
                         "oakPrincipal=krbPrincipalName=%s@OX.AC.UK,cn=OX.AC.UK,cn=KerberosRealms,dc=oak,dc=ox,dc=ac,dc=uk" % username)
    return results[0][1]
    
OAK_PRINCIPAL_RE = re.compile('krbPrincipalName=([a-z0-9]+)@OX.AC.UK,cn=OX.AC.UK,cn=KerberosRealms,dc=oak,dc=ox,dc=ac,dc=uk')
def get_username_by_email(email):
    oakldap = get_oakldap()
    results = oakldap.search_s( "ou=people,dc=oak,dc=ox,dc=ac,dc=uk",
                         ldap.SCOPE_SUBTREE,
                         "oakAlternativeMail=%s" % email)

    try:    
        principals = results[0][1]['oakPrincipal']
    except IndexError:
        return None
        
    for principal in principals:
        match = OAK_PRINCIPAL_RE.match(principal)
        if match:
            return match.groups(0)[0]