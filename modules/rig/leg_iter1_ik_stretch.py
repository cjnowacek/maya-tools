"""Leg rig iteration 1: stretchy IK leg with a reverse foot.

The baseline the later iterations build on:
  * rig (driver) chain + bind chain, bind driven by parent/scale constraints
  * RP solver hip -> ankle, SC solvers ankle -> ball -> toe
  * reverse foot: heel / toe / ball-roll / toe-wiggle pivots under the foot ctrl
  * stretch that only ever lengthens, normalised against the world control's
    scale so scaling the rig does not trigger it
  * bind skeleton parented OUTSIDE the world control to avoid double transforms

Expects six guide locators named <guide_prefix>Thigh, Knee, Ankle, Ball, Toe,
Heel. Build with the guides in their rest pose.
"""
import logging

import maya.cmds as cmds

from modules.rig.Lib import leg_rig_builder as lrb

logger = logging.getLogger(__name__)


TOOL_META = {
    "description": (
        'Stretchy IK leg with a reverse foot (iteration 1, the baseline).\n\n'
        'Needs six guide locators named <guide prefix>Thigh, Knee, Ankle, '
        'Ball, Toe, Heel in rest pose. Builds rig + bind chains with a '
        'root joint, RP/SC IK, reverse-foot pivots, and stretch that only '
        'lengthens and ignores global scale. Bind skeleton sits outside '
        'the world control to avoid double transforms.'
    ),
    "params": {'guide_prefix': {'label': 'guide prefix',
                      'tooltip': 'Prefix on the six guide locators.'},
     'rig_prefix': {'label': 'rig prefix',
                    'tooltip': 'Prefix for every node the build '
                               'creates.'}},
}


def collect_guides(guide_prefix):
    guides = {}
    for g in lrb.NEEDED:
        loc = guide_prefix + g
        if not cmds.objExists(loc):
            raise RuntimeError('missing guide locator: ' + loc)
        guides[g] = cmds.xform(loc, q=True, ws=True, t=True)
    return guides


def main(guide_prefix='', rig_prefix='leg_', *args):
    """guide_prefix  prefix on the six guide locators
       rig_prefix    prefix for every node the build creates"""
    rig = lrb.build_leg(rig_prefix, collect_guides(guide_prefix), roll_joints=0)
    logger.info('built %s: %d bind joints, no twist joints', rig_prefix, len(rig['bind']))
    return rig
