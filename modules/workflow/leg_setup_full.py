"""Leg IKFK switch + reverse foot in one run.

Composite of: Rig Op Leg IKFK Switch, then Rig Op Reverse Foot, with the
selection glue handled automatically (ankle/ball/toe joints found by name, a
heel guide created at ground level behind the ankle if none exists).
"""
import logging

import maya.cmds as mc

from modules.rig.Lib import scene_meta
from modules.wip import rig_op_leg_ikfk_switch
from modules.wip import rig_op_reverse_foot

logger = logging.getLogger(__name__)

TOOL_META = {
    "order": 2,
    "description": (
        "Full leg setup: IKFK switch, pole vector, reverse foot.\n\n"
        "Runs the Leg IKFK builder (needs {side}_Thigh/Calf/Ankle_BN_JNT), "
        "then the reverse foot on {side}_Ankle/Ball/Toe_BN_JNT. If no "
        "{side}_Heel guide exists, one is created at ground level behind "
        "the ankle (40% of foot length).\n\n"
        "Run AFTER: Skeleton From Guides.\n"
        "Assumes the character faces +Z."
    ),
    "params": {
        "side": {
            "label": "side",
            "choices": ["L", "R"],
            "tooltip": "Which leg to build.",
        },
    },
}


def main(side="L", *args):
    return build_leg(side or "L")


def _heel_guide(side):
    for candidate in ("{}_Heel".format(side), "{}_Heel_BN".format(side),
                      "{}_Heel_GUIDE".format(side)):
        if mc.objExists(candidate):
            return candidate
    ankle = mc.xform("{}_Ankle_BN_JNT".format(side), q=True, ws=True, t=True)
    toe = mc.xform("{}_Toe_BN_JNT".format(side), q=True, ws=True, t=True)
    foot_len = abs(toe[2] - ankle[2]) or 10.0
    heel = mc.spaceLocator(name="{}_Heel_GUIDE".format(side))[0]
    mc.xform(heel, ws=True, t=(ankle[0], 0.0, ankle[2] - foot_len * 0.4))
    logger.info("Created heel guide %s", heel)
    return heel


def build_leg(side="L"):
    step = "leg_" + side
    if scene_meta.done(step):
        existing = scene_meta.linked(step)
        _, nxt = scene_meta.next_step()
        mc.warning("{} leg already built ({}). Next step: {}".format(
            side, ", ".join(existing) or "?", nxt or "see Scene Status"))
        if existing:
            mc.select(existing)
        return existing or None

    required = ["{}_{}_BN_JNT".format(side, p) for p in
                ("Thigh", "Calf", "Ankle", "Ball", "Toe")]
    if not scene_meta.done("skeleton"):
        logger.warning("Meta node has no skeleton step recorded; "
                       "checking joints by name instead.")
    missing = [j for j in required if not mc.objExists(j)]
    if missing:
        mc.warning("Missing bind joints. Redirect: run '{}' first. Missing: {}".format(
            scene_meta.label("skeleton"), ", ".join(missing)))
        return None

    rig_op_leg_ikfk_switch.RigOps_LegIKFKSwitch(side)

    heel = _heel_guide(side)
    mc.select(["{}_Ankle_BN_JNT".format(side), "{}_Ball_BN_JNT".format(side),
               "{}_Toe_BN_JNT".format(side), heel])
    result = rig_op_reverse_foot.build_reverse_foot(side)
    built = [n for n in ("{}_Leg_Grp".format(side),
                         "{}_Foot_ReverseFoot_GRP".format(side)) if mc.objExists(n)]
    scene_meta.record("leg_" + side, nodes=built)
    logger.info("Leg setup complete for side %s", side)
    return result
