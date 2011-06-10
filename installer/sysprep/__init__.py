# Try and detect which distro we are, and import appropriately. If we don't
# support this distro, then raise NotImplementedError

import platform

if not hasattr(platform, 'linux_distribution'):
    if not hasattr(platform, 'dist'):
        distribution, distribution_version, distribution_id = (None, None, None)
    else:
        distribution, distribution_version, distribution_id = platform.dist()
else:
    distribution, distribution_version, distribution_id = platform.linux_distribution()

if distribution == 'Fedora':
    from installer.sysprep.fedora import *
elif distribution == 'redhat':
    from installer.sysprep.rhel import *
elif distribution == 'Ubuntu':
    if distribution_version == '10.04':
        from installer.sysprep.ubuntu_lucid import *
    elif distribution_version == '10.10':
        from installer.sysprep.ubuntu_maverick import *
    else:
        raise NotImplementedError()
else:
    raise NotImplementedError()