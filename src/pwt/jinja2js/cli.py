import optparse
import os.path
import string
import sys

import soy_wsgi
import jscompiler

def main(args = None):
    import pdb
    pdb.set_trace()
    parser = optparse.OptionParser()
    # closure template options that we support
    parser.add_option("--outputPathFormat", dest = "output_format",
                      help = "A format string that specifies how to build the path to each output file.",
                      metavar = "OUTPUT_FORMAT")

    # jinja2js specific options
    parser.add_option("--packages", dest = "packages",
                      default = [], action = "append",
                      help = "List of packages to look for template files",
                      metavar = "PACKAGE")

    options, files = parser.parse_args()

    outputPathFormat = options.output_format
    if not outputPathFormat:
        parser.print_help()
        sys.exit(0)

    env = soy_wsgi.create_environment(options.packages)

    o_template = string.Template(options.output_format)

    for filename in files:
        name = os.path.basename(filename)
        node = env._parse(open(filename).read(), name, filename)

        output = jscompiler.generate(node, env, name, filename)

        output_filename = o_template.substitute({
            "INPUT_FILE_NAME": filename,
            "INPUT_FILE_NAME_NO_EXT": os.path.splitext(filename)[0],
            "INPUT_DIRECTORY": os.path.dirname(filename),
            # "INPUT_PREFIX": 
            })
        open(output_filename, "w").write(output)


if __name__ == "__main__":
    main()
