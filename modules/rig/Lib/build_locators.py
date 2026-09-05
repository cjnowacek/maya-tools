"""Build guide locators for a biped: spine, arm, and leg chains.

Creates a "Guides" group with named locator hierarchies matching the repo
naming convention ({side}_Name_BN). Positions are rough biped defaults in
centimeters.

Library module: run through the Build Biped workflow tool (guides phase),
not from the toolset UI directly.
"""

import logging

import maya.cmds as mc

from modules.rig.Lib import scene_meta

logger = logging.getLogger(__name__)

SPINE_GUIDES = [
    ("Pelvis_BN", (0, 95, 0)),
    ("Spine1_BN", (0, 105, 0)),
    ("Spine2_BN", (0, 115, 0)),
    ("Spine3_BN", (0, 125, 0)),
    ("Chest_BN", (0, 135, 0)),
]

# limb chains are STRAIGHT lines: rotate the chain root and the whole
# limb aims as one piece. IK bend direction comes from preferred angles
# set at skeleton-build time, not from pre-bent guides.
ARM_GUIDES = [
    ("Clavicle_BN", (4, 142, 0)),
    ("Shoulder_BN", (16, 142, 0)),
    ("Elbow_BN", (42, 142, 0)),
    ("Wrist_BN", (68, 142, 0)),
]

LEG_GUIDES = [
    ("Thigh_BN", (10, 92, 0)),
    ("Calf_BN", (10, 50, 0)),
    ("Ankle_BN", (10, 10, 0)),
    ("Ball_BN", (10, 2, 12)),
    ("Toe_BN", (10, 2, 20)),
]

# Foot PIVOT guides (_GD suffix: placement targets for the reverse foot's
# pivots, NOT bones - the skeleton builder skips them). Heel is where the
# foot rocks back; the bank guides are the inner/outer sole edges the foot
# tips over sideways.
FOOT_PIVOT_GUIDES = [
    ("Heel_GD", (10, 0, -7)),
    ("BankInner_GD", (6, 0, 12)),
    ("BankOuter_GD", (14, 0, 12)),
]




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
    made += ensure_foot_pivot_guides(side, top)

    scene_meta.record("guides", nodes=[top], info={"side": side})
    mc.select(top)
    logger.debug("Built guides: %s", made)
    return made


def straighten_limb_guides(side="L"):
    """Project each limb's mid guide onto the root->end line, keeping the
    user's endpoint placement: the chain becomes a straight line that can
    be rotated in place as one piece."""
    def project(root, mid, end):
        if not all(mc.objExists(n) for n in (root, mid, end)):
            return False
        a = mc.xform(root, q=True, ws=True, t=True)
        b = mc.xform(mid, q=True, ws=True, t=True)
        c = mc.xform(end, q=True, ws=True, t=True)
        d = [c[i] - a[i] for i in range(3)]
        l2 = sum(v * v for v in d) or 1.0
        t = sum((b[i] - a[i]) * d[i] for i in range(3)) / l2
        mc.xform(mid, ws=True, t=[a[i] + d[i] * t for i in range(3)])
        return True
    pre = "{}_".format(side.upper()[0])
    done = []
    if project(pre + "Thigh_BN", pre + "Calf_BN", pre + "Ankle_BN"):
        done.append("leg")
    if project(pre + "Shoulder_BN", pre + "Elbow_BN", pre + "Wrist_BN"):
        done.append("arm")
    return done


def ensure_foot_pivot_guides(side="L", top="Guides"):
    """Add the foot pivot guides for a side if missing (safe to re-run,
    including on scenes whose guides predate these)."""
    mirror = side.upper().startswith("R")
    prefix = "{}_".format(side.upper()[0])
    if not mc.objExists(top):
        top = mc.createNode("transform", name=top)
    made = []
    for name, pos in FOOT_PIVOT_GUIDES:
        full = prefix + name
        if mc.objExists(full):
            continue
        loc = mc.spaceLocator(n=full)[0]
        x = -pos[0] if mirror else pos[0]
        mc.xform(loc, ws=True, t=(x, pos[1], pos[2]))
        loc = mc.parent(loc, top)[0]
        made.append(loc)
    return made
