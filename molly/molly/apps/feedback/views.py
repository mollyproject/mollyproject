import urllib

from django.conf import settings
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

from molly.utils.views import BaseView
from molly.utils.breadcrumbs import BreadcrumbFactory, Breadcrumb, lazy_reverse
from molly.utils.email import send_email

from forms import FeedbackForm

class IndexView(BaseView):
    @BreadcrumbFactory
    def breadcrumb(cls, request, context):
        return Breadcrumb(
            cls.conf.local_name, None, 'Feedback',
            lazy_reverse('index')
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
            # Send an e-mail to the managers notifying of feedback.
            email = send_email(request, {
                'email': form.cleaned_data['email'],
                'referer': request.POST.get('referer', ''),
                'body': form.cleaned_data['body'],
            }, 'feedback/email.txt', cls)

            qs = urllib.urlencode({
                'sent':'true',
                'referer': request.POST.get('referer', ''),
            })

            return HttpResponseRedirect('%s?%s' % (reverse('feedback:index'), qs))

        else:
            return cls.handle_GET(request, context)
