import maya.cmds as cmds

import logging

logger = logging.getLogger(__name__)


def create_JNT_LOC():
    # create a jnt and locator at point of selected object

    sel = cmds.ls(sl=1)
    logger.debug(sel)

    LOC = cmds.spaceLocator(p=(0, 0, 0))

    cmds.select(sel, LOC)

    constLoc = cmds.pointConstraint(sel, LOC, o=(0, 0, 0), w=1)
    cmds.delete(constLoc)
    cmds.select(cl=1)

    JNT = cmds.joint(p=(0, 0, 0))

    constJNT = cmds.pointConstraint(LOC, JNT, o=(0, 0, 0), w=1)
    cmds.delete(constJNT)
    cmds.parent(JNT, LOC)
    cmds.select(LOC)


def main(*args):
    create_JNT_LOC()


if __name__ == "__main__":
    main()
