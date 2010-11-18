from __future__ import absolute_import
import socket, struct, logging, threading, select, pickle, time, os
import logging.handlers

try:
    import cStringIO
except ImportError:
    import StringIO

import config

logger = logging.getLogger('mobile_portal.logger')

class SocketServer(object):
    def __init__(self):
        
        self.close_down_event = threading.Event()

        self.listener_thread = threading.Thread(target=self.listener)
        self.listener_thread.start()

    def listener(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        while not self.close_down_event.is_set():
            try:
                sock.bind(('localhost', logging.handlers.DEFAULT_TCP_LOGGING_PORT))
            except socket.error:
                time.sleep(1)
            else:
                break
                
        sock.listen(1)
        
        connections = set()
        buffers = {}
        expected = {}
        
        while not self.close_down_event.is_set():
        
            rlist = [sock] + list(connections)
            ready, _, _ = select.select(rlist, [], [], 1)
            if not ready:
                continue

            for conn in ready:

                if conn is sock:
                    new_conn, addr = sock.accept()
                    connections.add(new_conn)
                    buffers[new_conn] = ""
                    expected[new_conn] = None
                    continue

                
                new_data = conn.recv(1024)
                if new_data:
                    buffers[conn] += new_data
                else:
                    connections.remove(conn)
                    conn.close()
                    continue
                    
                while True:
                    if expected[conn] is None and len(buffers[conn]) >= 4:
                        expected[conn], = struct.unpack('!l', buffers[conn][:4])
                        buffers[conn] = buffers[conn][4:]
                    
                    if expected[conn] is not None and len(buffers[conn]) >= expected[conn]:
                        pickled = buffers[conn][:expected[conn]]
                        buffers[conn] = buffers[conn][expected[conn]:]
                        expected[conn] = None
                    else:
                        break
                        
                    try:
                        unpickled = pickle.loads(pickled)
                    except Exception, e:
                        logger.error('Malformed log message')
                    else:
                        try:
                            record = logging.makeLogRecord(unpickled)
                            given_logger = logging.getLogger(record.name)
                            given_logger.handle(record)
                        except Exception:
                            logger.exception("Couldn't handle LogRecord")
                    
        
        sock.close()
        for conn in connections:
            conn.close()

    def close_down(self):
        self.close_down_event.set()
        self.listener_thread.join()
        
if __name__ == '__main__':
    os.environ['MP_LOG_TO_SOCKET'] = 'no'
    config.initialise_logging()
    server = SocketServer()
    
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        server.close_down()