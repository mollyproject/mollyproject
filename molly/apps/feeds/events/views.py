from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _

from molly.utils.views import BaseView
from molly.utils.breadcrumbs import *

from ..models import Feed, Item

class IndexView(BaseView):
    def get_metadata(self, request):
        return {
            'title': _('Events'),
            'additional': _('View events from across the University.'),
        }

    @BreadcrumbFactory
    def breadcrumb(self, request, context):
        return Breadcrumb(
            self.conf.local_name, None, _('Events'), lazy_reverse('events:index')
        )

    def handle_GET(self, request, context):
        feeds = Feed.events.all()
        context['feeds'] = feeds
        return self.render(request, context, 'feeds/events/index',
                           expires=timedelta(days=7))

class ItemListView(BaseView):
    def get_metadata(self, request, slug):
        feed = get_object_or_404(Feed.events, slug=slug)

        # Translators: Feed last modified [date format] otherwise _('never_updated')
        last_modified = feed.last_modified.strftime('%a, %d %b %Y') if feed.last_modified else _('never updated')
        return {
            'last_modified': feed.last_modified,
            'title': feed.title,
            'additional': '<strong>Events feed</strong>, %s' % last_modified,
        }

    @BreadcrumbFactory
    def breadcrumb(self, request, context, slug):
        return Breadcrumb(
            self.conf.local_name,
            lazy_parent('index'),
            _('News feed'),
            lazy_reverse('item-list', args=[slug])
        )

    def handle_GET(self, request, context, slug):
        feed = get_object_or_404(Feed.events, slug=slug)
        context['feed'] = feed
        return self.render(request, context, 'feeds/events/item_list')

class ItemDetailView(BaseView):
    def get_metadata(self, request, slug, id):
        item = get_object_or_404(Item, feed__slug=slug, id=id)

        last_modified = item.last_modified.strftime('%a, %d %b %Y') if item.last_modified else _('never updated')
        return {
            'last_modified': item.last_modified,
            'title': item.title,
            'feed_title': escape(item.feed.title),
        }

    @BreadcrumbFactory
    def breadcrumb(self, request, context, slug, id):
        return Breadcrumb(
            self.conf.local_name,
            lazy_parent('item-list', slug=slug),
            _('Events item'),
            lazy_reverse('item-detail', args=[slug,id])
        )

    def handle_GET(self, request, context, slug, id):
        item = get_object_or_404(Item, feed__slug=slug, id=id)
        context.update({
            'item': item,
            'description': item.get_description_display(request.device)
        })
        return self.render(request, context, 'feeds/events/item_detail')
