import ldap, ldap.sasl
import os

os.environ['KRB5CCNAME'] = '/tmp/krb5cc_mp'

def get_common_name(username):
    auth = ldap.sasl.gssapi("")
    oakldap = ldap.initialize("ldap://ldap.oak.ox.ac.uk:389")
    oakldap.start_tls_s()
    oakldap.sasl_interactive_bind_s("",auth)
    results = oakldap.search_s( "ou=people,dc=oak,dc=ox,dc=ac,dc=uk",
                         ldap.SCOPE_SUBTREE,
                         "oakPrincipal=krbPrincipalName=%s@OX.AC.UK,cn=OX.AC.UK,cn=KerberosRealms,dc=oak,dc=ox,dc=ac,dc=uk" % username)
                         
    return results[0][1]['cn'][0]
