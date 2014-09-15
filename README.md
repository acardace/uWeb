uWeb
====

uWeb, a minimal WebServer written in Python.

uWeb supports almost any kind of interpreted or compiled CGI scripts (no PHP), uses the HTTP/1.1 protocol and GET,HEAD and POST requests are supported.

##This is how to use it:

- `./uWeb 8080 web/`


In the above example uWeb will be started on the port **8080** and it will serve files contained in the **web/** directory.


###Warning!!!
All of this has been developed for personal use, therefore this is incomplete and does not adhere completely to the HTTP standards.

I'm sharing this piece of code with the hope that it will be useful to someone or just to give out a (mini) practical guide to better understand how webservers are done and how the HTTP protocol works.

Have fun :)

-------------------------------------------------
Copyright **Antonio Cardace** 2014, anto.cardace@gmail.com
