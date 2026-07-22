"""Insert a zeroed parent group above each selected object.

Each group matches the object's world transform, so the object's local
values read zero afterward. Existing parents are preserved.
"""

import logging

import maya.cmds as cmds

logger = logging.getLogger(__name__)


def main(*args):
    create_group_at_selection()


def create_group_at_selection():
    sel = cmds.ls(sl=True)
    if not sel:
        cmds.warning("Select at least one object to group.")
        return None

    groups = []
    for node in sel:
        xform = cmds.xform(node, ws=True, q=True, m=True)
        grp = cmds.createNode("transform", name="{}_GRP".format(node))
        cmds.xform(grp, m=xform)

        parent = cmds.listRelatives(node, parent=True)
        if parent:
            cmds.parent(grp, parent[0])
        cmds.parent(node, grp)
        groups.append(grp)
        logger.debug("Inserted %s above %s", grp, node)

    cmds.select(groups)
    return groups
