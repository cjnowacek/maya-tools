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
        _add_axis_tripod(loc)
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
    orient_guides(top)

    scene_meta.record("guides", nodes=[top], info={"side": side})
    mc.select(top)
    logger.debug("Built guides: %s", made)
    return made


AXIS_TRIPOD = (
    ("X", (1, 0, 0), 13),   # red   = bone direction (aims at the child)
    ("Y", (0, 1, 0), 14),   # green
    ("Z", (0, 0, 1), 6),    # blue  = front reference
)


AXIS_WIDTH = 3.0    # curve lineWidth: thin default lines are hard to read


def _add_axis_tripod(loc, size=3.0, width=AXIS_WIDTH):
    """RGB axis lines parented as SHAPES under the guide transform, so the
    guide's orientation is readable at a glance without extra nodes."""
    for label, vec, color in AXIS_TRIPOD:
        crv = mc.curve(degree=1, point=[(0, 0, 0),
                                        tuple(v * size for v in vec)])
        shape = mc.listRelatives(crv, shapes=True)[0]
        shape = mc.rename(shape, "{}_axis{}Shape".format(loc, label))
        mc.setAttr(shape + ".overrideEnabled", 1)
        mc.setAttr(shape + ".overrideColor", color)
        try:                       # lineWidth needs Maya 2019+ and a VP2 draw
            mc.setAttr(shape + ".lineWidth", width)
        except RuntimeError:
            pass
        mc.parent(shape, loc, relative=True, shape=True)
        mc.delete(crv)


def set_axis_size(size=3.0, width=AXIS_WIDTH, top="Guides"):
    """Rescale every guide's axis tripod in place.

    The CVs are rewritten rather than the transform scaled, so guide
    scale stays 1 and nothing downstream inherits a scale factor. The
    locator's own crosshair is matched to the same size.
    """
    changed = 0
    for loc in mc.listRelatives(top, allDescendents=True, type="transform",
                                fullPath=True) or []:
        shapes = mc.listRelatives(loc, shapes=True, fullPath=True) or []
        for shape in shapes:
            short = shape.split("|")[-1]
            if mc.nodeType(shape) == "locator":
                for axis in "XYZ":
                    mc.setAttr("{}.localScale{}".format(shape, axis),
                               size * 0.35)
                continue
            if "_axis" not in short:
                continue
            label = short.split("_axis")[-1].replace("Shape", "")
            vec = dict((a, v) for a, v, _c in AXIS_TRIPOD).get(label)
            if not vec:
                continue
            mc.setAttr(shape + ".controlPoints[0]", 0, 0, 0, type="double3")
            mc.setAttr(shape + ".controlPoints[1]",
                       vec[0] * size, vec[1] * size, vec[2] * size,
                       type="double3")
            try:
                mc.setAttr(shape + ".lineWidth", width)
            except RuntimeError:
                pass
            changed += 1
    return changed


def _aim_guide(loc, target_pos):
    """Orient a guide so +X points at the target (one-shot, no constraint:
    rotating a chain root still aims the whole limb by hand)."""
    pos = mc.xform(loc, q=True, ws=True, t=True)
    d = [target_pos[i] - pos[i] for i in range(3)]
    length = (d[0] ** 2 + d[1] ** 2 + d[2] ** 2) ** 0.5
    if length < 1e-5:
        return
    d = [v / length for v in d]
    # front reference is world +Z unless the bone runs along Z (toes)
    up = (0.0, 1.0, 0.0) if abs(d[2]) > 0.9 else (0.0, 0.0, 1.0)
    tmp = mc.group(empty=True, world=True)
    mc.xform(tmp, ws=True, t=target_pos)
    cons = mc.aimConstraint(tmp, loc, aimVector=(1, 0, 0), upVector=up,
                            worldUpType="vector", worldUpVector=up)
    mc.delete(cons)
    mc.delete(tmp)


def orient_guides(top="Guides"):
    """Aim every guide down its chain; leaves and pivot guides copy the
    parent's frame. Safe to re-run: refreshes axes after guides move.

    Rotating a parent MOVES its children, so all world positions are
    snapshotted first and re-imposed top-down after each rotation - the
    naive aim-in-place version scrambled every placed guide (caught live;
    positions had to be rebuilt from the skeleton).
    """
    if not mc.objExists(top):
        return 0
    all_locs = []
    for loc in mc.listRelatives(top, allDescendents=True, type="transform",
                                fullPath=True) or []:
        if mc.listRelatives(loc, shapes=True, type="locator"):
            all_locs.append(loc)
    all_locs.sort(key=lambda n: n.count("|"))          # parents first
    snapshot = {loc: mc.xform(loc, q=True, ws=True, t=True)
                for loc in all_locs}

    def child_locs(loc):
        return [c for c in (mc.listRelatives(loc, children=True,
                                             type="transform",
                                             fullPath=True) or [])
                if mc.listRelatives(c, shapes=True, type="locator")]

    count = 0
    for loc in all_locs:
        kids = child_locs(loc)
        if kids:
            _aim_guide(loc, snapshot[kids[0]])
        else:
            parent = (mc.listRelatives(loc, parent=True, fullPath=True)
                      or [None])[0]
            if parent in snapshot:
                mc.xform(loc, ws=True,
                         ro=mc.xform(parent, q=True, ws=True, ro=True))
        # the rotation displaced every descendant: re-impose their
        # snapshotted world positions (top-down order keeps this stable)
        mc.xform(loc, ws=True, t=snapshot[loc])
        for kid in kids:
            mc.xform(kid, ws=True, t=snapshot[kid])
        count += 1
    # final pass: everything back at its snapshot, exactly
    for loc in all_locs:
        mc.xform(loc, ws=True, t=snapshot[loc])
    return count


def upgrade_guide_display(top="Guides", size=3.0, width=AXIS_WIDTH):
    """Retrofit axis tripods onto guides that lack them, size them all to
    `size`, then orient everything."""
    added = 0
    for loc in mc.listRelatives(top, allDescendents=True, type="transform",
                                fullPath=True) or []:
        if not mc.listRelatives(loc, shapes=True, type="locator"):
            continue
        short = loc.split("|")[-1]
        if mc.ls("{}_axisXShape".format(short)):
            continue
        _add_axis_tripod(short, size, width)
        added += 1
    set_axis_size(size, width, top)
    oriented = orient_guides(top)
    return added, oriented


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
        # end is a CHILD of mid in the guide chain, so moving mid dragged
        # it: restore its snapshot or the line we projected onto is gone
        mc.xform(end, ws=True, t=c)
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
        _add_axis_tripod(loc)
        x = -pos[0] if mirror else pos[0]
        mc.xform(loc, ws=True, t=(x, pos[1], pos[2]))
        loc = mc.parent(loc, top)[0]
        made.append(loc)
    return made
