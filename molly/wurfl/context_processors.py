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
    use_slippy_maps = device.pointing_method == "touchscreen"

    # Skyfire
    if browser.devid == 'generic_skyfire':
        style_group = "dumb"

    # Apple products
    elif device.brand_name == 'Apple' :
        style_group = "smart"

    # Symbian S60 v3 and above (iresspective of browser)
    elif device.device_os in ('Symbian', 'Symbian OS') and parse_version(device.device_os_version) >= (9, 2) :
        style_group = "smart"
        use_slippy_maps = False
        if parse_version(device.device_os_version) < (9, 4):
            # Only S60 5th edition properly supports JQuery
            use_javascript = False

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
    elif browser.brand_name == 'Opera' or browser.mobile_browser == 'Opera':
        style_group = 'smart'
        # Opera Mini 4 doesn't properly support JS
        if browser.mobile_browser == 'Opera Mini' and parse_version(browser.mobile_browser_version) <= (5,):
            use_javascript = False

    # Windows Mobile 7
    elif (device.device_os, parse_version(device.device_os_version)) == (u'Windows Mobile OS', (7,)):
        style_group = 'smart'
    
    # Kindle - but only the Mobile Safari based ones... unfortunately Wurfl seems
    # to think that version 3 still uses Netfront, so can't be clever here
    elif device.devid == 'amazon_kindle3_ver1' or 'amazon_kindle3_ver1' in device_parents[device.devid]:
        style_group = 'smart'
    
    # Desktop browsers
    elif 'generic_web_browser' in device_parents[browser.devid]:
        style_group = 'smart'
        use_slippy_maps = True

    # All Others
    else:
        style_group = "dumb"
        use_javascript = False
    
    return {
        'style_group': '%s' % style_group,
        'use_javascript': use_javascript,
        'use_slippy_maps': use_javascript and use_slippy_maps,
    }

def wurfl_device(request):
    return {
        'browser': request.browser,
        'device': request.device,
        'map_width': request.map_width,
        'map_height': request.map_height,
    }