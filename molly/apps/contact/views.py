import simplejson
import hashlib
import urllib2

from django.http import HttpResponse
from django.core.paginator import Paginator

from molly.utils.views import BaseView
from molly.utils.breadcrumbs import *

from .forms import GenericContactForm


class IndexView(BaseView):

    @BreadcrumbFactory
    def breadcrumb(self, request, context):
        return Breadcrumb(
            self.conf.local_name,
            None,
            'Contact search',
            lazy_reverse('index'),
        )

    def initial_context(self, request):
        return {
            'form': self.conf.provider.form(request.GET or None),
            'medium_choices': self.conf.provider.medium_choices,
        }

    def handle_GET(self, request, context):
        return self.render(request, context, 'contact/index')


class ResultListView(IndexView):

    @BreadcrumbFactory
    def breadcrumb(self, request, context):
        return Breadcrumb(
            self.conf.local_name,
            None,
            'Contact search',
            lazy_reverse('result_list'),
        )

    def handle_GET(self, request, context):
        provider = self.conf.provider

        form = provider.form(request.GET or None)
        medium = request.GET.get('medium')
        if not medium in [m[0] for m in provider.medium_choices]:
            medium = provider.medium_choices[0][0]

        if form.is_valid():

            try:
                page = int(request.GET.get('page', '1'))
            except ValueError:
                page = 1

            query = provider.normalize_query(form.cleaned_data, medium)

            if provider.handles_pagination:
                paginator = provider.perform_query(page=page, **query)
            else:
                people = provider.perform_query(**query)
                paginator = Paginator(people, 10)

            if not (1 <= page <= paginator.num_pages):
                return self.handle_error(
                    request, context,
                    'There are no results for this page.',
                )
            page = paginator.page(page)

            context.update({
                'page': page,
                'results': paginator,
                'medium': medium,
            })

        context['form'] = form
        return self.render(request, context, 'contact/result_list')

    def handle_error(self, request, context, message):
        context.update({
            'message': message,
        })

        return self.render(request, context, 'contact/result_list')


class ResultDetailView(BaseView):

    @BreadcrumbFactory
    def breadcrumb(self, request, context):
        return Breadcrumb(
            self.conf.local_name,
            None,
            'Contact search',
            lazy_reverse('result_detail'),
        )

    def handle_GET(self, request, context, id):
        try:
            context['result'] = self.conf.provider.fetch_result(id)
        except BaseContactProvider.NoSuchResult:
            raise Http404

        return self.render(request, context, 'context/result_detail')
