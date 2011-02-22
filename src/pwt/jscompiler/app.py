import webob
import webob.dec

import jinja2

class main(object):

    def __init__(self, *args, **config):
        loaders = []
        for package in config.pop("packages").split():
            loaders.append(jinja2.PackageLoader(*package.split(":")))

        if len(loaders) == 1:
            loader = loaders[0]
        else:
            loader = jinja2.ChoiceLoader(loaders)

        self.env = jinja2.Environment(
            loader = loader,
            extensions = ["pwt.jscompiler.jscompiler.Namespace"])

        self.config = config

    @webob.dec.wsgify
    def __call__(self, request):
        path = request.path.split("/")[1]
        if not path:
            path = "index.html"

        template = self.env.get_template(path)
        return webob.Response(template.render(**self.config))
