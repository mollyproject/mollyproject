from molly.wurfl import device_parents

def parse_version(s):
    try:
        return tuple(map(int, s.split('.')))
    except ValueError:
        return (0,)

def device_specific_media(request):
    """
    Uses DEVICE_SPECIFIC_MEDIA as a basis to pass extra context when the
    wurfl-detected device is a child of a given device id.
    """

    device, browser = request.device, request.browser
    use_javascript = True

    # Skyfire
    if browser.devid == 'generic_skyfire':
        style_group = "dumb"

    # Apple products
    elif device.brand_name == 'Apple' :
        style_group = "smart"

    # Symbian S60 v3 and above (iresspective of browser)
    elif device.device_os in ('Symbian', 'Symbian OS') and parse_version(device.device_os_version) >= (9, 2) :
        style_group = "smart"

    # Nokia Maemo
    elif device.brand_name == 'Nokia' and device.device_os == 'Linux Smartphone OS' :
        style_group = "smart"

    # Blackberries
    elif device.brand_name == 'RIM' :
        style_group = 'smart'
        use_javascript = False

    # Android
    elif device.device_os == 'Android' :
        style_group = 'smart'

    # Palm Web OS
    elif device.device_os == 'Web OS' :
        style_group = 'smart'

    # Opera Mini/Mobile Browsers
    elif browser.brand_name == 'Opera':
        style_group = 'smart'

    # Desktop browsers
    elif 'generic_web_browser' in device_parents[browser.devid]:
        style_group = 'smart'

    # All Others
    else:
        style_group = "dumb"
        use_javascript = False

    return {
        'style_group': 'groups-%s' % style_group,
        'use_javascript': use_javascript,
    }

def wurfl_device(request):
    return {
        'browser': request.browser,
        'device': request.device,
        'map_width': request.map_width,
        'map_height': request.map_height,
    }