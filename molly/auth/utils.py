from django.contrib.auth.models import User

from molly.conf import app_by_application_name
from .models import UserIdentifier, UserSession, ExternalServiceToken


def unify_users(request):
    user = request.user
    conf = app_by_application_name('molly.auth')

    users = set()
    for identifier in user.useridentifier_set.all():
        if not identifier.namespace in conf.unify_identifiers:
            continue

        identifiers = UserIdentifier.objects.filter(namespace=identifier.namespace, value=identifier.value)

        users |= set(i.user for i in identifiers)

    token_namespaces = set(t.namespace for t in user.externalservicetoken_set.all())
    identifier_namespaces = set(i.namespace for i in user.useridentifier_set.all())

    root_user = min(users, key=lambda u:u.date_joined)

    for u in users:

        u.usersession_set.all().update(user=root_user)

        for token in u.externalservicetoken_set.all():
            if u != user and token.namespace in token_namespaces:
                token.delete()
            else:
                token.user = root_user
                token.save()

        for identifier in u.useridentifier_set.all():
            if u != user and identifier.namespace in identifier_namespaces:
                identifier.delete()
            else:
                identifier.user = root_user
                identifier.save()

        if u != root_user:
            u.delete()
