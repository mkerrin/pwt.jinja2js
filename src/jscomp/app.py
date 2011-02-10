import webob
import webob.dec

@webob.dec.wsgify.middleware
def main(request, config):
    return webob.Response("Hello, world")
