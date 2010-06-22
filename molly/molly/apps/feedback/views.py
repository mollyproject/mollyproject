import urllib

from django.core.mail import EmailMessage
from django.conf import settings
from django.template import loader, Context
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

from molly.utils.views import BaseView
from molly.utils.breadcrumbs import BreadcrumbFactory, Breadcrumb, lazy_reverse

from forms import FeedbackForm

class IndexView(BaseView):
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
        return cls.render(request, context, 'feedback/index')

    def handle_POST(cls, request, context):
        if context['feedback_form'].is_valid():
            email = cls.get_email(request, context)
            email.send()

            qs = urllib.urlencode({
                'sent':'true',
                'referer': request.POST.get('referer', ''),
            })

            return HttpResponseRedirect('%s?%s' % (reverse('feedback:index'), qs))

        else:
            return cls.handle_GET(request, context)

    def get_email(cls, request, context):
        form = context['feedback_form']
        email_context = Context({
            'email': form.cleaned_data['email'],
            'devid': request.device.devid,
            'ua': request.META['HTTP_USER_AGENT'],
            'referer': request.POST.get('referer', ''),
            'lon': request.session.get('geolocation:location', (None, None))[0],
            'lat': request.session.get('geolocation:location', (None, None))[1],
            'body': form.cleaned_data['body'],
            'session_key': request.session.session_key,
        })
        
        template = loader.get_template('feedback/email.txt')
        email = template.render(email_context)
        
        headers = {}
        headers_section, body = email.split('\n\n', 1)
        for header in headers_section.split('\n'):
            key, value = header.split(': ', 1)
            headers[key] = value
        
        subject = headers.pop('Subject')
        if 'From' in headers:
            from_email = headers.pop('From')
        elif hasattr(cls.conf, 'from_email'):
            from_email = cls.conf.from_email
        else:
            from_email = settings.DEFAULT_FROM_EMAIL
        if hasattr(cls.conf, 'to_email'):
            to_email = cls.conf.to_email
        else:
            to_email = ('%s <%s>' % admin for admin in settings.MANAGERS)
            
        print (
            subject,
            body,
            from_email,
            to_email,
            headers,
        )
        
        email = EmailMessage(
            subject = subject,
            body = body,
            from_email = from_email,
            to = to_email,
            headers = headers,
        )
        
        return email