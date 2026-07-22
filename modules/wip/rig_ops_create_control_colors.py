"""Set the drawing-override color on the shapes of the selected controls.

With color_index 0 (default), color is chosen from the naming convention:
L_ prefix gets blue (6), R_ prefix gets red (13), anything else yellow (17).
Pass an explicit Maya color index (1-31) to override.
"""

import logging

import maya.cmds as cmds

logger = logging.getLogger(__name__)

SIDE_COLORS = {"L_": 6, "R_": 13}
CENTER_COLOR = 17


def main(color_index=0, *args):
    try:
        color_index = int(color_index)
    except (TypeError, ValueError):
        color_index = 0
    set_control_colors(color_index)


def set_control_colors(color_index=0):
    sel = cmds.ls(sl=True)
    if not sel:
        cmds.warning("Select controls to color.")
        return

    for node in sel:
        color = color_index
        if not color:
            color = CENTER_COLOR
            for prefix, side_color in SIDE_COLORS.items():
                if node.startswith(prefix):
                    color = side_color
                    break

        shapes = cmds.listRelatives(node, shapes=True, fullPath=True) or []
        if not shapes and cmds.objectType(node, isAType="shape"):
            shapes = [node]
        for shape in shapes:
            cmds.setAttr(shape + ".overrideEnabled", 1)
            cmds.setAttr(shape + ".overrideColor", color)
            logger.debug("Colored %s with index %s", shape, color)
