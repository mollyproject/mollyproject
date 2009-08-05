from renderers import mobile_render

def require_location(f):
    def g(request, *args, **kwargs):
        if not (hasattr(request, 'location') and request.location):
            context = {
                'return_url': request.get_full_path()
            }
            return mobile_render(request, context, 'core/require_location')
        return f(request, *args, **kwargs)
    return g