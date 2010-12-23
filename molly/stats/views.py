from django.http import HttpResponseForbidden
from django.db.models import Avg

from molly.utils.breadcrumbs import lazy_reverse, Breadcrumb, BreadcrumbFactory
from molly.utils.views import BaseView
from molly.stats.models import Hit

class SlowPagesView(BaseView):
    """
    Lists pages which take a long time to generate, on average, over the past week
    """
    
    @BreadcrumbFactory
    def breadcrumb(self, request, context):
        return Breadcrumb(
            self.conf.local_name,
            None,
            'Slow Pages',
            lazy_reverse('slow-pages'),
        )
    
    def handle_GET(self, request, context):
        
        if not request.user.has_perm('stats.can_view'):
            raise HttpResponseForbidden
        
        context = {
        #    'slow_pages': Hit.objects.values('full_path').annotate(average_response=Avg('response_time')).order_by('average_response').reverse()[:20]
            'slow_pages': Hit.objects.filter(response_time__isnull=False).values('full_path').annotate(average_response=Avg('response_time')).order_by('average_response').reverse()[:20]
        }
        
        print context['slow_pages']
        
        return self.render(request, context, 'stats/slow_pages')

class IndexView(BaseView):
    
    @BreadcrumbFactory
    def breadcrumb(self, request, context):
        return Breadcrumb(
            self.conf.local_name,
            None,
            'Stats',
            lazy_reverse('index'),
        )
    
    def handle_GET(self, request, context):
        
        if not request.user.has_perm('stats.can_view'):
            raise HttpResponseForbidden
        
        return self.render(request, context, 'stats/index')