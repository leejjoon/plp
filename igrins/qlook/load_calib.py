import os
import sys


def add_path():
    p = "/home/jjlee/work/igrins/plp_jjlee"
    if p not in sys.path:
        sys.path.append(p)


add_path()


def load_aperture(caldb, basename):
    """
    for orders that wvlsols are derived.
    """

    centroid = caldb.load_resource_for(basename, "aperture_definition")

    bottomup_solutions = centroid["bottom_up_solutions"]

    orders = caldb.load_resource_for(basename, "orders")["orders"]

    from igrins.libs.apertures import Apertures
    ap = Apertures(orders, bottomup_solutions)

    return ap


def get_calibs(band):

    config_name = os.path.join("/home/jjlee/work/igrins/plp_jjlee",
                               "recipe.config")

    from igrins.libs.recipe_helper import RecipeHelper

    utdate = "20170314"
    recipe_name = ""

    helper = RecipeHelper(config_name, utdate, recipe_name)

    caldb = helper.get_caldb()

    basename = (band, "1")

    ap = load_aperture(caldb, basename)
    ordermap = caldb.load_resource_for(basename, "ordermap")
    slitposmap = caldb.load_resource_for(basename, "slitposmap")

    return ap, ordermap, slitposmap


if __name__ == "__main__":
    ap, ordermap, slitposmap = get_calibs("K")
