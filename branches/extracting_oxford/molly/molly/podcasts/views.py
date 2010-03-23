import urllib
from xml.etree import ElementTree as ET

from django.http import HttpResponseRedirect, HttpResponsePermanentRedirect, HttpResponse, Http404
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404

from molly.utils.renderers import mobile_render
from molly.utils.views import BaseView
from molly.utils.breadcrumbs import *

from molly.wurfl import device_parents

from .models import Podcast, PodcastCategory
from . import TOP_DOWNLOADS_RSS_URL


class IndexView(BaseView):
    def get_metadata(cls, request):
        return {
            'title': 'Podcasts',
            'additional': 'Browse and listen to podcasts from around the University.'
        }
        
    @BreadcrumbFactory
    def breadcrumb(cls, request, context):
        return Breadcrumb('podcasts', None,
                          'Podcasts', lazy_reverse('podcasts_index'))
        
    def handle_GET(cls, request, context):
        if request.GET.get('foo') == 'bar':
            raise AssertionError('foo')
            
        show_itunesu_link = not request.device.devid in request.preferences['podcasts']['use_itunesu']
        if 'show_itunesu_link' in request.GET:
            show_itunesu_link = request.GET['show_itunesu_link'] != 'false'
    
        #if "apple_iphone_ver1" in device_parents[request.device.devid] :
        #        return HttpResponseRedirect ("http://deimos.apple.com/WebObjects/Core.woa/Browse/ox-ac-uk-public")
        context.update({
            'categories': PodcastCategory.objects.all(),
            'show_itunesu_link': show_itunesu_link,
        })
        return mobile_render(request, context, 'podcasts/index')

class CategoryDetailView(BaseView):
    def get_metadata(cls, request, code, medium=None):
        if medium:
            raise Http404
            
        category = get_object_or_404(PodcastCategory, code=code)
        return {
            'title': category.name,
            'additional': '<strong>Podcast category</strong>'
        }
        
    def initial_context(cls, request, code, medium=None):
        category = get_object_or_404(PodcastCategory, code=code)
        podcasts = Podcast.objects.filter(category=category)
        if medium:
            podcasts = podcasts.filter(medium=medium)
    
        return {
            'category': category,
            'podcasts': podcasts,
            'medium': medium,
        }

    @BreadcrumbFactory
    def breadcrumb(cls, request, context, code, medium=None):
        if medium:
            url = lazy_reverse('podcasts_category_medium', args=[code,medium])
        else:
            url = lazy_reverse('podcasts_category', args=[code])
        
        return Breadcrumb('podcasts', lazy_parent(IndexView),
                          context['category'].name,
                          url)
        
    def handle_GET(cls, request, context, code, medium=None):
        return mobile_render(request, context, 'podcasts/category_detail')

class PodcastDetailView(BaseView):
    class RespondThus(Exception):
        def __init__(self, response):
            self.response = response
            
    def get_metadata(cls, request, identifier=None, podcast=None):
        if not podcast:
            podcast = get_object_or_404(Podcast, identifier=identifier)
        
        return {
            'title': podcast.title,
            'category': 'podcast',
            'category_display': 'podcast',
            'last_updated': podcast.last_updated,
            'additional': '<strong>Podcast</strong> %s' % podcast.last_updated.strftime('%d %b %Y')
        }
        
    def initial_context(cls, request, identifier=None, podcast=None):
        if not podcast:
            podcast = get_object_or_404(Podcast, identifier=identifier)
        return {
            'podcast': podcast,
            'category': podcast.category,
        }
    
    @BreadcrumbFactory
    def breadcrumb(cls, request, context, identifier=None, podcast=None):
        return Breadcrumb('podcasts',
                          lazy_parent(CategoryDetailView,
                                      code=context['podcast'].category.code),
                          context['podcast'].title,
                          lazy_reverse('podcasts_podcast_detail'))
        
    def handle_GET(cls, request, context, identifier=None, podcast=None):
        if 'response' in context:
            return context['response']        
        
        items = context['podcast'].podcastitem_set.order_by('order','-published_date')
        
        context.update({
            'items': items,
        })
        return mobile_render(request, context, 'podcasts/podcast_detail')

class TopDownloadsView(PodcastDetailView):
    def get_metadata(cls, request):
        podcast=Podcast.objects.get(rss_url=TOP_DOWNLOADS_RSS_URL)
        return {
            'title': podcast.title,
            'additional': '<strong>Podcast</strong>, last updated: %s' % podcast.last_updated.strftime('%a, %d %b %Y')
        }
        
    def initial_context(cls, request):
        podcast=Podcast.objects.get(rss_url=TOP_DOWNLOADS_RSS_URL)
        return super(TopDownloadsView, cls).initial_context(request, podcast=podcast)

    @BreadcrumbFactory
    def breadcrumb(cls, request, context):
        return Breadcrumb('podcasts',
                          lazy_parent(IndexView),
                          'Top downloads from iTunes U',
                          lazy_reverse('podcasts_top_downloads'))
                          
    def handle_GET(cls, request, context):
        return super(TopDownloadsView, cls).handle_GET(request, context)

class ITunesURedirectView(BaseView):
    breadcrumb = NullBreadcrumb
    
    def handle_POST(cls, request, context):
        use_itunesu = request.POST.get('use_itunesu') == 'yes'
        remember = 'remember' in request.POST
        
        if remember:
            request.preferences['podcasts']['use_itunesu'][request.device.devid] = use_itunesu
        
        if request.method == 'POST' and 'no_redirect' in request.POST:
            return HttpResponse('', mimetype="text/plain")
        elif request.method == 'POST' and not use_itunesu:
            if remember:
                return HttpResponseRedirect(reverse('podcasts_index'))
            else:
                return HttpResponseRedirect(reverse('podcasts_index') + '?show_itunesu_link=false')
        else:
            return HttpResponseRedirect("http://deimos.apple.com/WebObjects/Core.woa/Browse/ox-ac-uk-public")
        
class RedirectOldLinksView(BaseView):
    breadcrumb = NullBreadcrumb
    
    def get_metadata(cls, request, code, id=None, medium=None):
        if id:
            podcast = get_object_or_404(Podcast, category__code=code, id=int(id))
            return PodcastDetailView.get_metadata(request, podcast=podcast)
        else:
            return CategoryDetailView.get_metadata(request, code, medium)
    
    def handle_GET(cls, request, context, code, id=None, medium=None):
        category = get_object_or_404(PodcastCategory, code=code)
        if id:
            podcast = get_object_or_404(Podcast, category=category, id=int(id))
            url = reverse('podcasts_podcast', args=[podcast.identifier])
        elif medium:
            url = reverse('podcasts_category_medium', args=[category.code,medium])
        else:
            url = reverse('podcasts_category', args=[category.code])
        return HttpResponsePermanentRedirect(url)
