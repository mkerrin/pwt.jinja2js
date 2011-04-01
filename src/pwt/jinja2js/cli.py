import optparse
import os.path
import string
import sys

import environment
import jscompiler

def get_output_filename(output_format, filename):
    filename_template = string.Template(output_format)

    output_filename = filename_template.substitute({
        "INPUT_FILE_NAME": os.path.basename(filename),
        "INPUT_FILE_NAME_NO_EXT": os.path.splitext(os.path.basename(filename))[0],
        "INPUT_DIRECTORY": os.path.dirname(filename),
        # "INPUT_PREFIX": 
        })

    return output_filename


writerclasses = {
    "stringbuilder": "pwt.jinja2js.jscompiler.StringBuilder",
    "concat": "pwt.jinja2js.jscompiler.Concat",
    }


def main(args = None, output = None):
    if output is None:
        output = sys.stdout

    parser = optparse.OptionParser()
    # closure template options that we support
    parser.add_option(
        "--outputPathFormat", dest = "output_format",
        help = "A format string that specifies how to build the path to each output file. You can include literal characters as well as the following $variables: ${INPUT_FILE_NAME}, ${INPUT_FILE_NAME_NO_EXT}, and ${INPUT_DIRECTORY}.",
        metavar = "OUTPUT_FORMAT")

    # jinja2js specific options
    parser.add_option(
        "--packages", dest = "packages",
        default = [], action = "append",
        help = "List of packages to look for template files.",
        metavar = "PACKAGE")

    parser.add_option(
        "--codeStyle", choices = ["stringbuilder", "concat"],
        dest = "codeStyle", default = "concat", type = "choice",
        help = "The code style to use when generating JS code. Either `stringbuilder` or `concat` styles.")

    options, files = parser.parse_args(args)

    outputPathFormat = options.output_format
    if not outputPathFormat:
        parser.print_help(output)
        return 1

    env = environment.create_environment(
        options.packages,
        writer = writerclasses[options.codeStyle])

    for filename in files:
        name = os.path.basename(filename)
        node = env._parse(open(filename).read(), name, filename)

        output = jscompiler.generate(node, env, name, filename)

        output_filename = get_output_filename(options.output_format, filename)
        open(output_filename, "w").write(output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
