# Create your views here.
from datetime import datetime, timedelta
import pytz, simplejson, urllib, random

from django.http import HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect, Http404
from django.core.urlresolvers import reverse, resolve
from django.shortcuts import get_object_or_404, render_to_response
from django.conf import settings
from django.core.management import call_command
from django.template import loader, Context, RequestContext
from django.core.mail import EmailMessage
from django import forms

from molly.utils.views import BaseView
from molly.utils.renderers import mobile_render
from molly.utils import geolocation
from molly.utils.breadcrumbs import *

from molly.osm.utils import fit_to_map
from molly.wurfl import device_parents
from molly.googlesearch.forms import GoogleSearchForm

from models import FrontPageLink, ExternalImageSized, LocationShare, UserMessage, ShortenedURL, BlogArticle
from forms import LocationShareForm, LocationShareAddForm, FeedbackForm, UserMessageFormSet, LocationUpdateForm

from context_processors import device_specific_media


class IndexView(BaseView):

    @BreadcrumbFactory
    def breadcrumb(cls, request, context):
        return Breadcrumb('core', None, 'Home', lazy_reverse('core:index'))
        
    def handle_GET(cls, request, context):
        internal_referer = request.META.get('HTTP_REFERER', '').startswith('http://oucs-alexd:8000/')
        internal_referer = request.META.get('HTTP_REFERER', '').startswith('http://m.ox.ac.uk/')
    
        if ("generic_web_browser" in device_parents[request.device.devid]
            and not request.preferences['core']['desktop_about_shown']
            and not request.GET.get('preview') == 'true'
            and not internal_referer
            and not settings.DEBUG):
            return HttpResponseRedirect(reverse('core:exposition'))
    
        fpls = dict((fpl.slug, fpl) for fpl in FrontPageLink.objects.all())
        fpls_prefs = sorted(request.preferences['front_page_links'].items(), key=lambda (slug,(order, display)): order)
        front_page_links = [fpls[slug] for (slug,(order, display)) in fpls_prefs if display and slug in fpls]
    
        gsf = GoogleSearchForm()
        gsf.fields['query'].widget.attrs['class'] = 'index-search-box'
    
        context = {
            'front_page_links': front_page_links,
            'search_form': gsf,
            'hide_feedback_link': True,
            'has_user_messages': UserMessage.objects.filter(session_key = request.session.session_key).count() > 0,
            'ua': request.META.get('HTTP_USER_AGENT', ''),
            'parents': device_parents[request.device.devid]

        }
        return mobile_render(request, context, 'core/index')
    
    def handle_POST(cls, request, context):
        no_desktop_about = {'true':True, 'false':False}.get(request.POST.get('no_desktop_about'))
        if not no_desktop_about is None:
            request.preferences['core']['desktop_about_shown'] = no_desktop_about
            
        return HttpResponseRedirect(reverse('core:index'))

class LocationUpdateView(BaseView):
    breadcrumb = NullBreadcrumb

    def initial_context(cls, request):
        data = dict(request.REQUEST.items())
        data['http_method'] = request.method
        return {
            'form': LocationUpdateForm(data),
            'format': request.REQUEST.get('format'),
            'return_url': request.REQUEST.get('return_url', ''),
            'requiring_url': hasattr(request, 'requiring_url'),
        }
        
    def handle_GET(cls, request, context):
        form = context['form']
        
        if form.is_valid():
            placemarks = geolocation.geocode(form.cleaned_data['name'])
            if placemarks:
                points = [(o[1][0], o[1][1], 'red') for o in placemarks]
                map_hash, (new_points, zoom) = fit_to_map(
                    None,
                    points = points,
                    min_points = len(points),
                    zoom = None if len(points)>1 else 15,
                    width = request.map_width,
                    height = request.map_height,
                )
            else:
                map_hash, zoom = None, None
            context.update({
                'placemarks': placemarks,
                'map_url': reverse('osm_generated_map', args=[map_hash]) if map_hash else None,
                'zoom': zoom,
                'zoom_controls': False,
            })
#        else:
#            context['placemarks'] = []
            
        if context['format'] == 'json':
            del context['form']
            del context['format']
            del context['breadcrumbs']
            return cls.json_response(context)
        elif context['format'] == 'embed':
            if form.is_valid():
                return mobile_render(request, context, 'core/update_location_confirm')
            else:
                return mobile_render(request, context, 'core/update_location_embed')
        else:
            return mobile_render(request, context, 'core/update_location')
            
        
    def handle_POST(cls, request, context):
        form = context['form']
        
        if form.is_valid():
            geolocation.set_location(request,
                                     form.cleaned_data['name'],
                                     form.cleaned_data['location'],
                                     form.cleaned_data['accuracy'],
                                     form.cleaned_data['method'])
        
        if context['format'] == 'json':
            return cls.json_response({
                'name': form.cleaned_data['name'],
            })
        else:
            if context.get('return_url'):
                return HttpResponseRedirect(context['return_url'])
            else:
                return HttpResponseRedirect(reverse('core:index'))

class LocationRequiredView(BaseView):
    def __new__(cls, request, *args, **kwargs):
        if request.preferences['location']['location']:
            return super(LocationRequiredView, cls).__new__(cls, request, *args, **kwargs)
        else:
            request.GET = dict(request.GET.items())
            request.GET['return_url'] = request.path
            request.requiring_location = True
            return LocationUpdateView(request)


if False:
    @require_auth
    def customise(request):
        post = request.POST or None
        links = request.user.get_profile().front_page_links.order_by('order')
    
        forms = [FrontPageLinkForm(post, instance=l, prefix="%d"%i) for i,l in enumerate(links)]
    
        if all(f.is_valid() for f in forms):
            forms.sort(key=lambda x:x.cleaned_data['order'])
            for i, f in enumerate(forms):
                f.cleaned_data['order'] = i+1
                f.save()
            return HttpResponseRedirect(reverse("index"))
    
        context = {
            'forms': forms,
        }
        return mobile_render(request, context, 'core/customise')

class ExternalImageView(BaseView):

    breadcrumb = NullBreadcrumb

    def handle_GET(cls, request, context, slug):
        eis = get_object_or_404(ExternalImageSized, slug=slug)
        response = HttpResponse(open(eis.get_filename(), 'r').read(), mimetype='image/jpeg')
        last_updated = pytz.utc.localize(eis.external_image.last_updated)
    
        response['ETag'] = slug
        return response

if False:
    @require_auth
    def location_sharing(request):
        post = request.POST or None
    
        location_shares = LocationShare.objects.filter(from_user=request.user).order_by('from_user')
        location_share_forms = []
        for i, location_share in enumerate(location_shares):
            lsf = LocationShareForm(post, instance=location_share, prefix="%d" % i)
            location_share_forms.append( lsf )
        location_share_add_form = LocationShareAddForm(post)
    
    
        if post and 'location_share_add' in post:
            if location_share_add_form.is_valid():
                try:
                    user = find_or_create_user_by_email(location_share_add_form.cleaned_data['email'], create_external_user=False)
                except ValueError:
                    request.user.message_set.create(message="No user with that e-mail address exists.")
                else:
                    if user in [ls.to_user for ls in location_shares]:
                        request.user.message_set.create(message="You are already sharing your location with that person.")
                    else:
                        location_share = LocationShare(
                            from_user = request.user,
                            to_user = user,
                            accuracy = location_share_add_form.cleaned_data['accuracy'],
                        )
                        if location_share_add_form.cleaned_data['limit']:
                            location_share.until = datetime.now() + timedelta(hours=location_share_add_form.cleaned_data['limit'])
                        location_share.save()
                        response = HttpResponseRedirect('.')
                        response.status_code = 303
                        return response
            else:
                request.user.message_set.create(message="Please enter a valid e-mail address.")
    
    
        context = {
            'location_share_forms': location_share_forms,
            'location_share_add_form': location_share_add_form,
        }
    
        return mobile_render(request, context, 'core/location_sharing')

class RunCommandView(BaseView):

    commands = {
        'update_podcasts': ('Update podcasts', []),
        'update_osm': ('Update OpenStreetMap data', []),
        'update_oxpoints': ('Update OxPoints data', []),
        'update_busstops': ('Update bus stop data', []),
        'update_rss': ('Update RSS feeds', []),
        'update_weather': ('Update weather feed', []),
#        'generate_markers': ('Generate map markers', []),
#        'pull_markers': ('Pull markers from external location', ['location']),
    }
    
    @BreadcrumbFactory
    def breadcrumb(cls, request, context):
        return Breadcrumb('core', None, 'Run command', lazy_reverse('core:run_command'))
        
    def __new__(cls, request, *args, **kwargs):
        if not request.user.is_superuser:
            raise Http404
        return super(RunCommandView, cls).__new__(request, *args, **kwargs)
        
    def initial_context(cls, request):
        return {
            'commands': RunCommandView.commands,
        }
        
    def handle_GET(cls, request, context):
        return mobile_render(request, context, 'core/run_command')
        
    def handle_POST(cls, request, context):

        command = request.POST['command']

        if command in commands:
            arg_names = commands[request.POST['command']][1]
            args = {}
            for arg in arg_names:
                args[arg] = request.POST[arg]

            call_command(command, **args)
            
        return HttpResponseRedirect(request.path)

class StaticDetailView(BaseView):
    @BreadcrumbFactory
    def breadcrumb(cls, request, context, title, template):
        return Breadcrumb(
            'core', None, title,
            lazy_reverse('core:static', args=[template])
        )
    
    def handle_GET(cls, request, context, title, template):
        t = loader.get_template('static/%s.xhtml' % template)
    
        context.update({
            'title': title,
            'content': t.render(Context()),
        })
        return mobile_render(request, context, 'core/static_detail')

class ExpositionView(BaseView):
    def get_metadata(cls, request, page):
        return {
            'exclude_from_search': True
        }
    
    breadcrumb = NullBreadcrumb
    cache_page_duration = 60*15
    
    def handle_GET(cls, request, context, page):
        page = page or 'about'
        template = loader.get_template('core/exposition/%s.xhtml' % page)
        
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
            return render_to_response('core/exposition/container.xhtml', {
                'content': content,
                'page': page,
            }, context_instance=RequestContext(request))    

def handler500(request):
    context = {
        'MEDIA_URL': settings.MEDIA_URL,
    }
    context.update(device_specific_media(request))
    response = render_to_response('500.html', context)
    response.status_code = 500
    return response

class FeedbackView(BaseView):
    @BreadcrumbFactory
    def breadcrumb(cls, request, context):
        return Breadcrumb(
            'core', None, 'Feedback',
            lazy_reverse('feedback')
        )
        
    def initial_context(cls, request):
        return {
            'feedback_form': FeedbackForm(request.POST or None)
        }
        
    def handle_GET(cls, request, context):
        context.update({
           'sent': request.GET.get('sent') == 'true',
           'referer': request.GET.get('referer', ''),
        })
        return mobile_render(request, context, 'core/feedback')
        
    def handle_POST(cls, request, context):
        if context['feedback_form'].is_valid():
            email = EmailMessage(
                'm.ox | Comment',
                cls.get_email_body(request, context), None,
                ('%s <%s>' % admin for admin in settings.ADMINS),
                [], None, [],
                {'Reply-To': context['feedback_form'].cleaned_data['email']},
            )
            email.send()
            
            qs = urllib.urlencode({
                'sent':'true',
                'referer': request.POST.get('referer', ''),
            })
       
            return HttpResponseRedirect('%s?%s' % (reverse('core:feedback'), qs))
            
        else:
            return cls.handle_GET(request, context)
            
    def get_email_body(cls, request, context):
        form = context['feedback_form']
        params = {
            'email': form.cleaned_data['email'],
            'devid': request.device.devid,
            'ua': urllib.urlencode({'user_agent':request.META['HTTP_USER_AGENT']}),
            'referer': request.POST.get('referer', ''),
            'lat': request.preferences['location']['location'][0],
            'lon': request.preferences['location']['location'][1],
            'body': form.cleaned_data['body'],
            'session_key': request.session.session_key,
        }
        body = """\
Meta
====

E-mail:      %(email)s
Device:      http://www.wurflpro.com/device/results?user_agent=&identifier=%(devid)s
User-agent:  http://www.wurflpro.com/device/results?%(ua)s
Referer:     %(referer)s
Location:    http://www.google.co.uk/search?q=%(lat)f,%(lon)f
Session key: %(session_key)s

Message
=======

%(body)s
""" % params

        return body
    
class UserMessageView(BaseView):
    @BreadcrumbFactory
    def breadcrumb(cls, request, context):
        return Breadcrumb(
            'core', None, 'View messages from the developers',
            lazy_reverse('core:messages')
        )
        
    def initial_context(cls, request):
        try:
            formset = UserMessageFormSet(
                request.POST or None,
                queryset=UserMessage.objects.filter(
                    session_key=request.session.session_key
                )
            )
        except forms.ValidationError:
            formset = UserMessageFormSet(
                None,
                queryset=UserMessage.objects.filter(
                    session_key=request.session.session_key
                )
            )            
        return {
            'formset': formset,
        }

    def handle_GET(cls, request, context):
        UserMessage.objects.filter(session_key=request.session.session_key).update(read=True)
        return mobile_render(request, context, 'core/messages')
        
    def handle_POST(cls, request, context):
        if context['formset'].is_valid():
            context['formset'].save()
            
        return HttpResponseRedirect(reverse('core:messages'))

class ShortenedURLRedirectView(BaseView):
    breadcrumb = NullBreadcrumb

    def handle_GET(cls, request, context, slug):
        shortened_url = get_object_or_404(ShortenedURL, slug=slug)
        return HttpResponsePermanentRedirect(shortened_url.path)

class ShortenURLView(BaseView):
    # We'll omit characters that look similar to one another
    AVAILABLE_CHARS = '23456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghkmnpqrstuvwxyz'
    
    def initial_context(cls, request):
        try:
            path = request.GET['path']
            view, view_args, view_kwargs = resolve(path.split('?')[0])
            if getattr(view, 'simple_shorten_breadcrumb', False):
                view_context = None
            else:
                view_context = view.initial_context(request, *view_args, **view_kwargs)
            
        except (KeyError, ):
            raise Http404
            
        return {
            'path': path,
            'view': view,
            'view_args': view_args,
            'view_kwargs': view_kwargs,
            'view_context': view_context,
            'complex_shorten': ('?' in path) or view_context is None or view_context.get('complex_shorten', False),
        }

    def breadcrumb_render(cls, request, context):
        view, view_context = context['view'], context['view_context']
        view_args, view_kwargs = context['view_args'], context['view_kwargs']
        
        if view_context:
            breadcrumb = view.breadcrumb.render(view, request, view_context, *view_args, **view_kwargs)
            return (
                breadcrumb[0],
                breadcrumb[1],
                (breadcrumb[4], context['path']),
                breadcrumb[1] == (breadcrumb[4], context['path']),
                'Shorten link',
            )
        else:
            index = resolve(reverse('%s_index' % view.app_name))[0].breadcrumb(request, context)
            index = index.title, index.url()
            return (
                view.app_name,
                index,
                (u'Back\u2026', context['path']),
                False,
                'Shorten link',
            )

    # Create a 'blank' object to attach our render method to by constructing
    # a class and then calling its constructor. It's a bit messy, and probably
    # points at a need to refactor breadcrumbs so that view.breadcrumb returns
    # the five-tuple passed to the template as opposed to
    # view.breadcrumb.render. 
    breadcrumb = type('bc', (object,), {})()
    breadcrumb.render = breadcrumb_render

            
    def handle_GET(cls, request, context):
        print context['complex_shorten']
        try:
            path = request.GET['path']
        except (KeyError):
            return cls.invalid_path(request, context)

        context['shortened_url'], created = ShortenedURL.objects.get_or_create(path=path)
        
        if created:
            if context['complex_shorten']:
                slug = '0'+''.join(random.choice(cls.AVAILABLE_CHARS) for i in range(5))
            else:
                slug = unicode(context['shortened_url'].id)
            context['shortened_url'].slug = slug
            context['shortened_url'].save()

        return mobile_render(request, context, 'core/shorten_url')
