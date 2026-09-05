"""Body setup: arms, legs, and torso from one panel.

Replaces Leg Setup Full. Each body part offers its BUILD as radio choices
(mutually exclusive) per the tool contract; sides applies to arms and legs.

  arms   build: none | ikfk            twist: none | roll | ribbon
  legs   build: none | ikfk + foot     twist: none | roll | ribbon
  torso  build: none | fk | spline ik | ribbon

Wraps: Rig Op Arm/Leg IKFK Switch, Rig Op Reverse Foot, Rig Ops Create Roll
Joints, the Lib ribbon builder, Rig Ops Create Controls, Spine Ops Ribbon
Spine. All selection glue is handled (chains found by BN_JNT name, heel
guide auto-created, spine chain assembled pelvis->chest).
"""
import logging

import maya.cmds as mc

from modules.rig.Lib import scene_meta
from modules.rig.Lib import leg_rig_builder as lrb
from modules.rig.Lib import leg_ribbon
from modules.wip import rig_op_arm_ikfk_switch
from modules.wip import rig_op_leg_ikfk_switch
from modules.wip import rig_op_reverse_foot
from modules.wip import rig_ops_create_roll_joints
from modules.wip import rig_ops_create_controls
from modules.wip import spine_ops_ribbon_spine

logger = logging.getLogger(__name__)

TOOL_META = {
    "order": 2,
    "description": (
        "Build arms, legs, and torso over the BN skeleton, in one run.\n\n"
        "Pick a BUILD per body part (radio, mutually exclusive) and a twist "
        "solution for the limbs. Legs include the reverse foot (a "
        "{side}_Heel guide is created at ground level if none exists). "
        "Torso spline ik is a base ikSplineSolver setup without controls "
        "yet.\n\n"
        "Run AFTER: Build Biped.\n"
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
            "tooltip": "Roll: discrete twist joints. Ribbon: uvPin surface.",
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
            "tooltip": "Roll: discrete twist joints. Ribbon: uvPin surface.",
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

# limb -> (roll chain: root/upper/mid/end, ribbon triple: start/mid/end)
LIMBS = {
    "arm": (("Clavicle", "Shoulder", "Elbow", "Wrist"),
            ("Shoulder", "Elbow", "Wrist")),
    "leg": ((None, "Thigh", "Calf", "Ankle"),   # root = thigh's parent
            ("Thigh", "Calf", "Ankle")),
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


def _add_twist(side, limb, mode):
    if mode == "roll":
        (root, upper, mid, end), _ = LIMBS[limb]
        upper_j = _jnt(side, upper)
        root_j = (_jnt(side, root) if root
                  else (mc.listRelatives(upper_j, parent=True) or [upper_j])[0])
        mc.select([root_j, upper_j, _jnt(side, mid), _jnt(side, end)])
        return bool(rig_ops_create_roll_joints.create_roll_joints(
            2, "{}_{}".format(side, limb.capitalize())))
    if mode == "ribbon":
        _, (a, b, c) = LIMBS[limb]
        bind = [_jnt(side, p) for p in (a, b, c)]
        P = {"Thigh": mc.xform(bind[0], q=True, ws=True, t=True),
             "Knee": mc.xform(bind[1], q=True, ws=True, t=True),
             "Ankle": mc.xform(bind[2], q=True, ws=True, t=True)}
        plane = lrb.norm(lrb.cross(lrb.sub(P["Knee"], P["Thigh"]),
                                   lrb.sub(P["Ankle"], P["Knee"])))
        top = "{}_{}_Grp".format(side, limb.capitalize())
        if not mc.objExists(top):
            top = mc.group(empty=True, name=top)
        lyr = "{}_{}_ribbon_lyr".format(side, limb)
        if not mc.objExists(lyr):
            lyr = mc.createDisplayLayer(name=lyr, empty=True)
        glob = (mc.listRelatives(bind[0], parent=True) or [top])[0]
        rig = {"bind": bind, "plane": plane, "top": top, "glob": glob,
               "layers": (lyr, lyr)}
        return bool(leg_ribbon.add_ribbons(
            "{}_{}_".format(side, limb), rig, P,
            joints_per_segment=5, mid_ctrl=True))
    return False


# --------------------------------------------------------------------- arms
def build_arm(side, twist="none"):
    parts = ("Clavicle", "Shoulder", "Elbow", "Wrist")
    missing = _missing(side, parts)
    if missing:
        _redirect_missing(missing)
        return None
    mc.select([_jnt(side, p) for p in parts])
    rig_op_arm_ikfk_switch.RigOps_ArmIKFKSwitch(side)
    extras = {"twist": twist}
    if twist != "none":
        extras["twist_built"] = _add_twist(side, "arm", twist)
    built = [n for n in ("{}_Arm_Grp".format(side),) if mc.objExists(n)]
    scene_meta.record("arm_" + side, nodes=built, info=extras)
    logger.info("Arm setup complete for side %s (%s)", side, extras)
    return built or True


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

    extras = {"twist": twist}
    if twist != "none":
        extras["twist_built"] = _add_twist(side, "leg", twist)
    built = [n for n in ("{}_Leg_Grp".format(side),
                         "{}_Foot_ReverseFoot_GRP".format(side))
             if mc.objExists(n)]
    scene_meta.record("leg_" + side, nodes=built, info=extras)
    logger.info("Leg setup complete for side %s (%s)", side, extras)
    return built or True


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
    built = []
    if mode == "fk":
        mc.select(chain)
        controls = rig_ops_create_controls.create_fk_controls("BN_JNT")
        built = controls or []
    elif mode == "spline":
        handle, effector, curve = mc.ikHandle(
            name="Torso_Spline_IKS", solver="ikSplineSolver",
            startJoint=chain[0], endEffector=chain[-1],
            createCurve=True, simplifyCurve=True, numSpans=2)
        curve = mc.rename(curve, "Torso_Spline_CRV")
        grp = mc.group([handle, curve], name="Torso_Spline_GRP")
        built = [grp]
        mc.warning("Base spline IK built (no controls yet); cluster or "
                   "skin Torso_Spline_CRV to drive it.")
    elif mode == "ribbon":
        mc.select(chain)
        spine_ops_ribbon_spine.build_ribbon_spine(2.0)
        built = [n for n in ("RibbonSpine_GRP", "Spine_Ribbon_GRP")
                 if mc.objExists(n)]
    scene_meta.record("torso", nodes=built, info={"build": mode})
    logger.info("Torso setup complete (%s)", mode)
    return built or True
