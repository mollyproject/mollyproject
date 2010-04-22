# Create your views here.
from datetime import datetime, timedelta
import pytz, simplejson, urllib, random

from django.http import HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect, Http404
from django.core.urlresolvers import reverse, resolve
from django.shortcuts import get_object_or_404, render_to_response
from django.conf import settings
from django.core.management import call_command
from django.template import loader, Context, RequestContext
from django.core.mail import EmailMessage
from django import forms

from molly.utils.views import BaseView
from molly.utils.breadcrumbs import *

from molly.osm.utils import fit_to_map
from molly.wurfl import device_parents
from molly import conf

from models import ExternalImageSized, UserMessage, ShortenedURL, BlogArticle
from forms import FeedbackForm, UserMessageFormSet

class IndexView(BaseView):

    @BreadcrumbFactory
    def breadcrumb(cls, request, context):
        return Breadcrumb('core', None, 'Home', lazy_reverse('core:index'))
        
    def handle_GET(cls, request, context):
        # Check whether the referer header is from the same host as the server
        # is responding as
        try:
            internal_referer = request.META.get('HTTP_REFERER', '').split('/')[2] == request.META.get('HTTP_HOST')
        except IndexError:
            internal_referer = False
    
        # Redirects if the user is a desktop browser who hasn't been referred
        # from this site. Also extra checks for preview mode and DEBUG.
        if ("generic_web_browser" in device_parents[request.device.devid]
            and not request.session.get('core:desktop_shown', False)
            and not request.GET.get('preview') == 'true'
            and not internal_referer
            and not settings.DEBUG):
            return HttpResponseRedirect(reverse('core:exposition'))
    
        applications = [{
            'application_name': app.application_name,
            'local_name': app.local_name,
            'title': app.title,
            'url': reverse('%s:index' % app.local_name),
            'display_to_user': app.conf.display_to_user,
        } for app in conf.applications.values()]
        
        context = {
            'applications': applications,
            'hide_feedback_link': True,
        }
        return cls.render(request, context, 'core/index')
    
    def handle_POST(cls, request, context):
        no_desktop_about = {'true':True, 'false':False}.get(request.POST.get('no_desktop_about'))
        if not no_desktop_about is None:
            request.session['core:desktop_about_shown'] = no_desktop_about
            
        return HttpResponseRedirect(reverse('core:index'))

class ExternalImageView(BaseView):

    breadcrumb = NullBreadcrumb

    def handle_GET(cls, request, context, slug):
        eis = get_object_or_404(ExternalImageSized, slug=slug)
        response = HttpResponse(open(eis.get_filename(), 'r').read(), mimetype='image/jpeg')
        last_updated = pytz.utc.localize(eis.external_image.last_updated)
    
        response['ETag'] = slug
        return response

class StaticDetailView(BaseView):
    @BreadcrumbFactory
    def breadcrumb(cls, request, context, title, template):
        return Breadcrumb(
            'core', None, title,
            lazy_reverse('core:static', args=[template])
        )
    
    def handle_GET(cls, request, context, title, template):
        t = loader.get_template('static/%s.xhtml' % template)
    
        context.update({
            'title': title,
            'content': t.render(Context()),
        })
        return cls.render(request, context, 'core/static_detail')

class ExpositionView(BaseView):
    def get_metadata(cls, request, page):
        return {
            'exclude_from_search': True
        }
    
    breadcrumb = NullBreadcrumb
    cache_page_duration = 60*15
    
    def handle_GET(cls, request, context, page):
        page = page or 'about'
        template = loader.get_template('core/exposition/%s.xhtml' % page)
        
        if page == 'blog':
            inner_context = {
                'articles': BlogArticle.objects.all(),
            }
        else:
            inner_context = {}
        
        content = template.render(RequestContext(request, inner_context))
        
        if request.GET.get('ajax') == 'true':
            return HttpResponse(content)
        else:
            return render_to_response('core/exposition/container.xhtml', {
                'content': content,
                'page': page,
            }, context_instance=RequestContext(request))    

def handler500(request):
    context = {
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

class FeedbackView(BaseView):
    @BreadcrumbFactory
    def breadcrumb(cls, request, context):
        return Breadcrumb(
            'core', None, 'Feedback',
            lazy_reverse('feedback')
        )
        
    def initial_context(cls, request):
        return {
            'feedback_form': FeedbackForm(request.POST or None)
        }
        
    def handle_GET(cls, request, context):
        context.update({
           'sent': request.GET.get('sent') == 'true',
           'referer': request.GET.get('referer', ''),
        })
        return cls.render(request, context, 'core/feedback')
        
    def handle_POST(cls, request, context):
        if context['feedback_form'].is_valid():
            email = EmailMessage(
                'm.ox | Comment',
                cls.get_email_body(request, context), None,
                ('%s <%s>' % admin for admin in settings.ADMINS),
                [], None, [],
                {'Reply-To': context['feedback_form'].cleaned_data['email']},
            )
            email.send()
            
            qs = urllib.urlencode({
                'sent':'true',
                'referer': request.POST.get('referer', ''),
            })
       
            return HttpResponseRedirect('%s?%s' % (reverse('core:feedback'), qs))
            
        else:
            return cls.handle_GET(request, context)
            
    def get_email_body(cls, request, context):
        form = context['feedback_form']
        params = {
            'email': form.cleaned_data['email'],
            'devid': request.device.devid,
            'ua': urllib.urlencode({'user_agent':request.META['HTTP_USER_AGENT']}),
            'referer': request.POST.get('referer', ''),
            'lat': request.session.get('geolocation:location', (None, None))[0],
            'lon': request.session.get('geolocation:location', (None, None))[1],
            'body': form.cleaned_data['body'],
            'session_key': request.session.session_key,
        }
        body = """\
Meta
====

E-mail:      %(email)s
Device:      http://www.wurflpro.com/device/results?user_agent=&identifier=%(devid)s
User-agent:  http://www.wurflpro.com/device/results?%(ua)s
Referer:     %(referer)s
Location:    http://www.google.co.uk/search?q=%(lat)f,%(lon)f
Session key: %(session_key)s

Message
=======

%(body)s
""" % params

        return body
    
class UserMessageView(BaseView):
    @BreadcrumbFactory
    def breadcrumb(cls, request, context):
        return Breadcrumb(
            'core', None, 'View messages from the developers',
            lazy_reverse('core:messages')
        )
        
    def initial_context(cls, request):
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

    def handle_GET(cls, request, context):
        UserMessage.objects.filter(session_key=request.session.session_key).update(read=True)
        return cls.render(request, context, 'core/messages')
        
    def handle_POST(cls, request, context):
        if context['formset'].is_valid():
            context['formset'].save()
            
        return HttpResponseRedirect(reverse('core:messages'))

class ShortenedURLRedirectView(BaseView):
    breadcrumb = NullBreadcrumb

    def handle_GET(cls, request, context, slug):
        shortened_url = get_object_or_404(ShortenedURL, slug=slug)
        return HttpResponsePermanentRedirect(shortened_url.path)

class ShortenURLView(BaseView):
    # We'll omit characters that look similar to one another
    AVAILABLE_CHARS = '23456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghkmnpqrstuvwxyz'
    
    def initial_context(cls, request):
        try:
            path = request.GET['path']
            view, view_args, view_kwargs = resolve(path.split('?')[0])
            if getattr(view, 'simple_shorten_breadcrumb', False):
                view_context = None
            else:
                view_context = view.initial_context(request, *view_args, **view_kwargs)
            
        except (KeyError, ):
            raise Http404
            
        return {
            'path': path,
            'view': view,
            'view_args': view_args,
            'view_kwargs': view_kwargs,
            'view_context': view_context,
            'complex_shorten': ('?' in path) or view_context is None or view_context.get('complex_shorten', False),
        }

    def breadcrumb_render(cls, request, context):
        view, view_context = context['view'], context['view_context']
        view_args, view_kwargs = context['view_args'], context['view_kwargs']
        
        if view_context:
            breadcrumb = view.breadcrumb.render(view, request, view_context, *view_args, **view_kwargs)
            return (
                breadcrumb[0],
                breadcrumb[1],
                (breadcrumb[4], context['path']),
                breadcrumb[1] == (breadcrumb[4], context['path']),
                'Shorten link',
            )
        else:
            index = resolve(reverse('%s_index' % view.app_name))[0].breadcrumb(request, context)
            index = index.title, index.url()
            return (
                view.app_name,
                index,
                (u'Back\u2026', context['path']),
                False,
                'Shorten link',
            )

    # Create a 'blank' object to attach our render method to by constructing
    # a class and then calling its constructor. It's a bit messy, and probably
    # points at a need to refactor breadcrumbs so that view.breadcrumb returns
    # the five-tuple passed to the template as opposed to
    # view.breadcrumb.render. 
    breadcrumb = type('bc', (object,), {})()
    breadcrumb.render = breadcrumb_render

            
    def handle_GET(cls, request, context):
        print context['complex_shorten']
        try:
            path = request.GET['path']
        except (KeyError):
            return cls.invalid_path(request, context)

        context['shortened_url'], created = ShortenedURL.objects.get_or_create(path=path)
        
        if created:
            if context['complex_shorten']:
                slug = '0'+''.join(random.choice(cls.AVAILABLE_CHARS) for i in range(5))
            else:
                slug = unicode(context['shortened_url'].id)
            context['shortened_url'].slug = slug
            context['shortened_url'].save()

        return cls.render(request, context, 'core/shorten_url')
