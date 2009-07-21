from django.shortcuts import get_object_or_404
from django.template import RequestContext
from django.contrib.auth import authenticate
from django.contrib.auth import login as dologin, logout as dologout
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.forms.util import ErrorList

from mobile_portal.core.models import Profile
from mobile_portal.core.renderers import mobile_render

from utils import allow_unauth, require_unauth

@require_unauth
def login(request):
    context = {
        'username':'',
        'message':None
    }

    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                dologin(request, user)
                if request.POST.get('redirect_url', None):
                    return HttpResponseRedirect(request.POST['redirect_url'])
                else:
                    return HttpResponseRedirect(reverse("core_index"))
            else:
                message = "Sorry, your account has been disabled. Please check your e-mail for a password reset e-mail or contact a co-ordinator."
        else:
            message = "Sorry, your username and password were invalid."
        context['username'], context['message'] = username, message
        context['redirect_url'] = request.POST.get('redirect_url', '')
    else:
        context['redirect_url'] = request.GET.get('redirect_url', '')
    

    return mobile_render(request, context, "auth/login")

@require_unauth
def webauth_login(request):
    """
    This view needs to be set up in the Apache config as a Webauth target. See
    the Stanford Webauth pages for how to do this. If this isn't done, you'll
    see a KeyError exception on the first line of code in this view.
    
    It looks up the Webauth user in the WebauthUser model and logs in the
    associated user if one is found. If no user is found, then a non-binnie
    Oxford SSO person has attempted to get in and we tell them they aren't
    welcome.
    """
    
    if not 'AUTH_TYPE' in request.META:
        return HttpResponseRedirect(reverse('webauth_failure'))
    if request.META['AUTH_TYPE'] == 'WebAuth':
        webauth_username = request.META['REMOTE_USER']
        try:
            profile = Profile.objects.get(webauth_username = webauth_username)
        except Profile.DoesNotExist:
            user = User.objects.create_user('sso/%s' % webauth_username, '')
            profile = Profile.objects.create(user = user, webauth_username=webauth_username)
        r = authenticate(webauth_user=profile)
        dologin(request, profile.user)
    next_url = request.GET.get('redirect_url', reverse("core_index"))
    return HttpResponseRedirect(next_url)

def logout(request):
    context = {
        'used_webauth':request.session.get('_auth_user_backend') == 'mobile_portal.webauth.backends.WebauthBackend',
    }
    dologout(request)
    return mobile_render(request, context, "auth/logged_out")

@allow_unauth
def webauth_logout(request):
    """
    Redirects to the SSO logout page in a more elegant fashion than linking
    there directly.
    """
    
    return HttpResponseRedirect("https://webauth.ox.ac.uk/logout")

@require_unauth
def webauth_failure(request):
    """
    Displays a message to say something went wrong with Webauth and sends
    a notification to the IT Officer to let him/her know.
    """
    
    return mobile_render(request, context, "auth/webauth_failure")
