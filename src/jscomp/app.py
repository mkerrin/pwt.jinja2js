import webob
import webob.dec

@webob.dec.wsgify.middleware
def main(request, config, **kwargs):
    return webob.Response("Hello, world")
