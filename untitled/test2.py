#!/usr/bin/python
# from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
from http.server import BaseHTTPRequestHandler,HTTPServer
from socketserver import ThreadingMixIn
import json
import re
from urllib.parse import parse_qs
import cgi

PORT_NUMBER = 8090

# This class will handle any incoming request from
# a browser
class myHandler(BaseHTTPRequestHandler):


    # Handler for the GET requests
    def do_GET(self):

        print('Get request received')
        if None != re.search('/api/v1/getrecord/*', self.path):
        ## 북마크 기능 : F11, 북마크 보기 : Shift + F11
        ## 디버깅 : Alt + Shift + F9
        ## 그냥 실행 : Ctrl + Shift + F10
        ## 함수 선언부로 가기 : Ctrl + B

            recordID = (self.path.split('/')[-1]).split('?')[-1]
            recordID2 = recordID.split('&')
            city = recordID2[0].split('=')[-1]
            zipcode = recordID2[1].split('=')[-1]
            mobile = recordID2[2].split('=')[-1]
            nickname = recordID2[3].split('=')[-1]
            print("recordID = ", recordID)
            if True :
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                # Send the html message
                self.wfile.write(bytes("<html><head><title>Title goes here.</title></head>", "utf-8"))
                self.wfile.write(bytes("<body><p>This is a test.</p>", "utf-8"))
                self.wfile.write(bytes("<p>City : %s</p>" % city, "utf-8"))
                self.wfile.write(bytes("<p>Zipcode : %s</p>" % zipcode, "utf-8"))
                self.wfile.write(bytes("<p>Mobile : %s</p>" % mobile, "utf-8"))
                self.wfile.write(bytes("<p>Nickname : %s</p>" % nickname, "utf-8"))
                self.wfile.write(bytes("<p>You accessed path: %s</p>" % self.path, "utf-8"))
                self.wfile.write(bytes("</body></html>", "utf-8"))

            else:
                self.send_response(400, 'Bad Request: record does not exist')
                self.send_header('Content-Type', 'application/json')
                self.end_headers()


try:

    # Create a web server and define the handler to manage the
    # incoming request
    server = HTTPServer(('', PORT_NUMBER), myHandler)
    print(HTTPServer.mro())
    print ('Started httpserver on port ' , PORT_NUMBER)

    # Wait forever for incoming http requests
    server.serve_forever()

except KeyboardInterrupt:
    print ('^C received, shutting down the web server')
    server.socket.close()
