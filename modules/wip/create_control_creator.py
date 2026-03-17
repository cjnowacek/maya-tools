"""
File: ControlCreator.py
Author: CJ Nowacek
Created Date: NA
Description: UI for creating controls at a position
"""

import maya.cmds as mc
import maya.mel as mel
import os

# TODO add different export types
# TODO add options for animation?


class ControlCreator(object):

    # constructor
    def __init__(self):

        self.window = "ToolOps_ControlCreator"
        self.title = "Control Creator"
        self.size = (400, 600)

        # close old window is open
        if mc.window(self.window, exists=True):
            mc.deleteUI(self.window, window=True)

        # create new window
        self.window = mc.window(self.window, title=self.title)

        mc.columnLayout(adjustableColumn=True)

        mc.text(self.title)
        mc.separator(height=20)

        self.mirror_ckb = mc.checkBox(label="Mirror", v=False)
        self.export_bn = mc.button(label="Create", command=self.run)
        mc.setParent("..")

        # display new window
        mc.showWindow()

    def MirrorControl(self):

        sel = mc.ls(sl=1)
        this = mc.createNode("transform", n="mirror group")
        newcon = mc.duplicate(sel, n=sel[0].replace("L_", "R_"))
        mc.parent(newcon, this)

        mc.xform(this, scale=[-1, 1, 1])
        mc.parent(newcon, world=True)
        mc.delete(this)
        mc.select(sel, newcon)

    def finalizeControl(self):

        sel = mc.ls(sl=1)

        for i in range(len(sel)):

            mat = mc.xform(sel[i], q=True, m=True, ws=True)
            grp = mc.createNode("transform", n=sel[i].replace("_CON", "_GRP"))
            off = mc.createNode("transform", n=sel[i].replace("_CON", "_OFF"))
            mc.parent(off, grp)
            const = mc.parentConstraint(sel[i], grp, mo=False)
            mc.delete(const)
            print(sel)
            mc.parent(sel[i], off)

            if mc.objExists("CON_controls"):
                pass
            else:
                mc.createNode("transform", n="CON_controls")

            mc.parent(grp, "CON_controls")

            mc.select(cl=1)
            jnt = mc.joint(n=sel[i].replace("_CON", "_BN"))
            const = mc.parentConstraint(sel[i], jnt, mo=False)
            mc.delete(const)

            if mc.objExists("BN_joints"):
                pass
            else:
                mc.createNode("transform", n="BN_joints")

            mc.parent(jnt, "BN_joints")

            # parenting

            mc.makeIdentity(sel[i], a=True, t=True, r=True, s=True)
            mc.makeIdentity(jnt, a=True, t=True, r=True, s=True)
            mc.parentConstraint(sel[i], jnt, mo=True)

            mc.select(cl=1)

    def run(self, *args):
        mirror = mc.checkBox(self.mirror_ckb, q=True, value=True)
        if mirror == 1:
            self.MirrorControl()
        self.finalizeControl()


# Main function to run the tool
def main(*args):
    dialog = ControlCreator()
    dialog.show()
