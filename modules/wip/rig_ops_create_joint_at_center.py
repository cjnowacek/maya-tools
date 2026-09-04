"""Create a joint at the center of the current component or object selection."""

import logging

import maya.cmds as mc

logger = logging.getLogger(__name__)


TOOL_META = {
    "description": (
        'Create a joint at the center of the current selection.\n\n'
        'Works on component selections (vertices, edges, faces) and whole '
        "objects: the joint lands on the selection's bounding center."
    ),
}


def main(*args):
    create_joint_at_center()


def create_joint_at_center():
    sel = mc.ls(sl=True)
    if not sel:
        mc.warning("Select components or objects to place a joint at their center.")
        return None

    # A cluster's pivot lands on the selection center; snap a joint to it
    clstr = mc.cluster()
    mc.select(cl=True)
    jnt = mc.joint(rad=1)
    const = mc.parentConstraint(clstr, jnt, mo=False)
    mc.delete(const, clstr)
    mc.select(jnt)
    logger.debug("Created %s at selection center", jnt)
    return jnt
