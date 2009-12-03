from views import EntityDetailView
from mobile_portal.oxpoints.models import Entity

class SiteSearch(object):
    def __new__(cls, query, only_app, request):
        print "Here"
        
        id = query.strip()
        if len(id) == 5:
            id = '693' + id
        if len(id) == 2:
            entities = Entity.objects.filter(central_stop_id=id.upper())
        elif len(id) == 8:
            entities = Entity.objects.filter(naptan_code=id)
        else:
            entities = []
            
           
        results = []
        for entity in entities:
            metadata = EntityDetailView.get_metadata(
                request,
                entity.entity_type.slug,
                entity.display_id
            )
            
            result = {
                'redirect_if_sole_result': True,
                'url': entity.get_absolute_url(),
                'excerpt': '',
                'application': 'maps',
            }
            result.update(metadata)
            
            results.append(result)
        
        print "Results", results
        return results, False, None