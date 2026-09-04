"""Create a locator (with a joint parented under it) at the selected object's
position. Useful for placing guide points that carry an orientable joint.
"""

import logging

import maya.cmds as cmds

logger = logging.getLogger(__name__)


TOOL_META = {
    "description": (
        'Create a locator with a joint under it at the selected object.\n\n'
        'For placing guide points that carry an orientable joint, e.g. on '
        'the Build Locators guides.'
    ),
}


def main(*args):
    create_jnt_loc()


def create_jnt_loc():
    sel = cmds.ls(sl=True)
    if not sel:
        cmds.warning("Select an object to place a joint and locator at.")
        return None

    loc = cmds.spaceLocator(p=(0, 0, 0))
    const = cmds.pointConstraint(sel, loc, offset=(0, 0, 0), weight=1)
    cmds.delete(const)

    cmds.select(cl=True)
    jnt = cmds.joint(p=(0, 0, 0))
    const = cmds.pointConstraint(loc, jnt, offset=(0, 0, 0), weight=1)
    cmds.delete(const)
    cmds.parent(jnt, loc)

    cmds.select(loc)
    logger.debug("Created %s with %s at %s", loc, jnt, sel)
    return loc, jnt
