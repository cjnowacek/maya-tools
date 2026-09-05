"""Body setup: arms, legs, and torso from one panel.

Each body part offers its BUILD as radio choices (mutually exclusive);
sides applies to arms and legs.

  arms   build: none | ikfk            twist: none | roll | ribbon
  legs   build: none | ikfk + foot     twist: none | roll | ribbon
  torso  build: none | fk | spline ik | ribbon

Twist joints are part of the SKELETON (Build Biped creates them, named by
module: L_Leg_ThighTwist1_BN_JNT, L_Arm_ForearmTwist2_BN_JNT, ...). The
twist option here only DRIVES those existing joints - roll via swing-twist
matrix readers, ribbon via a uvPin surface - so the driver can be swapped
later without re-skinning.

Everything built lands under Body_Rig_Grp, sectioned per module:
Body_Rig_Grp > {side}_Arm_Grp / {side}_Leg_Grp (reverse foot inside) /
Torso_Grp, with each module's twist machinery inside its own group.
"""
import logging

import maya.cmds as mc

from modules.rig.Lib import scene_meta
from modules.rig.Lib import leg_rig_builder as lrb
from modules.rig.Lib import leg_ribbon
from modules.wip import rig_op_arm_ikfk_switch
from modules.wip import rig_op_leg_ikfk_switch
from modules.wip import rig_op_reverse_foot
from modules.wip import rig_ops_create_controls
from modules.wip import spine_ops_ribbon_spine

logger = logging.getLogger(__name__)

TOP_GRP = "Body_Rig_Grp"

TOOL_META = {
    "order": 2,
    "description": (
        "Build arms, legs, and torso over the BN skeleton, in one run.\n\n"
        "Pick a BUILD per body part (radio, mutually exclusive). The twist "
        "option DRIVES the skeleton's twist joints (created by Build "
        "Biped, named by module e.g. L_Leg_ThighTwist1_BN_JNT): roll uses "
        "swing-twist matrix readers, ribbon a uvPin surface. Swapping "
        "driver later needs no re-skin. Legs include the reverse foot (a "
        "{side}_Heel guide is created at ground level if none exists).\n\n"
        "Everything is grouped per module under Body_Rig_Grp.\n\n"
        "Run AFTER: Build Biped (with twists/segment > 0 for twist).\n"
        "Assumes the character faces +Z and BN_JNT naming."
    ),
    "params": {
        "sides": {
            "label": "sides",
            "choices": ["both", "L", "R"],
            "tooltip": "Which side(s) to build arms and legs for.",
        },
        "arm_build": {
            "label": "build",
            "group": "Arms",
            "radio": True,
            "choices": ["none", "ikfk"],
            "tooltip": "IKFK switch + pole vector on the arm chain.",
        },
        "arm_twist": {
            "label": "twist",
            "group": "Arms",
            "radio": True,
            "choices": ["none", "roll", "ribbon"],
            "tooltip": "Drive the arm's skeleton twist joints.",
        },
        "leg_build": {
            "label": "build",
            "group": "Legs",
            "radio": True,
            "choices": ["none", "ikfk"],
            "tooltip": "IKFK switch + pole vector + reverse foot.",
        },
        "leg_twist": {
            "label": "twist",
            "group": "Legs",
            "radio": True,
            "choices": ["none", "roll", "ribbon"],
            "tooltip": "Drive the leg's skeleton twist joints.",
        },
        "torso_build": {
            "label": "build",
            "group": "Torso",
            "radio": True,
            "choices": ["none", "fk", "spline", "ribbon"],
            "tooltip": "FK controls, base spline IK, or a ribbon spine.",
        },
    },
}

# module -> segments: (twist label, seg top joint, seg end joint, kind)
# kind "upper": counter-rotate the top joint's own twist (fixed end at top)
# kind "lower": follow the end joint's twist measured about the top joint
MODULE_SEGMENTS = {
    "Arm": [("UpperArm", "Shoulder", "Elbow", "upper"),
            ("Forearm", "Elbow", "Wrist", "lower")],
    "Leg": [("Thigh", "Thigh", "Calf", "upper"),
            ("Shin", "Calf", "Ankle", "lower")],
}


def main(sides="both", arm_build="ikfk", arm_twist="none",
         leg_build="ikfk", leg_twist="none", torso_build="none", *args):
    side_list = ["L", "R"] if (sides or "both") == "both" else [sides]
    results = {}
    for side in side_list:
        if arm_build != "none":
            results["arm_" + side] = build_arm(side, arm_twist)
        if leg_build != "none":
            results["leg_" + side] = build_leg(side, leg_twist)
    if torso_build != "none":
        results["torso"] = build_torso(torso_build)
    if not results:
        mc.warning("Nothing selected to build.")
    return results


# ------------------------------------------------------------------ helpers
def _jnt(side, part):
    return "{}_{}_BN_JNT".format(side, part)


def _missing(side, parts):
    return [_jnt(side, p) for p in parts if not mc.objExists(_jnt(side, p))]


def _redirect_missing(missing):
    mc.warning("Missing bind joints. Redirect: run '{}' first. Missing: {}"
               .format(scene_meta.label("skeleton"), ", ".join(missing)))


def _top_grp():
    if not mc.objExists(TOP_GRP):
        mc.group(empty=True, name=TOP_GRP)
    return TOP_GRP


def _into_group(node, group):
    """Parent node under group if it is not already there."""
    if not node or not mc.objExists(node):
        return
    current = (mc.listRelatives(node, parent=True) or [None])[0]
    if current != group:
        try:
            mc.parent(node, group)
        except RuntimeError:
            logger.debug("could not group %s under %s", node, group,
                         exc_info=True)


def _module_grp(side, module):
    """The module's rig group (created by the IKFK builders), under the top."""
    grp = "{}_{}_Grp".format(side, module)
    if not mc.objExists(grp):
        grp = mc.group(empty=True, name=grp)
    _into_group(grp, _top_grp())
    return grp


def _twist_joints(side, module, label):
    """Skeleton twist joints of one segment, in along-the-bone order."""
    pattern = "{}_{}_{}Twist*_BN_JNT".format(side, module, label)
    found = mc.ls(pattern, type="joint") or []
    return sorted(found)


# -------------------------------------------------------------- twist: roll
def _drive_twists_roll(side, module):
    """Drive the segment's skeleton twists with swing-twist matrix readers.

    Pure DG (multMatrix -> decompose -> quat isolate -> quatToEuler), no
    extra DAG nodes. Upper segments counter-rotate so the top end stays
    put; lower segments follow the end joint's twist.
    """
    driven = 0
    for label, top_part, end_part, kind in MODULE_SEGMENTS[module]:
        twists = _twist_joints(side, module, label)
        if not twists:
            continue
        top_j, end_j = _jnt(side, top_part), _jnt(side, end_part)
        prefix = "{}_{}_{}".format(side, module, label)
        if kind == "upper":
            reader = lrb.twist_reader(prefix + "Twist", top_j)
        else:
            reader = lrb.twist_reader(prefix + "Twist", end_j, ref=top_j)
        n = len(twists)
        for i, tj in enumerate(twists):
            frac = (i + 1) / float(n + 1)
            weight = -(1.0 - frac) if kind == "upper" else frac
            mdl = mc.createNode("multDoubleLinear",
                                name="{}Twist{}_w".format(prefix, i + 1))
            mc.setAttr(mdl + ".input2", weight)
            mc.connectAttr(reader, mdl + ".input1")
            mc.connectAttr(mdl + ".output", tj + ".rotateX", force=True)
            driven += 1
    return driven


# ------------------------------------------------------------ twist: ribbon
def _drive_twists_ribbon(side, module):
    """Drive the module's skeleton twists from ribbon surfaces (uvPin)."""
    segs = MODULE_SEGMENTS[module]
    (lab0, a, b, _), (lab1, _b, c, _k) = segs
    bind = [_jnt(side, p) for p in (a, b, c)]
    existing = {"thighRibbon": _twist_joints(side, module, lab0),
                "shinRibbon": _twist_joints(side, module, lab1)}
    if not any(existing.values()):
        return 0
    P = {"Thigh": mc.xform(bind[0], q=True, ws=True, t=True),
         "Knee": mc.xform(bind[1], q=True, ws=True, t=True),
         "Ankle": mc.xform(bind[2], q=True, ws=True, t=True)}
    plane = lrb.norm(lrb.cross(lrb.sub(P["Knee"], P["Thigh"]),
                               lrb.sub(P["Ankle"], P["Knee"])))
    top = _module_grp(side, module)
    lyr = "{}_{}_ribbon_lyr".format(side, module.lower())
    if not mc.objExists(lyr):
        lyr = mc.createDisplayLayer(name=lyr, empty=True)
    glob = (mc.listRelatives(bind[0], parent=True) or [top])[0]
    rig = {"bind": bind, "plane": plane, "top": top, "glob": glob,
           "layers": (lyr, lyr)}
    out = leg_ribbon.add_ribbons("{}_{}_".format(side, module.lower()),
                                 rig, P, mid_ctrl=True, existing=existing)
    return len(out["joints"]) if out else 0


def _add_twist(side, module, mode):
    if mode == "none":
        return None
    has_any = any(_twist_joints(side, module, label)
                  for label, _t, _e, _k in MODULE_SEGMENTS[module])
    if not has_any:
        mc.warning("No {} twist joints in the skeleton for side {}. "
                   "Redirect: run '{}' with twists/segment > 0."
                   .format(module, side, scene_meta.label("skeleton")))
        return 0
    if mode == "roll":
        return _drive_twists_roll(side, module)
    if mode == "ribbon":
        return _drive_twists_ribbon(side, module)
    return None


# --------------------------------------------------------------------- arms
def build_arm(side, twist="none"):
    parts = ("Clavicle", "Shoulder", "Elbow", "Wrist")
    missing = _missing(side, parts)
    if missing:
        _redirect_missing(missing)
        return None
    mc.select([_jnt(side, p) for p in parts])
    rig_op_arm_ikfk_switch.RigOps_ArmIKFKSwitch(side)
    grp = _module_grp(side, "Arm")
    extras = {"twist": twist, "twists_driven": _add_twist(side, "Arm", twist)}
    scene_meta.record("arm_" + side, nodes=[grp], info=extras)
    logger.info("Arm setup complete for side %s (%s)", side, extras)
    return [grp]


# --------------------------------------------------------------------- legs
def _heel_guide(side):
    for candidate in ("{}_Heel".format(side), "{}_Heel_BN".format(side),
                      "{}_Heel_GUIDE".format(side)):
        if mc.objExists(candidate):
            return candidate
    ankle = mc.xform(_jnt(side, "Ankle"), q=True, ws=True, t=True)
    toe = mc.xform(_jnt(side, "Toe"), q=True, ws=True, t=True)
    foot_len = abs(toe[2] - ankle[2]) or 10.0
    heel = mc.spaceLocator(name="{}_Heel_GUIDE".format(side))[0]
    mc.xform(heel, ws=True, t=(ankle[0], 0.0, ankle[2] - foot_len * 0.4))
    logger.info("Created heel guide %s", heel)
    return heel


def build_leg(side, twist="none"):
    missing = _missing(side, ("Thigh", "Calf", "Ankle", "Ball", "Toe"))
    if missing:
        _redirect_missing(missing)
        return None

    rig_op_leg_ikfk_switch.RigOps_LegIKFKSwitch(side)
    heel = _heel_guide(side)
    mc.select([_jnt(side, "Ankle"), _jnt(side, "Ball"),
               _jnt(side, "Toe"), heel])
    rig_op_reverse_foot.build_reverse_foot(side)

    grp = _module_grp(side, "Leg")
    # the reverse foot is part of the leg module
    _into_group("{}_Foot_ReverseFoot_GRP".format(side), grp)
    extras = {"twist": twist, "twists_driven": _add_twist(side, "Leg", twist)}
    scene_meta.record("leg_" + side, nodes=[grp], info=extras)
    logger.info("Leg setup complete for side %s (%s)", side, extras)
    return [grp]


# -------------------------------------------------------------------- torso
def _spine_chain():
    chain = [j for j in ("Pelvis_BN_JNT", "Spine1_BN_JNT", "Spine2_BN_JNT",
                         "Spine3_BN_JNT", "Chest_BN_JNT") if mc.objExists(j)]
    if len(chain) < 3:
        mc.warning("Spine chain not found (need Pelvis/Spine*/Chest "
                   "BN_JNT). Redirect: run '{}' first."
                   .format(scene_meta.label("skeleton")))
        return None
    return chain


def build_torso(mode):
    chain = _spine_chain()
    if not chain:
        return None
    grp = "Torso_Grp"
    if not mc.objExists(grp):
        grp = mc.group(empty=True, name=grp)
    _into_group(grp, _top_grp())
    built = []
    if mode == "fk":
        mc.select(chain)
        controls = rig_ops_create_controls.create_fk_controls("BN_JNT")
        if controls:
            root_grp = (mc.listRelatives(controls[0], parent=True) or [None])[0]
            _into_group(root_grp, grp)
            built = controls
    elif mode == "spline":
        handle, effector, curve = mc.ikHandle(
            name="Torso_Spline_IKS", solver="ikSplineSolver",
            startJoint=chain[0], endEffector=chain[-1],
            createCurve=True, simplifyCurve=True, numSpans=2)
        curve = mc.rename(curve, "Torso_Spline_CRV")
        for n in (handle, curve):
            _into_group(n, grp)
        built = [grp]
        mc.warning("Base spline IK built (no controls yet); cluster or "
                   "skin Torso_Spline_CRV to drive it.")
    elif mode == "ribbon":
        mc.select(chain)
        spine_ops_ribbon_spine.build_ribbon_spine(2.0)
        for n in ("RibbonSpine_GRP", "Spine_Ribbon_GRP"):
            _into_group(n, grp)
        built = [grp]
    scene_meta.record("torso", nodes=[grp], info={"build": mode})
    logger.info("Torso setup complete (%s)", mode)
    return built or True
