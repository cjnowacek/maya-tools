"""Leg rig iteration 2: iteration 1 plus discrete roll (twist) joints.

Adds N roll joints to the thigh and shin:
  * thigh rolls COUNTER-rotate the femur twist (100%, 67%, 33% ...) so the hip
    end stays put while the knee end follows
  * shin rolls FOLLOW the ankle twist (33%, 67%, 100% ...) so the calf stays
    put while the ankle end follows
  * both slide along the bone when the leg stretches

Twist comes from a swing-twist decomposition (multMatrix delta -> decompose ->
quaternion isolated to X -> quatToEuler), not from Euler channels. The matrix
order matters: restInverse * current, so the delta lands in the PARENT's frame
whose X runs down the bone. The other order reads roughly 45% of the true
twist. Superseded by iteration 3, where the ribbon surface supplies twist
directly and none of this network is needed.

Expects six guide locators named <guide_prefix>Thigh, Knee, Ankle, Ball, Toe,
Heel. Build with the guides in their rest pose.
"""
import logging

from modules.rig.Lib import leg_rig_builder as lrb

from modules.rig.leg_iter1_ik_stretch import collect_guides

logger = logging.getLogger(__name__)


TOOL_META = {
    "description": (
        'Iteration 1 plus discrete roll (twist) joints.\n\n'
        'Adds N twist joints per segment: thigh rolls counter-rotate the '
        'femur so the hip end stays put; shin rolls follow the ankle. '
        'Driven by swing-twist matrix decomposition, and they slide along '
        "the bone when the leg stretches. Superseded by iteration 3's "
        'ribbon, which gets twist from a surface instead.'
    ),
    "params": {'guide_prefix': {'label': 'guide prefix',
                      'tooltip': 'Prefix on the six guide locators.'},
     'rig_prefix': {'label': 'rig prefix',
                    'tooltip': 'Prefix for every node the build '
                               'creates.'},
     'roll_joints': {'label': 'rolls / segment',
                     'min': 1,
                     'max': 9,
                     'tooltip': 'Twist joints per limb segment.'}},
}


def main(guide_prefix='leg2_', rig_prefix='leg2_', roll_joints=3, *args):
    """guide_prefix  prefix on the six guide locators
       rig_prefix    prefix for every node the build creates
       roll_joints   twist joints per segment"""
    rig = lrb.build_leg(rig_prefix, collect_guides(guide_prefix),
                        roll_joints=int(roll_joints))
    logger.info('built %s: %d bind joints, %d roll joints',
                rig_prefix, len(rig['bind']), len(rig['rolls']))
    return rig
