from maya import cmds as mc
from maya import mel

from modules.ThirdParty import zbw_control_shapes as zbw_con

import logging

logger = logging.getLogger(__name__)

jointLocations = []


def buildControls():

    sel = mc.ls(sl=1)

    this = mc.curve(n="{}".format(sel[0]), d=1, p=zbw_con.shapes["cube"])

    mc.select()

    mel.eval("MatchTransform;")

    logger.debug(sel)


def main(*args):
    buildControls()


if __name__ == "__main__":
    main()
