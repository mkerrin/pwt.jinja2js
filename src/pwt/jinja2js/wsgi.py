from cStringIO import StringIO
import webob
import webob.dec

import jinja2

import jscompiler
import environment

class JinjaEnvironment(object):

    def __init__(self, *args, **kwargs):
        self.env = environment.create_environment(
            packages = kwargs.get("packages", "").split(),
            autoescape = kwargs.get("autoescape", "").split(),
            writer = kwargs.get("writer", "pwt.jinja2js.jscompiler.StringBuilder"))


class Resources(JinjaEnvironment):

    def __init__(self, *args, **kwargs):
        super(Resources, self).__init__(*args, **kwargs)
        self.url = kwargs["url"]

    @webob.dec.wsgify
    def __call__(self, request):
        path = request.path[len(self.url):]

        try:
            source, filename, uptodate = self.env.loader.get_source(
                self.env, path)
        except jinja2.TemplateNotFound:
            return webob.Response("Not found", status = 404)

        node = self.env._parse(source, path, filename)

        output = jscompiler.generate(node, self.env, path, filename)

        return webob.Response(
            body = output, content_type = "application/javascript")
