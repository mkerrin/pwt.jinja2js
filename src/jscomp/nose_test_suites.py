from nose.plugins import Plugin

class Suites(Plugin):

    name = "test-suites"

    interactive = True

    def options(self, parser, env):
        super(Suites, self).options(parser, env)

        parser.add_option(
            "--test-suites-include",
            dest = "suites",
            action = "append",
            help = "Load tests from directory")

    def configure(self, options, conf):
        super(Suites, self).configure(options, conf)
        self.suites = options.suites

    def prepareTestLoader(self, loader):
        self.loader = loader

    def loadTestsFromModule(self, module, path = None):
        tests = self.loader.suiteClass([])
        for suite in self.suites:
            if not suite.startswith(module.__name__):
                continue

            try:
                s = getattr(module, suite[len(module.__name__) + 1:])
            except AttributeError:
                # no attributes
                continue

            tests.addTest(s())

        return tests
