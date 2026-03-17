import maya.cmds as mc
import maya.mel as mel
from maya import OpenMaya as om


def main(*args):
    RigOps_createJointatCenter()


class RigOps_createJointatCenter(object):

    def __init__(self):
        clstr = mc.cluster()
        mc.select(cl=1)
        jnt = mc.joint()
        mc.select(cl=1)
        const = mc.parentConstraint(clstr, jnt, mo=0)
        mc.delete(const, clstr)
