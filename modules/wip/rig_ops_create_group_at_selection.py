import maya.cmds as cmds


# create group that matches location of a given object
def main():
    RigOps_createGroupatSelection()


class RigOps_createGroupatSelection(object):

    def __init__(self):
        sel = cmds.ls(sl=1)
        selXform = cmds.xform(sel, ws=True, q=True, m=True)

        GRP = cmds.createNode("transform", name=str(sel[0]) + "_GRP")
        cmds.xform(GRP, m=selXform)

        if cmds.listRelatives(sel, p=True):
            cmds.select(sel)
            target = cmds.pickWalk(d="UP")
            cmds.parent(GRP, target)
            cmds.parent(sel, GRP)
        else:
            cmds.parent(sel, GRP)
