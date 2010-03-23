
def wurfl_device(request):
    return {
        'browser': request.browser,
        'device': request.device,
    }