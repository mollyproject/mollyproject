from __future__ import with_statement
try:
    from multiprocessing.connection import Listener
    from multiprocessing.managers import BaseManager, BaseProxy
except ImportError:
    from processing.connection import Listener
    from processing.managers import BaseProxy, BaseManager, CreatorMethod
import sys
from threading import Thread, Lock, Event
from datetime import datetime, timedelta
from time import sleep

from PyZ3950.zoom import Query
from PyZ3950.z3950 import Client
from PyZ3950 import z3950
from PyZ3950.zmarc import MARC, MARC8_to_Unicode

import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'mobile_portal.settings'

from django.conf import settings

class OLISConnection(object):
    def __init__(self):
        self.connection = Client(
            getattr(settings, 'Z3950_HOST'),
            getattr(settings, 'Z3950_PORT', 210),
            implementationId = 'PyZ3950/m.ox.ac.uk',
        )
        self.databaseName = getattr(settings, 'Z3950_DATABASE')
        self.connection.default_recordSyntax = z3950.Z3950_RECSYN_USMARC_ov
        self.results = None
        self.query = None
        self.control_numbers = {}
        
    def search(self, query):
        self.connection.dbnames = [self.databaseName]
        recv = self.connection.search_2(query.query)
        self.results = recv
        return recv
        
    def close(self):
        self.connection.close()
        
    def present(self, *args, **kwargs):
        return self.connection.present(*args, **kwargs)
 

class ResultsProxy(BaseProxy):
    def __len__(self):
        return self._callmethod('__len__')
    def __getitem__(self, index):
        return self._callmethod('__getitem__', [index])
    def __iter__(self):
        return self._callmethod('__iter__')



        
class Z3950ConnectionManager(object):
    def __init__(self):
        self.Search = self.get_search_cls()
        self.translator = MARC8_to_Unicode()
        
    def log(self, **kwargs):
         with self.log_lock:
            print kwargs
        
    def purge_connections(self):
        try:
            while True:
                with self.connection_lock:
                    for sessionkey, connection in self.connections.items():
                        if (datetime.now() - connection.last_used).seconds > 300:
                            del self.connections[sessionkey]
                            connection.close()
                            print "Closed connection for sessionkey %s" % sessionkey
                        else:
                            print "Sessionkey %s is %d seconds old " % (sessionkey, (datetime.now() - connection.last_used).seconds)
                for i in range(10):
                    sleep(1)
                    if self.we_are_going_now.isSet():
                        raise SystemExit
        except SystemExit:
            pass

    def get_search_cls(cm):
        class Search(object):
            def __init__(self, sessionkey, query):
                print "Woo! Search!"
                with cm.connection_lock:
                    if not sessionkey in cm.connections:
                        cm.connections[sessionkey] = OLISConnection()
                        
                    connection = cm.connections[sessionkey]
                    
                connection.last_used = datetime.now()
                    
                self.connection, self.sessionkey = connection, sessionkey

                if query.startswith('(1,1032)=') and query[9:] in connection.control_numbers:
                    self.offset, self.count = connection.control_numbers[query[9:]], 1
                else:
                    if connection.query != query:
                        self.perform_query(query)
                        connection.query = query
                    self.results = connection.results
                    self.offset, self.count = 0, self.results.resultCount
                    
            
            @staticmethod
            def marc_to_unicode(x):
                translator = cm.translator
                def f(y):
                    if isinstance(y, dict):
                        return dict((k,f(y[k])) for k in y)
                    elif isinstance(y, tuple):
                        return tuple(f(e) for e in y)
                    elif isinstance(y, list):
                        return [f(e) for e in y]
                    elif isinstance(y, str):
                        if any((ord(c) > 127) for c in y):
                            return translator.translate(y)
                        else:
                            return y.decode('ascii')
                return f(MARC(x).fields)

                        
            def perform_query(self, query):
                self.query = Query('CCL', query)
                self.results = self.connection.search(self.query)
                self.control_numbers = {}
                cm.log(action="SEARCH",
                       query=query,
                       sessionkey=self.sessionkey,
                       result_count=self.results.resultCount)
                        
            def __len__(self):
                self.connection.last_used = datetime.now()
                return self.count
                
            def __getitem__(self, index):
                self.connection.last_used = datetime.now()
                if isinstance(index, slice):
                    index = slice(index.start+self.offset, index.stop+self.offset)
                    if index.start >= index.stop or index.start >= len(self):
                        return []
                    count = min(index.stop, len(self)) - index.start
                    results = self.connection.present(start=index.start, count=count)
                    results = [e.record[1].encoding[1] for e in results.records[1]]
                    results = map(Search.marc_to_unicode, results)
                    self.update_control_numbers(index.start, results)

                    cm.log(action="PRESENT",
                           sessionkey=self.sessionkey,
                           start=index.start,
                           count=count,
                           lcn=None if count != 1 else results[0][1][0][6:])

                    return results
                else:
                    return self[index:index+1][0]

            def update_control_numbers(self, start, results):
                for i, result in enumerate(results):
                    self.connection.control_numbers[result[1][0][6:]] = i + start

            def __iter__(self):
                def gen():
                    buffer, i = [], 0
                    while i < len(self):
                        if not buffer:
                            buffer += self[i:i+10]
                        yield buffer.pop(0)
                        i += 1
                    raise StopIteration
                return gen()

        return Search
     
    def serve_forever(self):
        self.connections = {}
        self.connection_lock = Lock()
        self.log_lock = Lock()
        
        self.we_are_going_now = Event()
        self.connection_purger = Thread(target=self.purge_connections)
        self.connection_purger.start()
        

                
    def leaving(self):
        self.we_are_going_now.set()

zcm = Z3950ConnectionManager()

class Z3950Manager(BaseManager):
    def __init__(self, address=None, authkey=None):
                                 
        super(Z3950Manager, self).__init__(
            ('localhost', settings.Z3950_CONN_MANAGER_LISTEN_PORT),
            authkey=settings.Z3950_CONN_MANAGER_AUTHKEY)

        
        print "Here"

    def serve_forever(self):
        self.zcm.serve_forever()
        try:
            self.get_server().serve_forever()
        except:
            super(Z3950Manager, self).serve_forever()
        self.zcm.leaving()
        
    if sys.version_info < (2, 6):
        search = CreatorMethod(
            zcm.Search,
            proxytype=ResultsProxy,
            exposed=(
                '__len__',
                '__getitem__',
                '__iter__',
            )
        )
        
        @classmethod
        def from_address(cls):
            return super(cls, cls).from_address(
                address=('localhost', settings.Z3950_CONN_MANAGER_LISTEN_PORT),
                authkey=settings.Z3950_CONN_MANAGER_AUTHKEY)

if sys.version_info >= (2, 6):
    Z3950Manager.register(
        'search',
        zcm.Search,
        proxytype=ResultsProxy,
        exposed=(
            '__len__',
            '__getitem__',
            '__iter__',
        )
    )

if __name__ == '__main__':
    manager = Z3950Manager()
    manager.zcm = zcm
    
    manager.serve_forever()
    

