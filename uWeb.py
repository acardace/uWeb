#!/usr/bin/python3.4

'''
 uWeb, a minimal WebServer written in Python.
 Copyright (C) 2014  Antonio Cardace.

 uWeb is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 uWeb is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program.  If not, see <http://www.gnu.org/licenses/>
'''

import http.server
import os
import sys
import copy

SERVER_NAME="uWeb 0.1"

def cgi_header(self):
    self.wfile.write( bytes( "HTTP/1.1 200 OK\n" ,"utf-8") )
    self.wfile.write( bytes( "Server: "+SERVER_NAME+"\n" ,"utf-8") )
    self.wfile.write( bytes("Date: "+self.date_time_string()+"\n","utf-8"))


def print_log(self):
    print(self.address_string()+" - - ["+self.log_date_time_string()+"] \""+self.command+" "+self.path+" "+self.request_version+"\" 200 -")


def cgi_env(self, scriptname):
    env = copy.deepcopy(os.environ)
    env['SERVER_SOFTWARE'] = self.version_string()
    env['SERVER_NAME'] = self.server.server_name
    env['GATEWAY_INTERFACE'] = 'CGI/1.1'
    env['SERVER_PROTOCOL'] = self.protocol_version
    env['SERVER_PORT'] = str(self.server.server_port)
    env['REQUEST_METHOD'] = self.command
    env['SCRIPT_NAME'] = scriptname
    env['REMOTE_ADDR'] = self.client_address[0]
    if self.headers.get('content-type') is None:
        env['CONTENT_TYPE'] = self.headers.get_content_type()
    else:
        env['CONTENT_TYPE'] = self.headers['content-type']
    length = self.headers.get('content-length')
    if length:
        env['CONTENT_LENGTH'] = length
    query = getQueries(self.path)
    if query:
        env['QUERY_STRING'] = query
    ua = self.headers.get('user-agent')
    if ua:
        env['HTTP_USER_AGENT'] = ua
    co = filter(None, self.headers.get_all('cookie', []))
    cookie_str = ', '.join(co)
    if cookie_str:
        env['HTTP_COOKIE'] = cookie_str
    return env

def local_path(path):
    i = path.find("?")

    if i> -1:
        local = "."+path[:i]
    else:
        local = "."+path
    return local

def getQueries(path):
    i = path.find("?")
    if i> -1:
        queryString = path[i+1:]
    else:
        return False
    return queryString

def run_cgi(self, toOpen):
    #look for queries
    env = cgi_env(self, toOpen)
    self.wfile.flush()
    pid = os.fork()
    if pid == 0:
        #prepare HEADER
        cgi_header(self)
        #LOG
        print_log(self)
        args = [toOpen]
        try:
            os.dup2( self.wfile.fileno() , 1)
            os.execve(toOpen , args, env)
            os._exit(0)
        except:
            os._exit(1)
    else:
        # Parent
        os.waitpid(pid, 0)
        self.wfile.flush()
        return

def serve_html_head(self, toOpen):
    f = open(toOpen, 'r')
    content = bytes( f.read(), 'utf-8')
    self.send_response(200)
    self.send_header("Server",SERVER_NAME )
    self.send_header("Content-type", "text/html; charset=utf-8")
    self.send_header("Content-Length",len(content) )
    self.end_headers()
    f.close()
    return content

def serve_html(self, toOpen):
    content = serve_html_head(self, toOpen)
    self.wfile.write( content )

def not_found(self):
    self.send_error( 404, self.responses[404][0])
    self.end_headers()

def show_help_message():
    print("""uWeb 0.1

    usage:
    uWeb PORT WEBSITE_DIR

    - PORT is the port on which you want to execute uWeb
    - WEBSITE_DIR is the directory in which you have chosen to put all your .html/.py files.
    """)

class HTTPhandler(http.server.BaseHTTPRequestHandler):
    def do_HEAD(self):
        toOpen = local_path(self.path)
        py_cgi = False

        if self.path == "/":
            if os.path.exists("index.htm"):
                toOpen = "index.htm"
            elif os.path.exists("index.html"):
                toOpen = "index.html"
        elif self.path.find(".py") > -1:
            py_cgi = True

        if os.path.exists(toOpen):
            #CGI
            if py_cgi == True:
                cgi_header(self)
                self.end_headers()
            #PLAIN HTML
            else:
                serve_html_head(self, toOpen)
        #The requested content does not exists
        else:
            not_found(self)

    def do_GET(self):
        toOpen = local_path(self.path)
        py_cgi = False

        if self.path == "/":
            if os.path.exists("index.htm"):
                toOpen = "index.htm"
            elif os.path.exists("index.html"):
                toOpen = "index.html"
        elif self.path.find(".py") > -1:
            py_cgi = True

        if os.path.exists(toOpen):
            #CGI
            if py_cgi == True:
                run_cgi(self, toOpen)
            #PLAIN HTML
            else:
                serve_html(self, toOpen)
        #The requested content does not exists
        else:
            not_found(self)

def runDaemon(server_class=http.server.HTTPServer, handler_class=HTTPhandler):
    if len(sys.argv) != 3:
        show_help_message()
        sys.exit()

    DEFAULT_DIR =sys.argv[2]
    PORT=int(sys.argv[1])
    server_addr = ("",PORT)
    httpd = server_class(server_addr, handler_class)
    os.chdir(DEFAULT_DIR)
    try:
        print("Starting uWeb up on port",PORT,"!")
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting uWeb down!")
        httpd.shutdown()

#MAIN
runDaemon()
