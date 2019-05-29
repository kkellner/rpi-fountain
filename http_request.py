# Fountain project
#
# http_request.py - handle http requests
#

import logging
import http.server
import socketserver
import json


water_level = None

class HttpServer():

    def __init__(self, _water_level):
        global water_level 
        water_level = _water_level
        PORT = 80
        #Handler = http.server.SimpleHTTPRequestHandler(directory="/")
        #httpd = socketserver.TCPServer(("", PORT), Handler)
        socketserver.TCPServer.allow_reuse_address = True
        httpd = socketserver.TCPServer(('0.0.0.0', PORT), GetRequestHandler)
        logging.info("serving at port: %d", PORT)

        httpd.serve_forever(poll_interval=0.5)
        logging.info("after serve_forever")



# Docs: https://docs.python.org/3/library/http.server.html
class GetRequestHandler(http.server.SimpleHTTPRequestHandler):
    """
    Class for handling a request to the root path /
    """

    def do_GET(self):

        if self.path == '/':
            data = "Water level: %.1f" % water_level.getWaterDepth()
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
                'water_level': water_level,
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


