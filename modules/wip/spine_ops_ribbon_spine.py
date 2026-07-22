"""Ribbon spine builder.

Select the spine joints IN ORDER (pelvis first, chest last; 3 or more).
Builds a lofted NURBS ribbon through the chain, pins a transform to the
surface for each joint with a single uvPin node (Maya 2020+), drives each
bind joint from its pin, and skins the ribbon to three driver joints
(bottom / mid / top) with circle controls.

uvPin is used instead of follicles: one node handles every pin, evaluates
faster, and drives the pin transforms directly via offsetParentMatrix.

The ribbon width runs along world X; adjust after building if your rig
needs a different orientation.
"""

import logging

import maya.cmds as mc

logger = logging.getLogger(__name__)


def main(width=2.0, *args):
    try:
        width = float(width)
    except (TypeError, ValueError):
        width = 2.0
    build_ribbon_spine(width)


def build_ribbon_spine(width=2.0):
    joints = mc.ls(sl=True, type="joint")
    if len(joints) < 3:
        mc.warning("Select three or more spine joints in order (pelvis first).")
        return None

    positions = [mc.xform(j, q=True, ws=True, t=True) for j in joints]
    master = mc.createNode("transform", n="RibbonSpine_System")

    # Loft two offset copies of a curve through the chain into a ribbon
    half = width / 2.0
    curve_a = mc.curve(d=3, p=[(p[0] + half, p[1], p[2]) for p in positions])
    curve_b = mc.curve(d=3, p=[(p[0] - half, p[1], p[2]) for p in positions])
    surface = mc.loft(
        curve_b, curve_a, n="RibbonSpine_Surface", d=3, ch=False, u=True
    )[0]
    mc.delete(curve_a, curve_b)
    mc.rebuildSurface(
        surface,
        ch=False,
        su=1,
        sv=len(joints) - 1,
        du=3,
        dv=3,
        dir=2,
        rpo=True,
    )
    mc.parent(surface, master)

    surface_shape = mc.listRelatives(surface, shapes=True)[0]

    # One uvPin node pins a transform per joint, evenly spaced along V
    pin_grp = mc.createNode("transform", n="RibbonSpine_Pins")
    mc.parent(pin_grp, master)

    uv_pin = mc.createNode("uvPin", n="RibbonSpine_uvPin")
    mc.connectAttr(surface_shape + ".worldSpace[0]", uv_pin + ".deformedGeometry")

    for i, jnt in enumerate(joints):
        mc.setAttr("{}.coordinate[{}].coordinateU".format(uv_pin, i), 0.5)
        mc.setAttr(
            "{}.coordinate[{}].coordinateV".format(uv_pin, i),
            i / float(len(joints) - 1),
        )

        pin = mc.createNode("transform", n="RibbonSpine_Pin{}".format(i))
        mc.parent(pin, pin_grp)
        mc.connectAttr(
            "{}.outputMatrix[{}]".format(uv_pin, i), pin + ".offsetParentMatrix"
        )
        mc.parentConstraint(pin, jnt, mo=True)

    # Three driver joints skinned to the ribbon, with controls
    driver_grp = mc.createNode("transform", n="RibbonSpine_Drivers")
    mc.parent(driver_grp, master)

    driver_positions = [positions[0], positions[len(positions) // 2], positions[-1]]
    drivers = []
    controls = []
    for label, pos in zip(("Bottom", "Mid", "Top"), driver_positions):
        mc.select(cl=True)
        drv = mc.joint(n="RibbonSpine_{}_DRV_JNT".format(label))
        mc.xform(drv, ws=True, t=pos)

        con = mc.circle(
            n="RibbonSpine_{}_CON".format(label), nr=[0, 1, 0], sw=360, r=width * 2
        )[0]
        grp = mc.group(con, n="RibbonSpine_{}_GRP".format(label))
        mc.xform(grp, ws=True, t=pos)
        mc.parent(drv, con)
        mc.parent(grp, driver_grp)
        drivers.append(drv)
        controls.append(con)

    mc.skinCluster(drivers, surface, tsb=True, mi=2, n="RibbonSpine_skinCluster")

    mc.select(controls)
    logger.debug("Ribbon spine built for %s", joints)
    return master
