import urllib2, re
from django.contrib.auth.models import User
from models import Profile
from ldap_queries import get_person_data, get_username_by_email

class AnyMethodRequest(urllib2.Request):
    def __init__(self, url, data=None, headers={}, origin_req_host=None, unverifiable=None, method=None):
        self.method = method and method.upper() or None
        urllib2.Request.__init__(self, url, data, headers, origin_req_host, unverifiable)

    def get_method(self):
        if not self.method is None:
            return self.method
        elif self.has_data():
            return "POST"
        else:
            return "GET"

def update_user_from_ldap(user):
    profile = user.get_profile()

    person_data = get_person_data(profile.webauth_username)
    profile.display_name = person_data['displayName'][0]
    profile.save()
    user.first_name = person_data['givenName'][0]
    user.last_name = person_data['sn'][0]
    user.email = person_data['mail'][0]
    user.save()

def create_user_from_username(username):
    user = User.objects.create_user('sso_%s' % username, '')
    profile = Profile.objects.create(user = user, webauth_username=username)
    update_user_from_ldap(user)
    return user

def create_user_from_email(email):
    pass

OXFORD_EMAIL_RE = re.compile(r".+@([a-z\-]+\.ox\.ac\.uk|oup\.com)")
def find_or_create_user_by_email(email, create_external_user=True):
    if OXFORD_EMAIL_RE.match(email):
        username = get_username_by_email(email)
        if not username:
            raise ValueError
        try:
            profile = Profile.objects.get(webauth_username=username)
            return profile.user
        except Profile.DoesNotExist:
            user = create_user_from_username(username)
            return user
    else:
        try:
            user = User.objects.get(email=email)
            return user
        except User.DoesNotExist:
            if create_external_user:
                user = create_user_from_email(email)
                return user
            else:
                raise ValueError