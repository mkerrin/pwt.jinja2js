"""
XXX - remove this and just use an unmodified Jinja2 environment. This
would keep things simple.
"""
import jinja2
import jinja2.environment
import jinja2.utils

class Environment(jinja2.Environment):

    def __init__(self, *args, **kwargs):
        writer = kwargs.pop("writer", "pwt.jinja2js.jscompiler.Concat")
        self.writer = jinja2.utils.import_string(writer)
        self.js_func_aliases = kwargs.pop("js_func_aliases", {})
        self.add_compiler_annotations = kwargs.pop(
            "add_compiler_annotations", False)
        self.strip_html_whitespace = kwargs.pop(
            "strip_html_whitespace", False)
        self.js_indentation = kwargs.pop("js_indentation", "    ")

        super(Environment, self).__init__(*args, **kwargs)


def create_environment(packages = [], directories = [], autoescape = [], extensions = [], writer = "pwt.jinja2js.jscompiler.Concat", **kwargs):
    loaders = []
    for package in packages:
        loaders.append(jinja2.PackageLoader(*package.split(":")))

    if directories:
        loaders.append(jinja2.FileSystemLoader(directories))

    if len(loaders) == 1:
        loader = loaders[0]
    else:
        loader = jinja2.ChoiceLoader(loaders)

    # autoescape, turn off by default no.
    if isinstance(autoescape, bool):
        # No changes necessary
        pass
    elif autoescape:
        auto_templates = []
        for auto in autoescape:
            if auto.lower() == "false":
                autoescape = False
                break
            if auto.lower() == "true":
                autoescape = True
                break

            auto_templates.append(auto)
        else:
            # Don't override the autoescape variable
            # XXX - this is not tested at the moment!!!
            def autoescape(template_name):
                if template_name in auto_templates:
                    return True

                if template_name[0] == "/" and template_name[1:] in auto_templates:
                    return True
                if template_name[0] != "/" \
                       and template_name + "/" in auto_templates:
                    return True

                return False
    else:
        autoescape = False

    extensions.append("pwt.jinja2js.jscompiler.Namespace")

    return Environment(
        loader = loader,
        extensions = extensions,
        autoescape = autoescape,
        writer = writer,
        **kwargs
        )


def parse_environment(config):
    return create_environment(
        packages = config.get("packages", "").split(),
        directories = config.get("directories", "").split(),
        autoescape = config.get("autoescape", "").split(),
        writer = config.get("writer", "pwt.jinja2js.jscompiler.StringBuilder")
        )
