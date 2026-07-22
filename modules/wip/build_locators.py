"""Build guide locators for a biped: spine, arm, and leg chains.

Creates a "Guides" group with named locator hierarchies matching the repo
naming convention ({side}_Name_BN). Positions are rough biped defaults in
centimeters; move the guides to fit the character, then build joints from
them (see tool_ops_create_jnt_loc_at_point).
"""

import logging

import maya.cmds as mc

logger = logging.getLogger(__name__)

SPINE_GUIDES = [
    ("Pelvis_BN", (0, 95, 0)),
    ("Spine1_BN", (0, 105, 0)),
    ("Spine2_BN", (0, 115, 0)),
    ("Spine3_BN", (0, 125, 0)),
    ("Chest_BN", (0, 135, 0)),
]

ARM_GUIDES = [
    ("Clavicle_BN", (4, 142, 2)),
    ("Shoulder_BN", (16, 142, 0)),
    ("Elbow_BN", (42, 142, -4)),
    ("Wrist_BN", (68, 142, 0)),
]

LEG_GUIDES = [
    ("Thigh_BN", (10, 92, 0)),
    ("Calf_BN", (10, 50, 4)),
    ("Ankle_BN", (10, 10, 0)),
    ("Ball_BN", (10, 2, 12)),
    ("Toe_BN", (10, 2, 20)),
]


def main(side="L", *args):
    build_guides(side or "L")


def _build_chain(guides, parent_group, prefix="", mirror=False):
    previous = None
    top = None
    for name, pos in guides:
        loc = mc.spaceLocator(n=prefix + name)[0]
        x = -pos[0] if mirror else pos[0]
        mc.xform(loc, ws=True, t=(x, pos[1], pos[2]))
        if previous:
            mc.parent(loc, previous)
        else:
            top = loc
        previous = loc
    mc.parent(top, parent_group)
    return top


def build_guides(side="L"):
    if mc.objExists("Guides"):
        top = "Guides"
    else:
        top = mc.createNode("transform", name="Guides")

    mirror = side.upper().startswith("R")
    prefix = "{}_".format(side.upper()[0])

    made = []
    if not mc.objExists("Pelvis_BN"):
        made.append(_build_chain(SPINE_GUIDES, top))
    made.append(_build_chain(ARM_GUIDES, top, prefix=prefix, mirror=mirror))
    made.append(_build_chain(LEG_GUIDES, top, prefix=prefix, mirror=mirror))

    mc.select(top)
    logger.debug("Built guides: %s", made)
    return made
