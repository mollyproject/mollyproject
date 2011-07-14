import urllib
from datetime import timedelta

from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _

from molly.utils.views import BaseView
from molly.utils.breadcrumbs import BreadcrumbFactory, Breadcrumb, lazy_reverse
from molly.utils import send_email

from forms import FeedbackForm

class IndexView(BaseView):

    @BreadcrumbFactory
    def breadcrumb(self, request, context):
        return Breadcrumb(
            self.conf.local_name, None, _('Feedback'),
            lazy_reverse('index'))

    def initial_context(self, request):
        return {
            'feedback_form': FeedbackForm(request.POST or None)}

    def handle_GET(self, request, context):
        context.update({
           'sent': request.GET.get('sent') == 'true',
           'feedback_referrer': request.GET.get('referer', ''),
        })
        return self.render(request, context, 'feedback/index',
                           expires=timedelta(days=365))

    def handle_POST(self, request, context):
        form = context['feedback_form']
        if form.is_valid():
            # Send an e-mail to the managers notifying of feedback.
            email = send_email(request, {
                'email': form.cleaned_data['email'],
                'referer': request.POST.get('referer', ''),
                'body': form.cleaned_data['body'],
            }, 'feedback/email.txt', self)

            qs = urllib.urlencode({
                'sent': 'true',
                'referer': request.POST.get('referer', ''),
            })

            return self.redirect('%s?%s' % (reverse('feedback:index'), qs),
                                 request)

        else:
            return self.handle_GET(request, context)
