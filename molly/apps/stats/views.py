from django.http import HttpResponseForbidden
from django.db.models import Avg, Count

from molly.utils.breadcrumbs import lazy_reverse, Breadcrumb, BreadcrumbFactory
from molly.utils.views import BaseView
from molly.apps.stats.models import Hit

LIST_LIMIT = 50

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
            return HttpResponseForbidden()
        
        context = {
            'slow_pages': Hit.objects.filter(response_time__isnull=False).values('full_path').annotate(average_response=Avg('response_time'), count=Count('full_path')).order_by('average_response').reverse()[:LIST_LIMIT]
        }
        
        return self.render(request, context, 'stats/slow_pages')

class PopularPagesView(BaseView):
    """
    Lists most popular pages
    """
    
    @BreadcrumbFactory
    def breadcrumb(self, request, context):
        return Breadcrumb(
            self.conf.local_name,
            None,
            'Popular Pages',
            lazy_reverse('popular-pages'),
        )
    
    def handle_GET(self, request, context):
        
        if not request.user.has_perm('stats.can_view'):
            return HttpResponseForbidden()
        
        context = {
            'title': 'Most Popular Pages',
            'pages': Hit.objects.values('full_path').annotate(count=Count('full_path')).order_by('count').reverse()[:LIST_LIMIT]
        }
        
        return self.render(request, context, 'stats/popular_pages')

class Popular404sView(BaseView):
    """
    Lists most popular 404s
    """
    
    @BreadcrumbFactory
    def breadcrumb(self, request, context):
        return Breadcrumb(
            self.conf.local_name,
            None,
            'Popular 404s',
            lazy_reverse('popular-404s'),
        )
    
    def handle_GET(self, request, context):
        
        if not request.user.has_perm('stats.can_view'):
            return HttpResponseForbidden()
        
        context = {
            'title': 'Most Popular 404s',
            'pages': Hit.objects.filter(status_code='404').values('full_path').annotate(count=Count('full_path')).order_by('count').reverse()[:LIST_LIMIT]
        }
        
        return self.render(request, context, 'stats/popular_pages')

class PopularDevicesView(BaseView):
    """
    Lists most popular devices
    """
    
    @BreadcrumbFactory
    def breadcrumb(self, request, context):
        return Breadcrumb(
            self.conf.local_name,
            None,
            'Popular Devices',
            lazy_reverse('popular-devices'),
        )
    
    def handle_GET(self, request, context):
        
        if not request.user.has_perm('stats.can_view'):
            return HttpResponseForbidden()
        
        context = {
            'devices': Hit.objects.values('device_id').annotate(count=Count('device_id')).order_by('count').reverse()[:LIST_LIMIT]
        }
        
        return self.render(request, context, 'stats/popular_devices')

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
            return HttpResponseForbidden()
        
        return self.render(request, context, 'stats/index')