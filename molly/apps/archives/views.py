# Create your views here.
import logging

from django.core.urlresolvers import reverse
from django.core.paginator import Paginator
from django.http import Http404

from molly.utils.views import BaseView
from molly.utils.breadcrumbs import *

from forms import SearchForm, BrowseForm
#from search import ArchivesSearchResult #, ArchivesBrowse

logger = logging.getLogger(__name__)
search_logger = logging.getLogger('molly.archives.searches')


class IndexView(BaseView):

    def get_metadata(self, request):
        return {
            'title': 'Archives Search',
            'exclude_from_search': True
        }
    
    def initial_context(self, request):
        return {
            'search_form': SearchForm()
        }

    @BreadcrumbFactory
    def breadcrumb(self, request, context):
        return Breadcrumb(self.conf.local_name, None,
                          'Archives Search', lazy_reverse('index'))
        
    def handle_GET(self, request, context):
        return self.render(request, context, 'archives/index')
    

class SearchResultView(BaseView):
    def get_metadata(cls, request):
        return {
            'show_in_results': False,
        }

    def initial_context(cls, request):
        return {
            'search_form': SearchForm(request.GET),
        }
        
    @BreadcrumbFactory
    def breadcrumb(cls, request, context):
        x = 'item' in context or context['search_form'].is_valid()
        return Breadcrumb(
            cls.conf.local_name,
            lazy_parent('index'),
            'Search results' if x else 'Archives Search',
            lazy_reverse('search'),
        )
        
    class InconsistentQuery(ValueError):
        def __init__(self, msg):
            self.msg = msg

    def handle_GET(self, request, context):
        search_form = context['search_form']
        if not (request.GET and search_form.is_valid()):
            return self.handle_no_search(request, context)
        # get query from form
        query = self.construct_query(request, search_form)
        # _could_ parse query for validity, but fairly safe as constructed
        # from form, and in any case server will diagnose if invalid
        
#        try:
#            query, removed = self.construct_query(request, search_form)
#        except self.InconsistentQuery, e:
#            return self.handle_error(request, context, e.msg)
        # check which page of results is needed - SRU handles its own pagination
        try:
            page_index = int(request.GET['page'])
        except (ValueError, KeyError):
            page_index = 1
        maximumRecords = getattr(self.conf, 'resultsPerPage', 10)
        startRecord = ((page_index - 1) * maximumRecords) + 1
        # carry out search
        try:
            results = self.conf.provider.perform_search(query, application=None, 
                                               maximumRecords=maximumRecords,
                                               startRecord=startRecord)
        except Exception, e:
            logger.exception("Archives SRU query error")
            raise
            return self.handle_error(request, context, 'An error occurred: %s' % e)
        # SRU handles own pagination - fake other pages!?
#        results = [None] * res.numberOfResults
#        results[startRecord - 1:startRecord - 1 + maximumRecords] = res.resultSetItems
        paginator = Paginator(results, maximumRecords)
        page = paginator.page(page_index)
        context.update({
            'results': paginator,
            'page': page,
        })
        return self.render(request, context, 'archives/item_list')
    
    def handle_error(self, request, context, message):
        context['error_message'] = message
        return self.render(request, context, 'archives/item_list')
    
    def handle_no_search(self, request, context, message):
        context['error_message'] = message
        return self.render(request, context, 'archives/item_list')
    
    def construct_query(self, request, search_form):
        query, removed = [], set()
        title, author, isbn = '', '', ''
        if search_form.cleaned_data['index']:
            index = search_form.cleaned_data['index']
        else:
            index = "cql.anywhere"
        if search_form.cleaned_data['relation']:
            relation = search_form.cleaned_data['relation']
        else:
            relation = "and/rel.algoithm=okapi"
        if search_form.cleaned_data['value']:
            value = search_form.cleaned_data['value']
            
        if not (index and relation and value):
            raise self.InconsistentQuery("You must supply some search terms.")

        search_logger.info("Archives query", extra={
            'session_key': request.session.session_key,
            'index': index,
            'relation': relation,
            'value': value,
        })
        return '{0} {1} "{2}"'.format(index, relation, value)


class ItemDetailView(BaseView):
    
    def handle_GET(self, request, context):
        pass


class BrowseResultView(BaseView):
    
    def handle_GET(self, request, context):
        pass
    