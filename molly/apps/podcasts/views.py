import urllib
from datetime import timedelta
from xml.etree import ElementTree as ET

from django.http import HttpResponse, Http404
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _
from django.utils.translation import get_language
from django.db.models import Q

from molly.utils.views import BaseView
from molly.utils.breadcrumbs import *

from molly.wurfl import device_parents

from molly.apps.podcasts.models import Podcast, PodcastCategory


class IndexView(BaseView):
    def get_metadata(self, request):
        return {
            'title': _('Podcasts'),
            'additional': _('Browse and listen to podcasts from around the University.')
        }
        
    @BreadcrumbFactory
    def breadcrumb(self, request, context):
        return Breadcrumb(self.conf.local_name, None,
                          _('Podcasts'), lazy_reverse('index'))
        
    def handle_GET(self, request, context):
        show_itunesu_link = request.session.get('podcasts:use_itunesu') == None
        if 'show_itunesu_link' in request.GET:
            show_itunesu_link = request.GET['show_itunesu_link'] != 'false'
        
        context.update({
            'categories': [c for c in PodcastCategory.objects.all()
                                        if c.podcast_set.all().count() > 0],
            'show_itunesu_link': show_itunesu_link,
            'podcasts': Podcast.objects.filter(category__isnull=True)
        })
        return self.render(request, context, 'podcasts/index',
                           expires=timedelta(days=7))

class CategoryDetailView(BaseView):
    def get_metadata(self, request, category, medium=None):
        if medium:
            raise Http404
            
        category = get_object_or_404(PodcastCategory, slug=category)
        return {
            'title': category.name,
            'additional': '<strong>' + _('Podcast category') + '</strong>'
        }
        
    def initial_context(self, request, category, medium=None):
        category = get_object_or_404(PodcastCategory, slug=category)
        
        # Only actually care about showing podcasts in the right language, not
        # dialect, so only match on before the -
        lang_code = get_language()
        if '-' in lang_code:
            lang_code = lang_code.split('-')[0]
        
        # Show all podcasts with no language
        podcasts = Podcast.objects.filter(category=category)
        if medium not in (None, 'all'):
            podcasts = podcasts.filter(medium=medium)
    
        all_podcasts = podcasts.count()
        if medium != 'all':
            podcasts = podcasts.filter(
                Q(language__startswith=lang_code) | Q(language=None)
            )
        lang_podcasts = podcasts.count()
    
        return {
            'category': category,
            'podcasts': podcasts,
            'medium': medium,
            'more_in_all': lang_podcasts != all_podcasts,
        }

    @BreadcrumbFactory
    def breadcrumb(self, request, context, category, medium=None):
        if medium:
            url = lazy_reverse('category-medium', args=[category,medium])
        else:
            url = lazy_reverse('category', args=[category])
        
        return Breadcrumb(self.conf.local_name, lazy_parent('index'),
                          context['category'].name,
                          url)
        
    def handle_GET(self, request, context, category, medium=None):
        return self.render(request, context, 'podcasts/category_detail',
                           expires=timedelta(hours=4))

class PodcastDetailView(BaseView):
    class RespondThus(Exception):
        def __init__(self, response):
            self.response = response
            
    def get_metadata(self, request, slug=None, podcast=None):
        if not podcast:
            try:
                podcast = get_object_or_404(Podcast, slug=slug)
            except Podcast.MultipleObjectsReturned:
                for podcast in Podcast.objects.filter(slug=slug)[1:]:
                    podcast.delete()
                podcast = get_object_or_404(Podcast, slug=slug)
        
        return {
            'title': podcast.title,
            'category': _('podcast'),
            'category_display': _('podcast'),
            'last_updated': podcast.last_updated,
            'additional': '<strong>' + _('Podcast') + '</strong> %s' % podcast.last_updated.strftime('%d %b %Y')
        }
        
    def initial_context(self, request, slug=None, podcast=None):
        if not podcast:
            try:
                podcast = get_object_or_404(Podcast, slug=slug)
            except Podcast.MultipleObjectsReturned:
                for podcast in Podcast.objects.filter(slug=slug)[1:]:
                    podcast.delete()
                podcast = get_object_or_404(Podcast, slug=slug)
        return {
            'podcast': podcast,
            'category': podcast.category,
        }
    
    @BreadcrumbFactory
    def breadcrumb(self, request, context, slug=None, podcast=None):
        if context['podcast'].category:
            parent = lazy_parent('category',
                                 category=context['podcast'].category.slug)
        else:
            parent = lazy_parent('index')
        return Breadcrumb(self.conf.local_name,
                          parent,
                          context['podcast'].title,
                          lazy_reverse('podcast'))
        
    def handle_GET(self, request, context, slug=None, podcast=None):
        if 'response' in context:
            return context['response']        
        
        items = context['podcast'].podcastitem_set.order_by('order','-published_date')
        
        context.update({
            'items': items,
        })
        return self.render(request, context, 'podcasts/podcast_detail',
                           expires=timedelta(hours=1))

class ITunesURedirectView(BaseView):
    breadcrumb = NullBreadcrumb
    
    def handle_POST(self, request, context):
        use_itunesu = request.POST.get('use_itunesu') == 'yes'
        remember = 'remember' in request.POST
        
        if remember:
            request.session['podcasts:use_itunesu'] = use_itunesu
        
        if request.method == 'POST' and 'no_redirect' in request.POST:
            return HttpResponse('', mimetype="text/plain")
        elif request.method == 'POST' and not use_itunesu:
            if remember:
                return self.redirect(reverse('podcasts:index'), request)
            else:
                return self.redirect(
                    reverse('podcasts:index') + '?show_itunesu_link=false',
                    request)
        else:
            # TODO Remove hard link to Oxford's iTunes U library
            return self.redirect(
                "http://deimos.apple.com/WebObjects/Core.woa/Browse/ox-ac-uk-public",
                request)
