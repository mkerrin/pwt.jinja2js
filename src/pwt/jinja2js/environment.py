import jinja2

def create_environment(packages = [], autoescape = [], extensions = []):
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

    return jinja2.Environment(
        loader = loader, extensions = extensions, autoescape = autoescape)
