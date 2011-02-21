import webob
import webob.dec

import jinja2

class main(object):

    def __init__(self, *args, **kwargs):
        loaders = []
        for package in kwargs["packages"].split():
            loaders.append(jinja2.PackageLoader(*package.split(":")))

        if len(loaders) == 1:
            loader = loaders[0]
        else:
            loader = jinja2.ChoiceLoader(loaders)

        self.env = jinja2.Environment(
            loader = loader,
            extensions = ["pwt.jscompiler.jscompiler.Namespace"])

    @webob.dec.wsgify
    def __call__(self, request):
        template = self.env.get_template("hello.html")
        return webob.Response(template.render(data = [1, 3, 5]))
