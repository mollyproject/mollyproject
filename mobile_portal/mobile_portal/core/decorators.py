from renderers import mobile_render

def require_location(f):
    def g(request, *args, **kwargs):
        if not request.preferences['location']['location']:
            return location_required(request, *args, **kwargs)
        return f(request, *args, **kwargs)
    return g
    
def location_required(request, *args, **kwargs):
    context = {
        'return_url': request.get_full_path()
    }
    return mobile_render(request, context, 'core/require_location')