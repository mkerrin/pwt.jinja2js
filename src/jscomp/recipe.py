import re
import os.path
import tempfile

import pwt.recipe.closurebuilder
from pwt.recipe.closurebuilder import depswriter
from pwt.recipe.closurebuilder import treescan
from pwt.recipe.closurebuilder import source

import jinja2.parser
import jinja2.environment
import jinja2.visitor

import jscompiler

class Source(jinja2.visitor.NodeVisitor):

    def __init__(self, path):
        self.env = jinja2.environment.Environment(
            extensions = ["jscomp.jscompiler.Namespace"]
            )

        self.source = source.GetFileContents(path)
        self.node = self.env._parse(self.source, os.path.basename(path), path)

        self._path = path

        self.provides = set([])
        # Manually added
        self.requires = set(["soy"])
        self.scan()

        self.tmp = None

    def GetSourcePath(self):
        jscode = jscompiler.generate(
            self.node, self.env, os.path.basename(self._path), self._path)
        self.tmp = tempfile.NamedTemporaryFile(delete = False)
        self.tmp.write(jscode)
        self.tmp.close()

        return jscode, self.tmp.name

    def __del__(self):
        # Remove any temporary files when the program is finishing
        if self.tmp:
            os.remove(self.tmp.name)

    def GetPath(self):
        return self._path

    def visit_NamespaceNode(self, node):
        self.provides.add(node.namespace.encode("utf-8"))

    def scan(self):
        self.visit(self.node)


class Deps(pwt.recipe.closurebuilder.Deps):

    def __init__(self, buildout, name, options):
        super(Deps, self).__init__(buildout, name, options)

        self.extension = options.get("extension", ".tmpl")
        self.extension_filter = re.compile(r"^.+\.%s" % self.extension)

    def get_sources(self, root, prefix = ""):
        start_wd = os.getcwd()
        os.chdir(root)

        path_to_source = {}
        for path in treescan.ScanTree(".", path_filter = self.extension_filter):
            prefixed_path = depswriter._NormalizePathSeparators(
                os.path.join(prefix, path))
            path_to_source[prefixed_path] = Source(
                os.path.join(start_wd, root, path))

        os.chdir(start_wd)

        return path_to_source

    def find_path_to_source(self):
        path_to_source = super(Deps, self).find_path_to_source()

        for root in self.options.get("roots", "").split("\n"):
            if not root:
                continue

            path_to_source.update(self.get_sources(root))

        for root_with_prefix in \
                self.options.get("root_with_prefix", "").split("\n"):
            if not root_with_prefix:
                continue

            root, prefix = depswriter._GetPair(root_with_prefix)
            path_to_source.update(self.get_sources(root, prefix))

        return path_to_source


class Compile(pwt.recipe.closurebuilder.Deps):

    pass
