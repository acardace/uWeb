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
import mimetypes

SERVER_NAME="uWeb 0.2"
PROT_VERSION="HTTP/1.1"
BLOCK_SIZE=1024

def look_for_redirect(content):
    i = content.lower().find(b"location:")
    if i > -1:
        return True
    else:
        return False

def cgi_header(self, content=None):
    if content!= None:
        redirect = look_for_redirect( str(content).encode('utf-8') )
    if not redirect:
        self.wfile.write( bytes( self.protocol_version+" 200 OK\n" ,"utf-8") )
    else:
        self.wfile.write( bytes( self.protocol_version+" 303 See other\n" ,"utf-8") )
    self.wfile.write( bytes( "Server: "+self.server_version+"\n" ,"utf-8") )
    self.wfile.write( bytes("Date: "+self.date_time_string()+"\n","utf-8"))


def print_log(self):
    print(self.address_string()+" - - ["+self.log_date_time_string()+"] \""+self.command+" "+self.path+" "+self.request_version+"\" 200 -")


def cgi_env(self, scriptname):
    env = copy.deepcopy(os.environ)
    env['SERVER_SOFTWARE'] = self.version_string()
    env['SERVER_NAME'] = self.server_version
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

def get_content_length(content):
    i = content.find(b"\n\n")
    return len(content[i+2:])

def run_cgi(self, toOpen):
    #look for queries
    env = cgi_env(self, toOpen)
    self.wfile.flush()
    #prepare pipe
    r,w = os.pipe()
    os.set_inheritable(w, True)
    pid = os.fork()
    if pid == 0:
        #LOG
        print_log(self)
        args = [toOpen]
        try:
            os.dup2( w , 1)
            os.dup2( self.rfile.fileno() , 0)
            os.execve(toOpen , args, env)
            os._exit(0)
        except:
            os._exit(1)
    else:
        # Parent
        os.waitpid(pid, 0)
        os.close(w)
        content = ""
        buf = os.read(r, BLOCK_SIZE).decode("utf-8")
        while buf != "":
            content += buf
            buf = os.read(r, BLOCK_SIZE).decode("utf-8")
        os.close(r)
        length =  str( get_content_length(content.encode("utf-8")))
        #prepare HEADER
        cgi_header(self, content)
        self.wfile.write( bytes("Content-Length: "+length+"\n", "utf-8") )
        self.wfile.write(content.encode("utf-8"))
        self.wfile.flush()
        return

def serve_head(self, toOpen, mime, encoding):
    f = open(toOpen, 'rb')
    content = f.read()
    self.send_response(200)
    if mime != None:
        self.send_header("Content-type", mime)
    self.send_header("Content-Length",len(content) )
    if encoding != None:
        self.send_header("Content-Encoding", encoding)
    self.end_headers()
    f.close()
    return content

def serve(self, toOpen, mime, encoding):
    content = serve_head(self, toOpen, mime, encoding)
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

def guess_type(path):
    (mimetype,encoding) = mimetypes.guess_type(path)
    return (mimetype,encoding)

class HTTPhandler(http.server.BaseHTTPRequestHandler):
    #to make self.rfile unbuffered, otherwise we would block while reading on it
    rbufsize=0

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
                self.wfile.write( bytes("\n","utf-8") )
            #PLAIN HTML
            else:
                mime,encoding = guess_type(toOpen)
                serve_head(self, toOpen, mime, encoding)
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
                mime, encoding = guess_type(toOpen)
                serve(self, toOpen, mime, encoding)
        #The requested content does not exists
        else:
            not_found(self)

    def do_POST(self):
       self.do_GET()

def runDaemon(server_class=http.server.HTTPServer, handler_class=HTTPhandler):
    if len(sys.argv) != 3:
        show_help_message()
        sys.exit()

    DEFAULT_DIR =sys.argv[2]
    PORT=int(sys.argv[1])
    server_addr = ("",PORT)
    httpd = server_class(server_addr, handler_class)
    #setting server options
    handler_class.server_version = SERVER_NAME
    handler_class.protocol_version = PROT_VERSION
    os.chdir(DEFAULT_DIR)
    try:
        print("Starting uWeb up on port",PORT,"!")
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting uWeb down!")
        httpd.shutdown()

#MAIN
runDaemon()
