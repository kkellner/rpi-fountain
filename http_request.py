# Fountain project
#
# http_request.py - handle http requests
#

import logging
import http.server
import socketserver
import json

fountain = None

class HttpServer():

    def __init__(self, _fountain):
        global fountain
        fountain = _fountain
        PORT = 80
        #Handler = http.server.SimpleHTTPRequestHandler(directory="/")
        #httpd = socketserver.TCPServer(("", PORT), Handler)
        socketserver.TCPServer.allow_reuse_address = True

        self.testvar = 1

        self.httpd = socketserver.TCPServer(
            ('0.0.0.0', PORT), GetRequestHandler)
        logging.info("serving at port: %d", PORT)

    def run(self):
        self.httpd.serve_forever(poll_interval=5)
        logging.info("after serve_forever")

    def shutdown(self):
        self.httpd.server_close()
        self.httpd._BaseServer__shutdown_request = True
        # httpd.shutdown()


# Docs: https://docs.python.org/3/library/http.server.html
class GetRequestHandler(http.server.SimpleHTTPRequestHandler):
    """
    Class for handling a request to the root path /
    """
    # def __init__(self, host_port_tuple, streamhandler, controllers):
    #    logging.info("init GetRequestHandler")

    def do_GET(self):

        #logging.info("testvar: %s" % self.server.testvar)

        if self.path == '/':
            value = fountain.water_level.getWaterDepth()
            if value is not None:
                data = "Water level: %.1f" % value
            else:
                data = "Water sensor not initialized"

            self.protocol_version = 'HTTP/1.1'
            self.send_response(200, 'OK')
            #self.send_header('Connection', 'Keep-Alive')
            self.send_header('Content-type', 'text/html')
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(bytes(data, 'utf-8'))
            return

        elif self.path == '/v1':

                # Create the response
            response = {
                'water_level': fountain.water_level,
                'customer_id': 345,
                'location_id': 456,
            }

            response['note_text'] = "example text"

            data = json.dumps(response)

            # Write the response
            self.protocol_version = 'HTTP/1.1'
            self.send_response(200, 'OK')
            self.send_header('Connection', 'Keep-Alive')
            self.send_header('Content-type', 'application/json')
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(bytes(data, 'utf-8'))
            return
        elif self.path == "/test":
             # serve the file!
            self.path = "testfile.txt"
            return http.server.SimpleHTTPRequestHandler.do_GET(self)

    def do_POST(s):
        print('-----------------------')
        print('POST %s (from client %s)' % (s.path, s.client_address))
        print(s.headers)
        content_length = int(s.headers['Content-Length'])
        post_data = json.loads(s.rfile.read(content_length))
        print(json.dumps(post_data, indent=4, sort_keys=True))
        s.send_response(200)
        s.end_headers()
