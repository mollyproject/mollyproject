import wurfl

device_parents = {}

def get_parents(device):
    if device == 'root' or device is None:
        return []
    try:
        return device_parents[device]
    except KeyError:
        device_parents[device] = [device] + get_parents(wurfl.devices.select_id(device).fall_back)
        return device_parents[device]

for device in wurfl.devices:
    if not device in device_parents:
        device_parents[device] = get_parents(device)
        
# Convert our lists to frozensets for efficiency's sake
for key in device_parents:
    device_parents[key] = frozenset(device_parents[key])