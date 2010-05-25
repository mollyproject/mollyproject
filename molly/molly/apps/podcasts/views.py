import urllib
from xml.etree import ElementTree as ET

from django.http import HttpResponseRedirect, HttpResponsePermanentRedirect, HttpResponse, Http404
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404

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
                          'Podcasts', lazy_reverse('podcasts:index'))
        
    def handle_GET(cls, request, context):
        show_itunesu_link = request.session.get('podcasts:use_itunesu') == None
        if 'show_itunesu_link' in request.GET:
            show_itunesu_link = request.GET['show_itunesu_link'] != 'false'
    
        #if "apple_iphone_ver1" in device_parents[request.device.devid] :
        #        return HttpResponseRedirect ("http://deimos.apple.com/WebObjects/Core.woa/Browse/ox-ac-uk-public")
        context.update({
            'categories': PodcastCategory.objects.all(),
            'show_itunesu_link': show_itunesu_link,
        })
        return cls.render(request, context, 'podcasts/index')

class CategoryDetailView(BaseView):
    def get_metadata(cls, request, category, medium=None):
        if medium:
            raise Http404
            
        category = get_object_or_404(PodcastCategory, slug=category)
        return {
            'title': category.name,
            'additional': '<strong>Podcast category</strong>'
        }
        
    def initial_context(cls, request, category, medium=None):
        category = get_object_or_404(PodcastCategory, slug=category)
        podcasts = Podcast.objects.filter(category=category)
        if medium:
            podcasts = podcasts.filter(medium=medium)
    
        return {
            'category': category,
            'podcasts': podcasts,
            'medium': medium,
        }

    @BreadcrumbFactory
    def breadcrumb(cls, request, context, category, medium=None):
        if medium:
            url = lazy_reverse('podcasts:category_medium', args=[category,medium])
        else:
            url = lazy_reverse('podcasts:category', args=[category])
        
        return Breadcrumb('podcasts', lazy_parent(IndexView),
                          context['category'].name,
                          url)
        
    def handle_GET(cls, request, context, category, medium=None):
        return cls.render(request, context, 'podcasts/category_detail')

class PodcastDetailView(BaseView):
    class RespondThus(Exception):
        def __init__(self, response):
            self.response = response
            
    def get_metadata(cls, request, slug=None, podcast=None):
        if not podcast:
            podcast = get_object_or_404(Podcast, slug=slug)
        
        return {
            'title': podcast.title,
            'category': 'podcast',
            'category_display': 'podcast',
            'last_updated': podcast.last_updated,
            'additional': '<strong>Podcast</strong> %s' % podcast.last_updated.strftime('%d %b %Y')
        }
        
    def initial_context(cls, request, slug=None, podcast=None):
        if not podcast:
            podcast = get_object_or_404(Podcast, slug=slug)
        return {
            'podcast': podcast,
            'category': podcast.category,
        }
    
    @BreadcrumbFactory
    def breadcrumb(cls, request, context, slug=None, podcast=None):
        if context['podcast'].category:
            parent = lazy_parent(CategoryDetailView,
                                 category=context['podcast'].category.slug)
        else:
            parent = lazy_parent(IndexView)
        return Breadcrumb('podcasts',
                          parent,
                          context['podcast'].title,
                          lazy_reverse('podcasts:podcast'))
        
    def handle_GET(cls, request, context, slug=None, podcast=None):
        if 'response' in context:
            return context['response']        
        
        items = context['podcast'].podcastitem_set.order_by('order','-published_date')
        
        context.update({
            'items': items,
        })
        return cls.render(request, context, 'podcasts/podcast_detail')

class ITunesURedirectView(BaseView):
    breadcrumb = NullBreadcrumb
    
    def handle_POST(cls, request, context):
        use_itunesu = request.POST.get('use_itunesu') == 'yes'
        remember = 'remember' in request.POST
        
        if remember:
            request.session['podcasts:use_itunesu'] = use_itunesu
        
        if request.method == 'POST' and 'no_redirect' in request.POST:
            return HttpResponse('', mimetype="text/plain")
        elif request.method == 'POST' and not use_itunesu:
            if remember:
                return HttpResponseRedirect(reverse('podcasts:index'))
            else:
                return HttpResponseRedirect(reverse('podcasts:index') + '?show_itunesu_link=false')
        else:
            return HttpResponseRedirect("http://deimos.apple.com/WebObjects/Core.woa/Browse/ox-ac-uk-public")
