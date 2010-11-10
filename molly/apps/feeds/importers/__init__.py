from base import BaseImporter
from daily_info import *
from generic_rss import *

__all__ = ['importers']

importers, locals_ = {}, locals().copy()
for name in locals_:
    klass = locals_[name]
    if not (isinstance(klass, type) and BaseImporter in klass.__mro__[1:]):
        continue
        
    importers[klass.slug] = klass()