import jinja2
import jinja2.environment
import jinja2.utils

class Environment(jinja2.Environment):

    def __init__(self, *args, **kwargs):
        writer = kwargs.pop("writer", "pwt.jinja2js.jscompiler.Concat")
        self.writer = jinja2.utils.import_string(writer)

        super(Environment, self).__init__(*args, **kwargs)


def create_environment(packages = [], autoescape = [], extensions = [], writer = "pwt.jinja2js.jscompiler.Concat"):
    loaders = []
    for package in packages:
        loaders.append(jinja2.PackageLoader(*package.split(":")))

    if len(loaders) == 1:
        loader = loaders[0]
    else:
        loader = jinja2.ChoiceLoader(loaders)

    # autoescape, turn off by default no.
    if autoescape:
        auto_templates = []
        for auto in autoescape:
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

    extensions.append("pwt.jinja2js.jscompiler.Namespace")

    return Environment(
        loader = loader, extensions = extensions, autoescape = autoescape,
        writer = writer)
