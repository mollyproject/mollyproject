from xml.sax.saxutils import escape
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404

from mobile_portal.core.ldap_queries import get_person_units
from mobile_portal.core.renderers import mobile_render
from mobile_portal.core.handlers import BaseView

from models import RSSFeed, RSSItem

from mobile_portal.core.breadcrumbs import Breadcrumb, BreadcrumbFactory, lazy_reverse, lazy_parent, NullBreadcrumb

class IndexView(BaseView):
    def get_metadata(cls, request):
        return {
            'title': 'News',
            'additional': 'View news feeds and events from across the University.',
        }
        
    @BreadcrumbFactory
    def breadcrumb(cls, request, context):
        return Breadcrumb(
            'rss', None, 'News', lazy_reverse('rss_index')
        )
        
    def handle_GET(cls, request, context):
        feeds = RSSFeed.objects.all()
        context = {
            'feeds': feeds,
        }
        return mobile_render(request, context, 'rss/index')

class ItemListView(BaseView):
    def get_metadata(cls, request, slug):
        feed = get_object_or_404(RSSFeed, slug=slug)
        
        return {
            'last_modified': feed.last_modified,
            'title': feed.title,
            'additional': '<strong>News feed</strong> %s' % feed.last_modified.strftime('%a, %d %b %Y'),
        }

    @BreadcrumbFactory
    def breadcrumb(cls, request, context, slug):
        return Breadcrumb(
            'rss',
            lazy_parent(IndexView),
            'News feed',
            lazy_reverse('rss_item_list', args=[slug])
        )
        
    def handle_GET(cls, request, context, slug):
        feed = get_object_or_404(RSSFeed, slug=slug)
        context['feed'] = feed
        return mobile_render(request, context, 'rss/item_list')

class ItemDetailView(BaseView):
    def get_metadata(cls, request, slug, id):
        item = get_object_or_404(RSSItem, feed__slug=slug, id=id)
        
        return {
            'last_modified': item.last_modified,
            'title': item.title,
            'additional': '<strong>News item</strong>, %s, %s' % (escape(item.feed.title), item.last_modified.strftime('%a, %d %b %Y')),
        }

    @BreadcrumbFactory
    def breadcrumb(cls, request, context, slug, id):
        return Breadcrumb(
            'rss',
            lazy_parent(ItemListView, slug=slug),
            'News item',
            lazy_reverse('rss_item_detail', args=[slug,id])
        )
        
    def handle_GET(cls, request, context, slug, id):
        item = get_object_or_404(RSSItem, feed__slug=slug, id=id)
        context.update({
            'item': item,
            'description': item.get_description_display(request.device)
        })
        return mobile_render(request, context, 'rss/item_detail')
