# Packages which Molly needs, but Pip can't handle
PIP_PACKAGES = [
    ('PyZ3950', 'git+http://github.com/oucs/PyZ3950.git'), # Custom PyZ3950, contains some bug fixes
    ('django-compress', 'git+git://github.com/mollyproject/django-compress.git#egg=django-compress'), # Fork of django-compress contains some extra features we need
    ('PIL', 'PIL'), # Because it doesn't install properly when called using setuptools...
]