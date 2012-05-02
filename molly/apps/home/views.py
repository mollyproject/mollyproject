from datetime import datetime, timedelta

from django.http import HttpResponse
from django.core.urlresolvers import reverse
from django.conf import settings
from django.template import loader, Context, RequestContext
from django import forms
from django.shortcuts import render_to_response
from django.utils.translation import ugettext as _

from molly.utils.views import BaseView
from molly.utils.breadcrumbs import *
from molly.favourites import get_favourites
from molly.wurfl import device_parents
from molly.conf.applications import app_by_application_name, has_app_by_application_name, has_app, all_apps
from molly.apps.weather.models import Weather

from models import UserMessage
from forms import UserMessageFormSet

class IndexView(BaseView):
    """
    Renders the portal home page
    """

    @BreadcrumbFactory
    def breadcrumb(self, request, context):
        return Breadcrumb(self.conf.local_name,
                          None,
                          _('Home'),
                          lazy_reverse('index'))

    def handle_GET(self, request, context):
        # Check whether the referer header is from the same host as the server
        # is responding as
        try:
            referer_host = request.META.get('HTTP_REFERER', '').split('/')[2]
            internal_referer = referer_host == request.META.get('HTTP_HOST')
        except IndexError:
            internal_referer = False

        # Redirects if the user is a desktop browser who hasn't been referred
        # from this site. Also extra checks for preview mode and DEBUG.
        if ("generic_web_browser" in device_parents[request.device.devid]
            and not request.session.get('home:desktop_shown', False)
            and not request.GET.get('preview') == 'true'
            and not internal_referer
            and not settings.DEBUG
            and has_app('molly.apps.desktop')
            and request.REQUEST.get('format') is None):
            return self.redirect(reverse('desktop:index'), request)
        
        messages = []
        # Add any one-off messages to be shown to this user
        if UserMessage.objects.filter(
                read=False, session_key=request.session.session_key).count():
            messages.append({
                'url': reverse('home:messages'),
                'body': _('You have a message from the developers')
            })
        
        # Warn users who use Opera devices
        if not request.session.get('home:opera_mini_warning', False) \
          and request.browser.mobile_browser == u'Opera Mini':
            messages.append(
                { 'body': _("""Please note that the "Mobile View" on Opera Mini does not display this site correctly. To ensure correct operation of this site, ensure "Mobile View" is set to Off in Opera settings""") })
            request.session['home:opera_mini_warning'] = True
        
        if has_app_by_application_name('molly.apps.weather'):
            weather_id = app_by_application_name('molly.apps.weather').location_id
            try:
                weather = Weather.objects.get(ptype='o', location_id=weather_id)
            except Weather.DoesNotExist:
                weather = None
        else:
            weather = None
        
        applications = [{
            'application_name': app.application_name,
            'local_name': app.local_name,
            'title': app.title,
            'url': reverse('%s:index' % app.local_name) \
                    if app.has_urlconf else None,
            'display_to_user': app.display_to_user,
        } for app in all_apps()]

        # Add accesskeys to the first 9 apps to be displayed to the user
        for i, app in enumerate(
                [app for app in applications if app['display_to_user']][:9]
            ):
            app['accesskey'] = i + 1

        context = {
            'applications': applications,
            'hide_feedback_link': True,
            'messages': messages,
            'favourites': get_favourites(request),
            'weather': weather,
        }
        return self.render(request, context, 'home/index',
                           expires=timedelta(minutes=10))

    def get_metadata(self, request):
        return {
            'exclude_from_search': True,
        }

    def handle_POST(self, request, context):
        no_desktop_about = request.POST.get('no_desktop_about')
        if no_desktop_about  == 'true':
            request.session['home:desktop_about_shown'] = True
        elif no_desktop_about  == 'false':
            request.session['home:desktop_about_shown'] = False

        return self.redirect(reverse('home:index'), request)

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
        return self.render(request, context, 'home/static_detail',
                           expires=timedelta(days=365))

class UserMessageView(BaseView):
    @BreadcrumbFactory
    def breadcrumb(self, request, context):
        return Breadcrumb(
            self.conf.local_name, None, _('View messages from the developers'),
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
        messages = UserMessage.objects.filter(
                session_key=request.session.session_key
            )
        messages.update(read=True)
        return self.render(request, context, 'home/messages')

    def handle_POST(self, request, context):
        if context['formset'].is_valid():
            context['formset'].save()

        return self.redirect(reverse('home:messages'), request)
