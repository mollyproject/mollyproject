from django.core.paginator import Paginator

from mobile_portal.core.ldap_queries import get_person_units
from mobile_portal.core.renderers import mobile_render

from models import RSSFeed, RSSItem

def get_user_data(request):
    if False and request.user.is_authenticated():
        units = get_person_units(request.user.get_profile().webauth_username)

    else:
        units = []
        
    return {
        'authenticated': request.user.is_authenticated(),
        'units': units
    } 

def index(request):
    feeds = RSSFeed.objects.all()
    
    user_data = get_user_data(request)
    feeds = set(feed for feed in feeds if not feed.show_predicate or eval(feed.show_predicate.predicate, user_data))
    
    items = RSSItem.objects.filter(feed__in = feeds).order_by('-last_modified')
    
    paginator = Paginator(items, 10)
    try:
        page_index = int(request.GET['page'])
    except:
        page_index = 1
    try:
        page = paginator.page(page_index)
    except (EmptyPage, InvalidPage):
        page = paginator.page(paginator.num_pages)

    context = {
        'page': page,
    }    
    
    return mobile_render(request, context, 'rss/index')