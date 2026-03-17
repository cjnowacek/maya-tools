from maya import cmds as mc
import maya.mel as mel
from maya import OpenMaya as om
from maya import OpenMayaUI as omui


def main():
    mainBodyLocs = spineLoc()
    armLocs = armLocs()
    legLocs = legLocs()

# main body
class RigOps_mainBodyLocs(object):

    # constructor
    def __init__(self):

        self.transform_group = mc.createNode("transform", name="Locs")

        self.spineLocList = []
        self.root_Name = "Root"


# _________________________________________________________________#


# build spineLocs
class spineLoc(object):

    # constructor
    def __init__(self):
        self.spineLocList = []
        self.pelvis_Name = "Pelvis_BN"
        self.spine1_Name = "Spine1_BN"
        self.spine2_Name = "Spine2_BN"
        self.spine3_Name = "Spine3_BN"
        self.chest_Name = "Chest_BN"

    def build(self):
        self.PelvisLoc = mc.spaceLocator(n=self.pelvis_Name, p=(0, 0, 0))[0]
        self.Spine1Loc = mc.spaceLocator(n=self.spine1_Name, p=(0, 0, 1))[0]
        self.Spine2Loc = mc.spaceLocator(n=self.spine2_Name, p=(0, 0, 2))[0]
        self.Spine3Loc = mc.spaceLocator(n=self.spine3_Name, p=(0, 0, 3))[0]
        self.ChestLoc = mc.spaceLocator(n=self.chest_Name, p=(0, 0, 4))[0]
        self.appendspineLocs()

        mc.parent(self.ChestLoc, self.Spine3Loc)
        mc.parent(self.Spine3Loc, self.Spine2Loc)
        mc.parent(self.Spine2Loc, self.Spine1Loc)
        mc.parent(self.Spine1Loc, self.PelvisLoc)

        self.transform_group = mc.createNode("transform", name="Spine_Group")

        mc.parent(self.PelvisLoc, self.transform_group)

        mc.select(self.transform_group)

    def appendspineLocs(self):

        if self.PelvisLoc not in self.spineLocList:
            self.spineLocList.append(self.PelvisLoc)
        if self.Spine1Loc not in self.spineLocList:
            self.spineLocList.append(self.Spine1Loc)
        if self.Spine2Loc not in self.spineLocList:
            self.spineLocList.append(self.Spine2Loc)
        if self.Spine3Loc not in self.spineLocList:
            self.spineLocList.append(self.Spine3Loc)
        if self.ChestLoc not in self.spineLocList:
            self.spineLocList.append(self.ChestLoc)


class RigOps_spineSkl(object):
    pass


class RigOps_spineRig(object):
    pass


# _________________________________________________________________#


# build armLocs
class armLocs(object):

    def __init__(self):
        self.spineLocList = []
        self.pelvis_Name = "Pelvis_BN"
        self.spine1_Name = "Spine1_BN"
        self.spine2_Name = "Spine2_BN"
        self.spine3_Name = "Spine3_BN"
        self.chest_Name = "Chest_BN"


class RigOps_armSkl(object):
    pass


class RigOps_armRig(object):
    pass


# _________________________________________________________________#


# build legLocs
class legLocs(object):

    def __init__(self):
        self.spineLocList = []
        self.pelvis_Name = "Pelvis_BN"
        self.spine1_Name = "Spine1_BN"
        self.spine2_Name = "Spine2_BN"
        self.spine3_Name = "Spine3_BN"
        self.chest_Name = "Chest_BN"


class RigOps_legSkl(object):
    pass


class RigOps_legRig(object):
    pass
