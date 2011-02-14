from cStringIO import StringIO
import webob
import webob.dec

import jinja2

import jscompiler

class Resources(object):

    def __init__(self, *args, **kwargs):
        self.url = kwargs["url"]

        loaders = []
        for package in kwargs["packages"].split():
            loaders.append(jinja2.PackageLoader(*package.split(":")))

        if len(loaders) == 1:
            loader = loaders[0]
        else:
            loader = jinja2.ChoiceLoader(loaders)

        self.env = jinja2.Environment(
            loader = loader, extensions = ["jscomp.jscompiler.Namespace"])

    @webob.dec.wsgify
    def __call__(self, request):
        path = request.path[len(self.url):]

        try:
            source, filename, uptodate = self.env.loader.get_source(self.env, path)
        except jinja2.TemplateNotFound:
            return webob.Response("Not found", status = 404)

        node = self.env._parse(source, path, filename)

        stream = StringIO()
        jscompiler.generate(node, self.env, path, filename, stream)

        return webob.Response(
            body = stream.getvalue(), content_type = "application/javascript")
