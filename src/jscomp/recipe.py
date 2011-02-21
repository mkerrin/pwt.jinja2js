import pwt.recipe.closurebuilder

class Deps(pwt.recipe.closurebuilder.Deps):

    def find_path_to_source(self):
        path_to_source = super(Deps, self).find_path_to_source()
