import logging
import maya.cmds as mc

logger = logging.getLogger(__name__)


def main():
    MirrorJoints()


def MirrorJoints(mirrorbehaviour=True):
    selList = []

    sel = mc.ls(sl=1)
    selchildren = mc.listRelatives(sel, ad=True)
    selList.append(sel)
    selList.append(selchildren)

    for each in range(len(selList)):
        logger.debug(selList[each])

    mc.select(cl=1)
    mirrorjnt = mc.joint(n="mirror_joint", p=[0, 0, 0])

    mc.parent(sel[:], mirrorjnt)
    mc.mirrorJoint(mirrorjnt, mb=mirrorbehaviour, mirrorYZ=True, sr=("_l", "_r"))
    topjoint = mc.ls(sl=1)
    newjoints = mc.listRelatives(children=True)

    mc.parent(newjoints, w=1)
    mc.delete(topjoint)

    mc.select(mirrorjnt)
    mc.parent(sel[:], w=1)
    mc.delete("mirror_joint")
