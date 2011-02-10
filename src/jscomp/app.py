import webob
import webob.dec

from jinja import PackageLoader, Environment

@webob.dec.wsgify.middleware
def main(request, config, **kwargs):
    env = Environment(loader = PackageLoader("jscomp", "templates"))
    template = env.get_template("hello.html")
    return webob.Response(template.render())
