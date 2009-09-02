from models import Preferences
from defaults import defaults

class PreferencesMiddleware(object):
    def process_request(self, request):

        if request.user.is_authenticated():
            request.preferences_object, created = Preferences.objects.get_or_create(user=request.user)
        else:
            session_key = request.session.session_key
            request.preferences_object, created = Preferences.objects.get_or_create(session_key=session_key)
            print "Created", created
        request.preferences = request.preferences_object.preference_set
        print "Loading", request.preferences._data, id(request.preferences)
        
    def process_response(self, request, response):
        try:
            print "Saving", request.preferences._data, id(request.preferences)
            request.preferences_object.save()
        except AttributeError:
            pass

        return response