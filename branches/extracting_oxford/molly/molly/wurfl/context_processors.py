
def wurfl_device(request):
    return {
        'browser': request.browser,
        'device': request.device,
        'map_width': request.map_width,
        'map_height': request.map_height,
    }