from datetime import datetime, timedelta

from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.conf import settings
from django.template import loader, Context, RequestContext
from django import forms
from django.shortcuts import render_to_response

from molly.utils.views import BaseView
from molly.utils.breadcrumbs import *

from molly.wurfl import device_parents
from molly import conf

from models import UserMessage
from forms import UserMessageFormSet

class IndexView(BaseView):

    @BreadcrumbFactory
    def breadcrumb(self, request, context):
        return Breadcrumb(self.conf.local_name, None, 'Home', lazy_reverse('index'))

    def handle_GET(self, request, context):
        # Check whether the referer header is from the same host as the server
        # is responding as
        try:
            internal_referer = request.META.get('HTTP_REFERER', '').split('/')[2] == request.META.get('HTTP_HOST')
        except IndexError:
            internal_referer = False

        # Redirects if the user is a desktop browser who hasn't been referred
        # from this site. Also extra checks for preview mode and DEBUG.
        if ("generic_web_browser" in device_parents[request.device.devid]
            and not request.session.get('home:desktop_shown', False)
            and not request.GET.get('preview') == 'true'
            and not internal_referer
            and not settings.DEBUG
            and conf.has_app('molly.apps.desktop')):
            return HttpResponseRedirect(reverse('desktop:index'))
        
        # Add any one-off messages to be shown to this user
        messages = []
        
        if not request.session.get('opera_mini_warning', False) and request.browser.mobile_browser == u'Opera Mini':
            messages.append('Please note that the "Mobile View" on Opera Mini does not display this site correctly. To ensure correct operation of this site, ensure "Mobile View" is set to Off in Opera settings')
            request.session['opera_mini_warning'] = True

        applications = [{
            'application_name': app.application_name,
            'local_name': app.local_name,
            'title': app.title,
            'url': reverse('%s:index' % app.local_name) if app.has_urlconf else None,
            'display_to_user': app.display_to_user,
        } for app in conf.all_apps()]

        # Add accesskeys to the first 9 apps to be displayed to the user
        for i, app in enumerate([app for app in applications if app['display_to_user']][:9]):
            app['accesskey'] = i + 1

        context = {
            'applications': applications,
            'hide_feedback_link': True,
            'is_christmas': datetime.now().month == 12,
            'messages': messages
        }
        return self.render(request, context, 'home/index', expires=timedelta(minutes=10))

    def get_metadata(self, request):
        return {
            'exclude_from_search': True,
        }

    def handle_POST(self, request, context):
        no_desktop_about = {'true':True, 'false':False}.get(request.POST.get('no_desktop_about'))
        if not no_desktop_about is None:
            request.session['home:desktop_about_shown'] = no_desktop_about

        return HttpResponseRedirect(reverse('home:index'))

class StaticDetailView(BaseView):
    @BreadcrumbFactory
    def breadcrumb(self, request, context, title, template):
        return Breadcrumb(
            self.conf.local_name, None, title,
            lazy_reverse('static', args=[template])
        )

    def handle_GET(self, request, context, title, template):
        t = loader.get_template('static/%s.html' % template)

        context.update({
            'title': title,
            'content': t.render(Context()),
        })
        return self.render(request, context, 'home/static_detail')

def handler500(request):
    context = {
        'request': request,
        'MEDIA_URL': settings.MEDIA_URL,
    }

    # This will make things prettier if we can manage it.
    # No worries if we can't.
    try:
        from molly.wurfl.context_processors import device_specific_media
        context.update(device_specific_media(request))
    except Exception, e:
        pass

    response = render_to_response('500.html', context)
    response.status_code = 500
    return response

class UserMessageView(BaseView):
    @BreadcrumbFactory
    def breadcrumb(self, request, context):
        return Breadcrumb(
            self.conf.local_name, None, 'View messages from the developers',
            lazy_reverse('messages')
        )

    def initial_context(self, request):
        try:
            formset = UserMessageFormSet(
                request.POST or None,
                queryset=UserMessage.objects.filter(
                    session_key=request.session.session_key
                )
            )
        except forms.ValidationError:
            formset = UserMessageFormSet(
                None,
                queryset=UserMessage.objects.filter(
                    session_key=request.session.session_key
                )
            )
        return {
            'formset': formset,
        }

    def handle_GET(self, request, context):
        UserMessage.objects.filter(session_key=request.session.session_key).update(read=True)
        return self.render(request, context, 'home/messages')

    def handle_POST(self, request, context):
        if context['formset'].is_valid():
            context['formset'].save()

        return HttpResponseRedirect(reverse('home:messages'))
