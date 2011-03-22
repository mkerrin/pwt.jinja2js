from cStringIO import StringIO
import webob
import webob.dec

import jinja2

import jscompiler

class JinjaEnvironment(object):

    def __init__(self, *args, **kwargs):
        loaders = []
        for package in kwargs["packages"].split():
            loaders.append(jinja2.PackageLoader(*package.split(":")))

        if len(loaders) == 1:
            loader = loaders[0]
        else:
            loader = jinja2.ChoiceLoader(loaders)

        # autoescape, turn off by default no.
        autoescape = kwargs.get("autoescape", "")
        if autoescape:
            auto_templates = []
            for auto in autoescape.split():
                if auto.lower() == "false":
                    autoescape = False
                    break
                if auto.lower() == "true":
                    autoescape = True
                    break

                auto_templates.append(auto)

            def autoescape(template_name):
                if template_name in auto_templates:
                    return True

                return False
        else:
            autoescape = False

        self.env = jinja2.Environment(
            loader = loader,
            extensions = ["pwt.jinja2js.jscompiler.Namespace"],
            autoescape = autoescape)

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

        stream = StringIO()
        jscompiler.generate(node, self.env, path, filename, stream)

        return webob.Response(
            body = stream.getvalue(), content_type = "application/javascript")
