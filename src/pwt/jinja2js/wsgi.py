import webob
import webob.dec

import jinja2

import jscompiler
import environment


class Resources(object):

    def __init__(self, *args, **kwargs):
        self.env = environment.parse_environment(kwargs)

    def compiler(self, node, env, path, filename):
        return jscompiler.generate(node, env, path, filename)

    @webob.dec.wsgify
    def __call__(self, request):
        path = request.path_info

        try:
            source, filename, uptodate = self.env.loader.get_source(
                self.env, path)
        except jinja2.TemplateNotFound:
            return webob.Response("Not found", status = 404)

        node = self.env._parse(source, path, filename)

        output = self.compiler(node, self.env, path, filename)

        return webob.Response(
            body = output, content_type = "application/javascript")


class ClosureResources(Resources):

    def compiler(self, node, env, path, filename):
        return jscompiler.generateClosure(node, env, path, filename)


class ConcatResources(Resources):

    def compiler(self, node, env, path, filename):
        return jscompiler.generateConcat(node, env, path, filename)
