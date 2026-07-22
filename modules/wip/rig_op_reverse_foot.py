"""Reverse-foot setup.

Select four things IN ORDER: ankle joint, ball joint, toe joint, and a heel
guide (joint or locator). Optionally select the leg's ikHandle fifth; if
omitted, the tool looks for "{side}_Leg_IKR" (the name the leg IKFK builder
uses) and parents it into the reverse chain so foot roll drives the leg IK.

Builds the classic reverse pivot hierarchy (heel > toe > ball > ankle),
single-chain IK handles for ankle->ball and ball->toe, and a foot control
with HeelRoll / BallRoll / ToeRoll / ToeSpin / Bank attributes.

Assumes the character faces +Z with world-oriented pivots: roll maps to
rotateX, spin to rotateY, bank to rotateZ. Adjust the connections if your
rig faces another axis.
"""

import logging

import maya.cmds as mc

logger = logging.getLogger(__name__)


def main(side="L", *args):
    build_reverse_foot(side or "L")


def build_reverse_foot(side="L"):
    sel = mc.ls(sl=True)
    if len(sel) < 4:
        mc.warning(
            "Select ankle, ball, and toe joints plus a heel guide (in order)."
        )
        return None

    ankle, ball, toe, heel = sel[:4]
    leg_ik = sel[4] if len(sel) > 4 else None
    if leg_ik is None and mc.objExists("{}_Leg_IKR".format(side)):
        leg_ik = "{}_Leg_IKR".format(side)

    name = "{}_Foot".format(side)
    top = mc.group(em=True, n="{}_ReverseFoot_GRP".format(name))

    def pivot(label, snap_to):
        piv = mc.group(em=True, n="{}_{}_PIV".format(name, label))
        pos = mc.xform(snap_to, q=True, ws=True, t=True)
        mc.xform(piv, ws=True, t=pos)
        return piv

    heel_piv = pivot("Heel", heel)
    toe_piv = pivot("Toe", toe)
    ball_piv = pivot("Ball", ball)
    ankle_piv = pivot("Ankle", ankle)

    mc.parent(ankle_piv, ball_piv)
    mc.parent(ball_piv, toe_piv)
    mc.parent(toe_piv, heel_piv)
    mc.parent(heel_piv, top)

    # Single-chain handles so ball and toe follow the reverse pivots
    ball_ik = mc.ikHandle(
        n="{}_Ball_IKS".format(name), sol="ikSCsolver", sj=ankle, ee=ball
    )[0]
    toe_ik = mc.ikHandle(
        n="{}_Toe_IKS".format(name), sol="ikSCsolver", sj=ball, ee=toe
    )[0]
    mc.parent(ball_ik, ball_piv)
    mc.parent(toe_ik, toe_piv)

    if leg_ik and mc.objExists(leg_ik) and mc.objectType(leg_ik) == "ikHandle":
        mc.parent(leg_ik, ankle_piv)
        logger.debug("Parented leg ikHandle %s into reverse chain", leg_ik)
    else:
        mc.warning(
            "No leg ikHandle found; parent it under {} manually.".format(ankle_piv)
        )

    # Foot control drives the whole reverse chain
    ctl = mc.circle(n="{}_CON".format(name), nr=[0, 1, 0], sw=360, r=4)[0]
    ankle_pos = mc.xform(ankle, q=True, ws=True, t=True)
    mc.xform(ctl, ws=True, t=(ankle_pos[0], 0, ankle_pos[2]))
    mc.makeIdentity(ctl, apply=True, t=True, r=True, s=True)
    mc.parent(top, ctl)

    for attr, node, axis in (
        ("HeelRoll", heel_piv, "rotateX"),
        ("BallRoll", ball_piv, "rotateX"),
        ("ToeRoll", toe_piv, "rotateX"),
        ("ToeSpin", toe_piv, "rotateY"),
        ("Bank", ball_piv, "rotateZ"),
    ):
        mc.addAttr(ctl, ln=attr, at="float", k=True)
        mc.connectAttr("{}.{}".format(ctl, attr), "{}.{}".format(node, axis))

    mc.select(ctl)
    logger.debug("Built reverse foot %s", top)
    return ctl
