import simplejson, hashlib, urllib2
from django.http import HttpResponse
from django.core.paginator import Paginator

from molly.utils.renderers import mobile_render
from molly.utils.views import BaseView
from molly.utils.breadcrumbs import *

from .forms import GenericContactForm

class IndexView(BaseView):
    @BreadcrumbFactory
    def breadcrumb(cls, request, context):
        return Breadcrumb(
            'contact',
            None,
            'Contact search',
            lazy_reverse('contact:index'),
        )

    def initial_context(cls, request):
        return {
            'form': cls.conf.provider.form(request.GET or None),
            'medium_choices': cls.conf.provider.medium_choices,
        }

    def handle_GET(cls, request, context):
        return mobile_render(request, context, 'contact/index')

class ResultListView(IndexView):

    @BreadcrumbFactory
    def breadcrumb(cls, request, context):
        return Breadcrumb(
            'contact',
            None,
            'Contact search',
            lazy_reverse('contact:index'),
        )

    def handle_GET(cls, request, context):
        provider = cls.conf.provider

        form = provider.form(request.GET or None)
        medium = request.GET.get('medium', provider.medium_choices[0][0])

        if form.is_valid() and medium in [m[0] for m in provider.medium_choices]:

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
                return cls.handle_error(
                    request, context,
                    'There are no results for this page.',
                )
            page = paginator.page(page) 

            context.update({
                'page': page,
                'paginator': paginator,
                'medium': medium,
            })

        if 'format' in request.GET and request.GET['format'] == 'json':
            json = simplejson.dumps(context)
            response = HttpResponse(
                json,
                mimetype='application/json'
            )
    #        response['X-JSON'] = json
            response['ETag'] = hashlib.sha224(json).hexdigest()
            return response
        else:
            context['form'] = form
            return mobile_render(request, context, 'contact/result_list')

    def handle_error(cls, request, context, message):
        context.update({
            'message': message,
        })

        return mobile_render(request, context, 'contact/result_list')


class ResultDetailView(BaseView):
    @BreadcrumbFactory
    def breadcrumb(cls, request, context):
        return Breadcrumb(
            'contact',
            None,
            'Contact search',
            lazy_reverse('contact:index'),
        )


    def handle_GET(cls, request, context, id):
        try:
            context['result'] = cls.conf.provider.fetch_result(id)
        except BaseContactProvider.NoSuchResult:
            raise Http404

        return mobile_render(request, context, 'context/result_detail')
