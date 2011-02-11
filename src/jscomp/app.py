import webob
import webob.dec

from jinja2 import PackageLoader, Environment

env = Environment(loader = PackageLoader("jscomp", "templates"))
env.compile_templates("archive", zip = None)

@webob.dec.wsgify.middleware
def main(request, config, **kwargs):
    template = env.get_template("hello.html")
    return webob.Response(template.render())
