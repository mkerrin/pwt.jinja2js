import doctest
import unittest
import zc.buildout.tests
import zc.buildout.testing
import sys
import os.path

# Import the depswrite and source from closure-library checkout
old_path = sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), "build"))
import depstree_test
import source_test
# reset the path
sys.path = sys.path[:-1]

def setUp(test):
    if not isinstance(test, doctest.DocTest):
        return

    zc.buildout.testing.buildoutSetUp(test)
    zc.buildout.testing.install_develop("pwt.recipe.closurebuilder", test)


def suite():
    suite = unittest.TestSuite((
        doctest.DocFileTest(
            "README.txt",
            setUp = setUp,
            tearDown = zc.buildout.testing.buildoutTearDown,
            ),
        unittest.makeSuite(depstree_test.DepsTreeTestCase),
        unittest.makeSuite(source_test.SourceTestCase),
        ))

    return suite


if __name__ == "__main__":
    unittest.main(defaultTest = "test_suite")
