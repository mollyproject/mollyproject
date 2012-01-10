from django.core.urlresolvers import RegexURLPattern

def url(pattern, name=None, extra={}):
    
    def url_annotator(view):
        view.pattern = RegexURLPattern(pattern, view, extra, name)
        return view
    
    return url_annotator
