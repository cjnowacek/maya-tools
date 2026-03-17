import maya.cmds as cmds
import maya.mel as mel

#Yellow is 17
#Blue is 18
#Red is 13


def main():
    RigOps_createContolColors()


class RigOps_createContolColors(object):

    def __init__(self):
        cmds.pickWalk(d='DOWN')

        sel = cmds.ls(sl=True, s=True)

        print(sel)

        for i in sel:
            cmds.setAttr(i + '.overrideEnabled', 1)
            cmds.setAttr(i + '.overrideColor', 18)
