"""Create a cube curve control matched to each selected transform."""

import logging

import maya.cmds as mc

logger = logging.getLogger(__name__)

# Unit cube drawn as a single degree-1 curve (edge path visits every edge)
CUBE_SHAPE = [
    (0.5, 0.5, 0.5),
    (0.5, 0.5, -0.5),
    (-0.5, 0.5, -0.5),
    (-0.5, 0.5, 0.5),
    (0.5, 0.5, 0.5),
    (0.5, -0.5, 0.5),
    (0.5, -0.5, -0.5),
    (0.5, 0.5, -0.5),
    (-0.5, 0.5, -0.5),
    (-0.5, -0.5, -0.5),
    (0.5, -0.5, -0.5),
    (-0.5, -0.5, -0.5),
    (-0.5, -0.5, 0.5),
    (-0.5, 0.5, 0.5),
    (-0.5, -0.5, 0.5),
    (0.5, -0.5, 0.5),
]


def main(scale=1.0, *args):
    try:
        scale = float(scale)
    except (TypeError, ValueError):
        scale = 1.0
    create_cube_controls(scale)


def create_cube_controls(scale=1.0):
    sel = mc.ls(sl=True)
    if not sel:
        mc.warning("Select transforms to build cube controls at.")
        return None

    controls = []
    for node in sel:
        points = [(p[0] * scale, p[1] * scale, p[2] * scale) for p in CUBE_SHAPE]
        con = mc.curve(n="{}_CON".format(node), d=1, p=points)
        const = mc.parentConstraint(node, con, mo=False)
        mc.delete(const)
        controls.append(con)
        logger.debug("Created %s at %s", con, node)

    mc.select(controls)
    return controls
