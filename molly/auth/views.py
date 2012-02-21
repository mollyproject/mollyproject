import urllib
import urllib2
import urlparse
import logging
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth import logout
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.forms.util import ErrorList
from django.utils.translation import ugettext as _

from molly.utils.views import BaseView
from molly.utils.breadcrumbs import BreadcrumbFactory, Breadcrumb, static_reverse, lazy_reverse, static_parent

from .forms import PreferencesForm, UserSessionFormSet, ExternalServiceTokenFormSet
from .models import UserSession

class SecureView(BaseView):
    """
    An 'abstract' view for all secure pages.
    
    Implements a timeout so that people will need to reauthenticate if a
    secure page hasn't been accessed recently. The SecureMidddleware checks
    for this class in a view's MRO in order to enforce an HTTPS connection.
    """

    def __call__(self, request, *args, **kwargs):
        """
        Enforces timeouts for idle sessions.
        """

        # If the SecureMiddleware hasn't redirected requests over !HTTPS
        # something has gone wrong. We ignore this for debugging purposes.
        assert settings.DEBUG_SECURE or request.is_secure()

        last_accessed = request.secure_session.get('last_accessed', datetime.now())
        timeout_period = request.secure_session.get('timeout_period', 15)
        if last_accessed < datetime.now() - timedelta(minutes=timeout_period) and getattr(self.conf, 'enforce_timeouts', True):
            return TimedOutView(request, self, *args, **kwargs)
        request.secure_session['last_accessed'] = datetime.now()

        return super(SecureView, self).__call__(request, *args, **kwargs)

class TimedOutView(BaseView):
    """
    Handles the case where a user's secure session has been inactive for too
    long.
    
    This view should not be included in a urlconf as it is referenced only by
    SecureView.
    """

    def initial_context(self, request, view, *args, **kwargs):
        return {
            'has_pin': 'pin' in request.secure_session,
        }    
    
    @BreadcrumbFactory
    def breadcrumb(self, request, context, view, *args, **kwargs):
        return Breadcrumb(
            view.conf.local_name,
            None,
            _('Session expired'),
            static_reverse(request.get_full_path()),
        )
    
    def handle_GET(self, request, context, view, *args, **kwargs):
        return self.render(request, context, 'auth/timed_out')
            
    def handle_POST(self, request, context, view, *args, **kwargs):
        if 'clear_session' in request.POST:
            for key in request.secure_session.keys():
                del request.secure_session[key]
            request.secure_session['is_secure'] = True
            return self.redirect('.', request)
        elif 'reauthenticate' in request.POST and context['has_pin']:
            valid_pin = request.POST.get('pin') == request.secure_session['pin']
            if valid_pin:
                # Reauthenticating brings the inactivity measure to zero
                request.secure_session['last_accessed'] = datetime.now()
                return self.redirect('.', request)
            else:
                context['incorrect_pin'] = True
                return self.render(request, context, 'auth/timed_out')
        else:
            return HttpResponse('', status=400)
        
class IndexView(SecureView):
    app_name = 'secure'
    
    def initial_context(self, request):
        return {
            'form': PreferencesForm(request.POST or {
                'timeout_period': request.secure_session.get('timeout_period', 15),
            }),
            'has_pin': 'pin' in request.secure_session,
            'session_key': request.secure_session.session_key,
            'user_sessions': UserSessionFormSet(request, request.POST or None),
            'external_service_tokens': ExternalServiceTokenFormSet(request, request.POST or None),
        }
        
    @BreadcrumbFactory
    def breadcrumb(self, request, context):
        return Breadcrumb(
            self.conf.local_name,
            None,
            _('Authentication preferences'),
            lazy_reverse('auth:index'),
        )
        
    def handle_GET(self, request, context):
        return self.render(request, context, 'auth/index')
    
    def handle_POST(self, request, context):
        forms = context['form'], context['user_sessions'], context['external_service_tokens']
        
        if not all(form.is_valid() for form in forms):
            return self.render(request, context, 'auth/index')
            
        if context['has_pin'] and form.cleaned_data['old_pin'] != request.secure_session['pin']:
            form.errors['old_pin'] = ErrorList(['You supplied an incorrect PIN. Please try again.'])
            return self.render(request, context, 'auth/index')

        form = context['form']
        request.secure_session['timeout_period'] = form.cleaned_data['timeout_period']
        
        if form.cleaned_data['new_pin_a']:
            if form.cleaned_data['new_pin_a'] == form.cleaned_data['new_pin_b']:
                request.secure_session['pin'] = form.cleaned_data['new_pin_a']
            else:
                form.errors['new_pin_b'] = ErrorList(['Your repeated PIN did not match.'])
                return self.render(request, context, 'auth/index')

        for form in forms:
            if hasattr(form, 'save'):
                form.save()
        
        return self.redirect('.', request)

    
class ClearSessionView(SecureView):
    
    def initial_context(self, request):
        return {
            'return_url': request.REQUEST.get('return_url', '/'),
            'suppress_clear_session_link': True,
        }
    
    @BreadcrumbFactory
    def breadcrumb(self, request, context):
        return Breadcrumb(
            self.conf.local_name,
            static_parent(context['return_url'], 'Back'),
            _('Clear session'),
            lazy_reverse('auth:clear-session'),
            
        )
     
    def handle_GET(self, request, context):
        return self.render(request, context, 'auth/clear_session')
    
    def handle_POST(self, request, context):
        UserSession.objects.filter(secure_session_key = request.secure_session.session_key).delete()
        logout(request)
        return self.redirect(context['return_url'], request)
