"""Reverse-foot setup.

Select four things IN ORDER: ankle joint, ball joint, toe joint, and a heel
guide (joint or locator). Optionally select the leg's ikHandle fifth; if
omitted, the tool looks for "{side}_Leg_IKR" (the name the leg IKFK builder
uses) and parents it into the reverse chain so foot roll drives the leg IK.

Builds the classic reverse pivot hierarchy (heel > toe > ball > ankle),
single-chain IK handles for ankle->ball and ball->toe, and a foot control
with a combined Roll + RollBreak (heel back, ball up to the break angle,
then over the toe) plus manual HeelRoll / BallRoll / ToeRoll / ToeSpin /
Bank attributes summed on top.

Assumes the character faces +Z with world-oriented pivots: roll maps to
rotateX, spin to rotateY, bank to rotateZ. Adjust the connections if your
rig faces another axis.
"""

import logging

import maya.cmds as mc

logger = logging.getLogger(__name__)


TOOL_META = {
    "description": (
        'Reverse-foot setup on an existing leg.\n\n'
        'Select IN ORDER: ankle joint, ball joint, toe joint, heel guide '
        '(joint or locator), and optionally the leg ikHandle (otherwise '
        '{side}_Leg_IKR is used). Builds the reverse pivot hierarchy, SC '
        'handles for ankle-ball-toe, and a foot control with HeelRoll / '
        'BallRoll / ToeRoll / ToeSpin / Bank.\n\n'
        'Assumes the character faces +Z with world-oriented pivots.'
    ),
    "params": {'side': {'label': 'side',
              'choices': ['L', 'R'],
              'tooltip': 'Which side of the character to build.'}},
}


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

    # bank pivots sit on the foot EDGES (feet bank on their sides, not
    # around the ball's center); width estimated from foot length
    ball_pos = mc.xform(ball, q=True, ws=True, t=True)
    heel_pos = mc.xform(heel, q=True, ws=True, t=True)
    toe_pos = mc.xform(toe, q=True, ws=True, t=True)
    mirror = -1.0 if side.upper().startswith("R") else 1.0
    # bank edges: PLACED guides win ({side}_BankInner/Outer_GD), estimate
    # from foot length only when no guide exists
    half_w = 0.35 * abs(toe_pos[2] - heel_pos[2]) or 4.0
    inner_guide = "{}_BankInner_GD".format(side)
    outer_guide = "{}_BankOuter_GD".format(side)
    if mc.objExists(inner_guide):
        inner_pos = mc.xform(inner_guide, q=True, ws=True, t=True)
    else:
        inner_pos = (ball_pos[0] - mirror * half_w, ball_pos[1], ball_pos[2])
    if mc.objExists(outer_guide):
        outer_pos = mc.xform(outer_guide, q=True, ws=True, t=True)
    else:
        outer_pos = (ball_pos[0] + mirror * half_w, ball_pos[1], ball_pos[2])
    inner_piv = mc.group(em=True, n="{}_InnerBank_PIV".format(name))
    mc.xform(inner_piv, ws=True, t=inner_pos)
    outer_piv = mc.group(em=True, n="{}_OuterBank_PIV".format(name))
    mc.xform(outer_piv, ws=True, t=outer_pos)

    mc.parent(ankle_piv, ball_piv)
    mc.parent(ball_piv, toe_piv)
    mc.parent(toe_piv, heel_piv)
    mc.parent(heel_piv, outer_piv)
    mc.parent(outer_piv, inner_piv)
    mc.parent(inner_piv, top)

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
    # yaw evaluated last so the foot can spin without gimbal-locking pitch
    mc.setAttr(ctl + ".rotateOrder", 3)  # xzy
    ankle_pos = mc.xform(ankle, q=True, ws=True, t=True)
    mc.xform(ctl, ws=True, t=(ankle_pos[0], 0, ankle_pos[2]))
    mc.makeIdentity(ctl, apply=True, t=True, r=True, s=True)
    mc.parent(top, ctl)

    for attr in ("HeelRoll", "BallRoll", "ToeRoll", "ToeSpin", "Bank",
                 "Roll"):
        mc.addAttr(ctl, ln=attr, at="float", k=True)
    mc.addAttr(ctl, ln="RollBreak", at="float", k=True, dv=35.0, min=0, max=90)
    mc.connectAttr(ctl + ".ToeSpin", toe_piv + ".rotateY")
    # Bank tips onto the matching EDGE: positive rolls over the outer edge,
    # negative over the inner (clamped so each pivot only takes its side)
    # Sign rule (derived, then verified live on both sides): rotZ+ lifts
    # whatever sits at +X of the pivot, and each edge pivot must lift the
    # foot body on its opposite side, so BOTH edges use -mirror. A fixed
    # sign lifts one side and sinks the other through the floor.
    bank_out = mc.createNode("clamp", n="{}_bankOut_clamp".format(name))
    mc.setAttr(bank_out + ".maxR", 360)
    mc.connectAttr(ctl + ".Bank", bank_out + ".inputR")
    bank_out_sign = mc.createNode("multDoubleLinear",
                                  n="{}_bankOut_sign".format(name))
    mc.setAttr(bank_out_sign + ".input2", -mirror)
    mc.connectAttr(bank_out + ".outputR", bank_out_sign + ".input1")
    mc.connectAttr(bank_out_sign + ".output", outer_piv + ".rotateZ")
    bank_in = mc.createNode("clamp", n="{}_bankIn_clamp".format(name))
    mc.setAttr(bank_in + ".minR", -360)
    mc.connectAttr(ctl + ".Bank", bank_in + ".inputR")
    bank_in_sign = mc.createNode("multDoubleLinear",
                                 n="{}_bankIn_sign".format(name))
    mc.setAttr(bank_in_sign + ".input2", -mirror)
    mc.connectAttr(bank_in + ".outputR", bank_in_sign + ".input1")
    mc.connectAttr(bank_in_sign + ".output", inner_piv + ".rotateZ")

    # Direct-manipulation pivots (AFR: "multiple pivot points on the feet"):
    # a small selectable wedge INSIDE each driven pivot, free to rotate on
    # top of whatever the attrs/pad contribute. The wedge is inserted into
    # the chain so rotating it pivots everything below it.
    def wedge(label, piv, radius=1.2):
        w = mc.circle(n="{}_{}_pivot_CON".format(name, label),
                      nr=(0, 1, 0), r=radius, ch=False)[0]
        mc.delete(mc.pointConstraint(piv, w))
        w = mc.parent(w, piv)[0]
        mc.setAttr(w + ".overrideEnabled", 1)
        mc.setAttr(w + ".overrideColor", 20)
        for a in ("sx", "sy", "sz"):
            mc.setAttr("{}.{}".format(w, a), lock=True, keyable=False)
        # reparent the pivot's other children under the wedge
        for child in mc.listRelatives(piv, children=True, type="transform") or []:
            if child != w.split("|")[-1]:
                mc.parent(child, w)
        return w

    wedge("Heel", heel_piv)
    wedge("Toe", toe_piv)
    wedge("Ball", ball_piv)

    # Single Roll with a heel break, summed with the manual per-pivot attrs:
    #   heel = HeelRoll + clamp(Roll, -360, 0)          (negative rocks back)
    #   ball = BallRoll + clamp(Roll, 0, RollBreak)     (heel lifts first)
    #   toe  = ToeRoll  + clamp(Roll - RollBreak, 0+)   (then rolls over toe)
    cl_heel = mc.createNode("clamp", n="{}_heelRoll_clamp".format(name))
    mc.setAttr(cl_heel + ".minR", -360)
    mc.connectAttr(ctl + ".Roll", cl_heel + ".inputR")
    cl_ball = mc.createNode("clamp", n="{}_ballRoll_clamp".format(name))
    mc.connectAttr(ctl + ".RollBreak", cl_ball + ".maxR")
    mc.connectAttr(ctl + ".Roll", cl_ball + ".inputR")
    sub_toe = mc.createNode("plusMinusAverage", n="{}_toeRoll_sub".format(name))
    mc.setAttr(sub_toe + ".operation", 2)
    mc.connectAttr(ctl + ".Roll", sub_toe + ".input1D[0]")
    mc.connectAttr(ctl + ".RollBreak", sub_toe + ".input1D[1]")
    cl_toe = mc.createNode("clamp", n="{}_toeRoll_clamp".format(name))
    mc.setAttr(cl_toe + ".maxR", 360)
    mc.connectAttr(sub_toe + ".output1D", cl_toe + ".inputR")
    for manual, auto, piv in (("HeelRoll", cl_heel + ".outputR", heel_piv),
                              ("BallRoll", cl_ball + ".outputR", ball_piv),
                              ("ToeRoll", cl_toe + ".outputR", toe_piv)):
        pma = mc.createNode("plusMinusAverage",
                            n="{}_{}_sum".format(name, manual))
        mc.connectAttr("{}.{}".format(ctl, manual), pma + ".input1D[0]")
        mc.connectAttr(auto, pma + ".input1D[1]")
        mc.connectAttr(pma + ".output1D", piv + ".rotateX")

    _build_roll_pad(side, name, ctl)
    _build_roll_ring(side, name, ctl, ball)

    mc.select(ctl)
    logger.debug("Built reverse foot %s", top)
    return ctl


def _build_roll_ring(side, name, ctl, ball):
    """Primary roll interface: an arc AT the ball of the foot, rotated
    directly (a rotation input for a rotation result, applied where the
    animator is looking). rotateX -> Roll, rotateZ -> Bank, rotateY ->
    ToeSpin: the whole foot vocabulary on one in-place manipulator.

    The ring rides the foot control but NOT the roll itself: its rotation
    is consumed as network input, so it stays grabbable at the ball
    instead of rolling away with the foot.
    """
    ball_pos = mc.xform(ball, q=True, ws=True, t=True)
    holder = mc.group(empty=True, name="{}_RollRing_GRP".format(name))
    mc.xform(holder, ws=True, t=ball_pos)
    mc.parentConstraint(ctl, holder, maintainOffset=True)

    ring = mc.circle(name="{}_RollRing_CON".format(name), normal=(1, 0, 0),
                     radius=5.0, sweep=360, ch=False)[0]
    ring = mc.parent(ring, holder, relative=True)[0]
    mc.setAttr(ring + ".overrideEnabled", 1)
    mc.setAttr(ring + ".overrideColor", 13)
    mc.setAttr(ring + ".rotateOrder", 3)  # xzy, same as the foot control
    for a in ("tx", "ty", "tz", "sx", "sy", "sz"):
        mc.setAttr("{}.{}".format(ring, a), lock=True, keyable=False)

    # rotation IS the value: 1:1 into the shared network. The pad (if
    # visible) drives the same attrs, so use one or the other per shot.
    for src, dst in (("rotateX", "Roll"), ("rotateZ", "Bank"),
                     ("rotateY", "ToeSpin")):
        plug = "{}.{}".format(ctl, dst)
        existing = mc.listConnections(plug, s=True, d=False, plugs=True)
        if existing:
            # the pad connected first; insert a sum so both inputs work
            pma = mc.createNode("plusMinusAverage",
                               n="{}_{}_inputSum".format(name, dst))
            mc.connectAttr(existing[0], pma + ".input1D[0]", force=True)
            mc.connectAttr("{}.{}".format(ring, src), pma + ".input1D[1]")
            mc.connectAttr(pma + ".output1D", plug, force=True)
        else:
            mc.connectAttr("{}.{}".format(ring, src), plug)
    mc.addAttr(ctl, ln="ShowRollRing", at="bool", k=True, dv=True)
    mc.connectAttr(ctl + ".ShowRollRing", holder + ".visibility")
    logger.debug("Built roll ring %s", ring)
    return ring


def _build_roll_pad(side, name, ctl):
    """2D slider pad for the foot roll (pattern from the Robin rig).

    A bounds rectangle floats beside the foot; the puck inside is limited
    to +/-2 in X and Z (Y locked). Drag back = heel roll, forward = ball
    roll then over the toe (through the control's Roll + RollBreak), drag
    sideways = bank. The pad follows the foot control.
    """
    mirror = -1.0 if side.upper().startswith("R") else 1.0
    pos = mc.xform(ctl, q=True, ws=True, t=True)

    holder = mc.group(empty=True, name="{}_RollPad_GRP".format(name))
    # flat on the ground beside the foot: reads as a PEDAL (push forward =
    # roll to the toe, pull back = rock the heel, slide sideways = bank)
    mc.xform(holder, ws=True, t=(pos[0] + mirror * 8.0, 0.0, pos[2]))
    mc.parentConstraint(ctl, holder, maintainOffset=True, skipRotate=("x", "z"))
    mc.addAttr(ctl, ln="ShowRollPad", at="bool", k=True, dv=True)
    mc.connectAttr(ctl + ".ShowRollPad", holder + ".visibility")

    bounds = mc.curve(name="{}_RollPad_bounds".format(name), degree=1,
                      point=[(-2.2, 0, -2.2), (2.2, 0, -2.2), (2.2, 0, 2.2),
                             (-2.2, 0, 2.2), (-2.2, 0, -2.2)])
    bounds = mc.parent(bounds, holder, relative=True)[0]
    mc.setAttr(bounds + ".overrideEnabled", 1)
    mc.setAttr(bounds + ".overrideColor", 6)
    for a in ("tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz"):
        mc.setAttr("{}.{}".format(bounds, a), lock=True)

    puck = mc.curve(name="{}_RollPad_CON".format(name), degree=1,
                    point=[(0, 0, -0.6), (0.6, 0, 0), (0, 0, 0.6),
                           (-0.6, 0, 0), (0, 0, -0.6)])
    puck = mc.parent(puck, holder, relative=True)[0]
    mc.setAttr(puck + ".overrideEnabled", 1)
    mc.setAttr(puck + ".overrideColor", 17)
    # asymmetric Z: the heel rock needs half the range roll-through does
    mc.transformLimits(puck, tx=(-2, 2), etx=(True, True),
                       tz=(-1, 2), etz=(True, True))
    for a in ("ty", "rx", "rz", "sx", "sy", "sz"):
        mc.setAttr("{}.{}".format(puck, a), lock=True, keyable=False)

    # forward (+Z) rolls onto ball/toe, back (-Z) rocks the heel:
    # 2 units of travel -> 70 deg of Roll (covers the 35 break + toe)
    roll_gain = mc.createNode("multDoubleLinear",
                              n="{}_RollPad_rollGain".format(name))
    mc.setAttr(roll_gain + ".input2", 35.0)
    mc.connectAttr(puck + ".translateZ", roll_gain + ".input1")
    mc.connectAttr(roll_gain + ".output", ctl + ".Roll")
    # sideways banks (mirrored so both feet bank outward the same way)
    bank_gain = mc.createNode("multDoubleLinear",
                              n="{}_RollPad_bankGain".format(name))
    mc.setAttr(bank_gain + ".input2", 25.0 * mirror)
    mc.connectAttr(puck + ".translateX", bank_gain + ".input1")
    mc.connectAttr(bank_gain + ".output", ctl + ".Bank")
    # third function on the same manipulator: spin the puck = toe spin
    mc.connectAttr(puck + ".rotateY", ctl + ".ToeSpin")
    logger.debug("Built roll pad %s", holder)
    return holder
