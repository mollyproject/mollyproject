from django.http import Http404, HttpResponse
from django.template import loader, TemplateDoesNotExist, RequestContext
from django.shortcuts import render_to_response

from molly.utils.views import BaseView
from molly.utils.breadcrumbs import NullBreadcrumb

from molly.apps.home.models import BlogArticle

class IndexView(BaseView):
    def get_metadata(cls, request, page):
        return {
            'exclude_from_search': True
        }

    breadcrumb = NullBreadcrumb

    def handle_GET(cls, request, context, page):
        page = page or 'about'
        
        try:
            if page in ('base', 'container'):
                raise TemplateDoesNotExist
            template = loader.get_template('desktop/%s.html' % page)
        except TemplateDoesNotExist, e:
            raise Http404

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
            return render_to_response('desktop/container.html', {
                'content': content,
                'page': page,
            }, context_instance=RequestContext(request))
