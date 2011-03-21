device_parents = {}
try:
    from molly.wurfl import wurfl_data
except ImportError:
    pass
else:

    def get_parents(device):
        if device == 'root' or device is None:
            return []
        device = unicode(device)
        try:
            return device_parents[device]
        except KeyError:
            device_parents[device] = [device] + get_parents(wurfl_data.devices.select_id(device).fall_back)
            return device_parents[device]

    for device in wurfl_data.devices:
        if not device in device_parents:
            device_parents[device] = get_parents(device)
        
    # Convert our lists to frozensets for efficiency's sake
    for key in device_parents:
        device_parents[key] = frozenset(device_parents[key])
