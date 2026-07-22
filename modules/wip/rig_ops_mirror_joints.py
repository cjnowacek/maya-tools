"""Mirror the selected joint chain across the YZ plane with mirror behavior,
swapping side name tokens (repo convention: L_ / R_ prefixes).
"""

import logging

import maya.cmds as mc

logger = logging.getLogger(__name__)


def main(search="L_", replace="R_", *args):
    mirror_joints(search or "L_", replace or "R_")


def mirror_joints(search="L_", replace="R_"):
    sel = mc.ls(sl=True, type="joint")
    if not sel:
        mc.warning("Select the root joint of the chain to mirror.")
        return None

    root = sel[0]
    original_parent = mc.listRelatives(root, parent=True)

    # Mirror around a temp joint at the origin so the chain flips about YZ
    mc.select(cl=True)
    tmp = mc.joint(n="mirror_tmp_JNT", p=[0, 0, 0])
    mc.parent(root, tmp)
    mirrored = mc.mirrorJoint(
        tmp, mirrorBehavior=True, mirrorYZ=True, searchReplace=(search, replace)
    )

    new_joints = mc.listRelatives(mirrored[0], children=True) or []
    if new_joints:
        new_joints = mc.parent(new_joints, world=True)
    mc.delete(mirrored[0])

    if original_parent:
        mc.parent(root, original_parent[0])
    else:
        mc.parent(root, world=True)
    mc.delete(tmp)

    mc.select(new_joints)
    logger.debug("Mirrored %s -> %s", root, new_joints)
    return new_joints
