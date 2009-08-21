from datetime import datetime

from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse

from pysakai import Connection
from pysakai.apps.sites.tools.signup import NoSuchMeetingException

from mobile_portal.core.renderers import mobile_render

def get_connection(weblearn_cookie, cache=None):
    c = Connection('weblearn.ox.ac.uk', secure=True, cache=cache)
    c.auths['cookie'].authenticate(weblearn_cookie)
    return c

def assert_connection(f):
    def g(request, *args, **kwargs):
        try:
            cache = request.session['weblearn_cache']
        except KeyError:
            cache = {}
        try:
            c = get_connection(request.session['weblearn_cookie'], cache=cache)
        except:
            return HttpResponseRedirect(reverse('sakai_set_cookie'))
        else:
            r = f(request, c, *args, **kwargs)
            request.session['weblearn_cache'] = c._cache
            return r
            
    g.__doc__ = f.__doc__
    return g

@assert_connection
def index(request, connection):
   
    context = {
        'connection': connection
    }
    return mobile_render(request, context, 'sakai/index')
    
def set_cookie(request):
    if request.method == 'POST':
        try:
            get_connection(request.POST['weblearn_cookie'])
        except:
            request.user.message_set.create(
                message='You did not supply a valid cookie; please try again.'
            )
        else:
            request.session['weblearn_cookie'] = request.POST['weblearn_cookie']
            return HttpResponseRedirect(reverse('sakai_index'))
        
    return mobile_render(request, {}, 'sakai/set_cookie')

@assert_connection
def signup_index(request, connection):
    sites = connection.sites.by_tool('signup')
    
    context = {
        'sites':sites,
        'now': datetime.now(),
        'connection': connection,
        'cache': (connection._cache, request.session['weblearn_cache']) 
    }
    
    return mobile_render(request, context, 'sakai/signup')
    
@assert_connection
def signup_timeslot(request, connection, site_id, meeting, timeslot):
    """
    This URL only accepts POST requests, with one of the following parameters
    set: 'signup' or 'cancel'.
    
    You will get a 400 Bad Request if you provide exactly one of these
    parameters or attempt to cancel a timeslot you are not scheduled to attend.
    
    All GETs will result in a 405 Method Not Allowed response.
    
    For those desiring to URL-hack, the final part takes the form:
        <site_id>:<meeting_start>:<timeslot_start>
        
    <site_id> is the first eight characters of the SHA1 hash of the full URL
    for the site, including URI scheme and hostname.
    
    <meeting_start> and <timeslot_start> are in the form 'YYYYMMDDhhmm'.
    """
    
    site = connection.sites.get_site_by_id(site_id)
    if not site:
        raise Http404
    
    try:
        meeting_start = datetime(*map(int, [meeting[:4], meeting[4:6], meeting[6:8], meeting[8:10], meeting[10:12]]))
        timeslot_start = datetime(*map(int, [timeslot[:4], timeslot[4:6], timeslot[6:8], timeslot[8:10], timeslot[10:12]]))
    except ValueError:
        raise Http404
        
    try:
        meeting, meeting_id = site.tools['signup'].get_meeting_by_start(meeting_start), meeting
        timeslot = [t for t in meeting.timeslots if t.start == timeslot_start][0]
    except (NoSuchMeetingException, IndexError):
        raise Http404

    if request.method != 'POST':
        return HttpResponse(signup_timeslot.__doc__.replace('\n    ', '\n')[1:], status=405, mimetype="text/plain")
    if len(set(request.POST) & set(['signup', 'cancel'])) != 1:
        return HttpResponse('', status=400, mimetype="text/plain")
        
    if 'cancel' in request.POST:
        if timeslot.signed_up:
            timeslot.cancel()
        else:
            return HttpResponse('', status=400, mimetype="text/plain")
    else:
        if not timeslot.signed_up:
            if meeting.attending:
                current_timeslot = [t for t in meeting.timeslots if t.signed_up][0]
                current_timeslot.cancel()
            timeslot.sign_up()
    
    return HttpResponseRedirect(reverse('sakai_signup') + "#meeting_%s_%s" % (site_id, meeting_id))
        
        
    