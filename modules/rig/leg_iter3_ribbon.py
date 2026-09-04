"""Leg rig iteration 3: stretchy IK + reverse foot + NURBS ribbon segments.

Adds to iteration 2: the discrete roll joints are replaced by a NURBS ribbon
per limb segment. Each segment is a surface skinned to three drivers
(top / mid / bottom) with the bind joints pinned to it via one `uvPin`.

The ribbon supplies twist interpolation from the surface itself, so the
quaternion twist-extraction network that iteration 2 needed is gone. It also
adds a mid control per segment for bulge and S-curves, which the roll joints
could not do.

Expects six guide locators named <guide_prefix>Thigh, Knee, Ankle, Ball, Toe,
Heel. Build with the guides in their rest pose.
"""
import logging

import maya.cmds as cmds

from modules.rig.Lib import leg_rig_builder as lrb
from modules.rig.Lib import leg_ribbon

logger = logging.getLogger(__name__)

# Read by the toolset UI (core/toolset_master.py): description fills the
# collapsible panel, params refine the auto-generated input widgets.
TOOL_META = {
    "description": (
        "Stretchy IK leg with reverse foot and NURBS ribbon segments.\n\n"
        "Needs six guide locators named <guide prefix>Thigh, Knee, Ankle, "
        "Ball, Toe, Heel placed in the rest pose. Builds rig + bind chains, "
        "a root joint (game-export ready), and one ribbon per limb segment "
        "with a uvPin: twist interpolates from the surface, and each segment "
        "gets a mid control for bulge and S-curves."
    ),
    "params": {
        "guide_prefix": {
            "label": "guide prefix",
            "tooltip": "Prefix on the six guide locators (e.g. 'leg3_' finds leg3_Thigh).",
        },
        "rig_prefix": {
            "label": "rig prefix",
            "tooltip": "Prefix for every node the build creates.",
        },
        "joints_per_segment": {
            "label": "joints / segment",
            "min": 3,
            "max": 9,
            "tooltip": "Bind joints pinned along each ribbon. 5 is the usual pick.",
        },
        "mid_ctrl": {
            "label": "mid control",
            "choices": [1, 0],
            "tooltip": "1: expose an animator control at each segment midpoint.",
        },
    },
}


def main(guide_prefix='leg3_', rig_prefix='leg3_', joints_per_segment=5,
         mid_ctrl=1, *args):
    """Build the ribbon leg.

    guide_prefix       prefix on the six guide locators
    rig_prefix         prefix for every node the build creates
    joints_per_segment bind joints pinned to each ribbon (5 is the usual pick)
    mid_ctrl           1 to expose an animator control at each segment mid
    """
    joints_per_segment = int(joints_per_segment)
    guides = {}
    for g in lrb.NEEDED:
        loc = guide_prefix + g
        if not cmds.objExists(loc):
            raise RuntimeError('missing guide locator: ' + loc)
        guides[g] = cmds.xform(loc, q=True, ws=True, t=True)

    rig = lrb.build_leg(rig_prefix, guides, roll_joints=0)
    rib = leg_ribbon.add_ribbons(rig_prefix, rig, guides,
                                 joints_per_segment=joints_per_segment,
                                 mid_ctrl=bool(int(mid_ctrl)))
    rig['ribbon'] = rib
    logger.info('built %s: %d ribbon bind joints, %d mid controls',
                rig_prefix, len(rib['joints']), len(rib['mid_ctrls']))
    return rig
