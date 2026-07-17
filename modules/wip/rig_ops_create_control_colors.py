import maya.cmds as cmds

import logging

logger = logging.getLogger(__name__)

# Yellow is 17
# Blue is 18
# Red is 13


def main():
    RigOps_createContolColors()


class RigOps_createContolColors(object):

    def __init__(self):
        cmds.pickWalk(d="DOWN")

        sel = cmds.ls(sl=True, s=True)

        logger.debug(sel)

        for i in sel:
            cmds.setAttr(i + ".overrideEnabled", 1)
            cmds.setAttr(i + ".overrideColor", 18)
