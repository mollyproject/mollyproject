from datetime import timedelta
from xml.sax.saxutils import escape

from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _
from django.utils.translation import get_language
from django.db.models import Q

from molly.utils.views import BaseView
from molly.utils.breadcrumbs import *

from ..models import Feed, Item

class IndexView(BaseView):
    def get_metadata(self, request):
        return {
            'title': _('News'),
            'additional': _('View news from across the University.'),
        }
        
    @BreadcrumbFactory
    def breadcrumb(self, request, context):
        return Breadcrumb(
            self.conf.local_name, None, _('News'), lazy_reverse('index')
        )
        
    def handle_GET(self, request, context):
        feeds = Feed.news.all()
        
        # Only actually care about showing feeds in the right language, not
        # dialect, so only match on before the -
        lang_code = get_language()
        if '-' in lang_code:
            lang_code = lang_code.split('-')[0]
        
        
        all_feeds = feeds.count()
        if 'all' not in request.GET:
            feeds = feeds.filter(
                Q(language__startswith=lang_code) | Q(language=None)
            )
        lang_feeds = feeds.count()
        
        context= {
            'feeds': feeds,
            'more_in_all': lang_feeds != all_feeds,
        }
        return self.render(request, context, 'feeds/news/index',
                           expires=timedelta(days=7))

class ItemListView(BaseView):
    def get_metadata(self, request, slug):
        feed = get_object_or_404(Feed.news, slug=slug)
        
        last_modified = feed.last_modified.strftime('%a, %d %b %Y') if feed.last_modified else _('never updated')
        return {
            'last_modified': feed.last_modified,
            'title': feed.title,
            'additional': '<strong>News feed</strong>, %s' % last_modified,
        }

    @BreadcrumbFactory
    def breadcrumb(self, request, context, slug):
        return Breadcrumb(
            self.conf.local_name,
            lazy_parent('index'),
            'News feed',
            lazy_reverse('item-list', args=[slug])
        )
        
    def handle_GET(self, request, context, slug):
        feed = get_object_or_404(Feed.news, slug=slug)
        context['feed'] = feed
        context['feed_items'] = feed.item_set.all()
        return self.render(request, context, 'feeds/news/item_list')

class ItemDetailView(BaseView):
    def get_metadata(self, request, slug, id):
        item = get_object_or_404(Item, feed__slug=slug, id=id)
        
        last_modified = item.last_modified.strftime('%a, %d %b %Y') if item.last_modified else 'never updated'
        return {
            'last_modified': item.last_modified,
            'title': item.title,
            'additional': '<strong>News item</strong>, %s, %s' % (escape(item.feed.title), last_modified),
        }

    @BreadcrumbFactory
    def breadcrumb(self, request, context, slug, id):
        return Breadcrumb(
            self.conf.local_name,
            lazy_parent('item-list', slug=slug),
            'News item',
            lazy_reverse('item-detail', args=[slug,id])
        )
        
    def handle_GET(self, request, context, slug, id):
        item = get_object_or_404(Item, feed__slug=slug, id=id)
        context.update({
            'item': item,
            'description': item.get_description_display(request.device)
        })
        return self.render(request, context, 'feeds/news/item_detail')
