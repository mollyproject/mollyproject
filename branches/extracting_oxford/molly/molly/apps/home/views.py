# Create your views here.
import urllib

from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.conf import settings
from django.template import loader, Context, RequestContext
from django.core.mail import EmailMessage
from django import forms

from molly.utils.views import BaseView
from molly.utils.breadcrumbs import *

from molly.wurfl import device_parents
from molly import conf

from models import UserMessage, BlogArticle
from forms import FeedbackForm, UserMessageFormSet

class IndexView(BaseView):

    @BreadcrumbFactory
    def breadcrumb(cls, request, context):
        return Breadcrumb('home', None, 'Home', lazy_reverse('home:index'))
        
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
            and not request.session.get('home:desktop_shown', False)
            and not request.GET.get('preview') == 'true'
            and not internal_referer
            and not settings.DEBUG):
            return HttpResponseRedirect(reverse('home:exposition'))
    
        applications = [{
            'application_name': app.application_name,
            'local_name': app.local_name,
            'title': app.title,
            'url': reverse('%s:index' % app.local_name),
            'display_to_user': app.conf.display_to_user,
        } for app in conf.all_apps()]
        
        context = {
            'applications': applications,
            'hide_feedback_link': True,
        }
        return cls.render(request, context, 'core/index')
    
    def handle_POST(cls, request, context):
        no_desktop_about = {'true':True, 'false':False}.get(request.POST.get('no_desktop_about'))
        if not no_desktop_about is None:
            request.session['home:desktop_about_shown'] = no_desktop_about
            
        return HttpResponseRedirect(reverse('home:index'))

class StaticDetailView(BaseView):
    @BreadcrumbFactory
    def breadcrumb(cls, request, context, title, template):
        return Breadcrumb(
            'home', None, title,
            lazy_reverse('home:static', args=[template])
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
            'home', None, 'Feedback',
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
       
            return HttpResponseRedirect('%s?%s' % (reverse('home:feedback'), qs))
            
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
            'home', None, 'View messages from the developers',
            lazy_reverse('home:messages')
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
            
        return HttpResponseRedirect(reverse('home:messages'))

