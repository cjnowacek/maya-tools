"""Create twist/roll joints along an arm-style chain.

Select four joints IN ORDER: root (e.g. clavicle), upper (shoulder), mid
(elbow), and end (wrist). Twist joints are distributed between upper->mid
and mid->end, driven by single-chain IK "reader" joints plus orient
constraints that isolate the twist axis (X down the chain).
"""

import logging

import maya.cmds as mc
from maya import OpenMaya as om

logger = logging.getLogger(__name__)


TOOL_META = {
    "description": (
        'Create twist/roll joints along an arm-style chain.\n\n'
        'Select four joints IN ORDER: root (clavicle), upper (shoulder), '
        'mid (elbow), end (wrist). Twist joints are distributed along '
        'upper-mid and mid-end, driven by SC-IK reader joints and orient '
        'constraints isolating the twist axis (X down the chain).'
    ),
    "params": {'twist_joint_count': {'label': 'twists / segment',
                           'min': 1,
                           'max': 8,
                           'tooltip': 'Twist joints per limb '
                                      'segment.'},
     'name': {'label': 'name',
              'tooltip': 'Name token for the created twist joints.'}},
}


def main(twist_joint_count=2, name="twist", *args):
    try:
        twist_joint_count = int(twist_joint_count)
    except (TypeError, ValueError):
        twist_joint_count = 2
    create_roll_joints(twist_joint_count, name or "twist")


def create_roll_joints(twist_joint_count=2, name="twist"):
    sel = mc.ls(sl=True, type="joint")
    if len(sel) < 4:
        mc.warning("Select four joints in order: root, upper, mid, end.")
        return None
    if not 1 <= twist_joint_count <= 5:
        mc.warning("Twist joint count must be between 1 and 5.")
        return None

    bn0, bn1, bn2, bn3 = sel[:4]
    joint_size = mc.getAttr(bn0 + ".radius")
    rig_group = mc.group(em=True, n="{}_Twist_GRP".format(name))

    bn1_mat = mc.xform(bn1, q=True, m=True, ws=True)
    bn2_mat = mc.xform(bn2, q=True, m=True, ws=True)
    bn3_mat = mc.xform(bn3, q=True, m=True, ws=True)
    bn2_pos = mc.xform(bn2, q=True, t=True, ws=True)

    root_vec = om.MVector(*mc.xform(bn1, q=True, ws=True, t=True))
    mid_vec = om.MVector(*mc.xform(bn2, q=True, ws=True, t=True))
    end_vec = om.MVector(*mc.xform(bn3, q=True, ws=True, t=True))

    # Twist "reader" chains: root-to-mid and end-to-mid single-chain IK
    mc.select(cl=True)
    rtm_ik_1 = mc.joint(n="{}_RTM_Twist_IK1_JNT".format(name), rad=joint_size * 2)
    rtm_ik_2 = mc.joint(n="{}_RTM_Twist_IK2_JNT".format(name), rad=joint_size * 2)
    mc.parent(rtm_ik_1, rig_group)
    mc.select(cl=True)
    etm_ik_1 = mc.joint(n="{}_ETM_Twist_IK1_JNT".format(name), rad=joint_size * 2)
    etm_ik_2 = mc.joint(n="{}_ETM_Twist_IK2_JNT".format(name), rad=joint_size * 2)
    mc.parent(etm_ik_1, rig_group)
    mc.select(cl=True)

    mc.xform(rtm_ik_1, m=bn1_mat, ws=True)
    mc.xform(rtm_ik_2, m=bn1_mat, ws=True)
    mc.xform(rtm_ik_2, t=bn2_pos, ws=True)
    mc.xform(etm_ik_1, m=bn3_mat, ws=True)
    mc.xform(etm_ik_2, m=bn2_mat, ws=True)

    # Evenly spaced positions for the twist joints along each span
    def span_positions(start_vec, end_vec_):
        span = end_vec_ - start_vec
        step = span / (twist_joint_count + 1)
        return [start_vec + step * (i + 1) for i in range(twist_joint_count)]

    rtm_joints = []
    for i, pos in enumerate(span_positions(root_vec, mid_vec), start=1):
        jnt = mc.joint(n="{}_RTM_Twist_BN{}_JNT".format(name, i))
        mc.xform(jnt, m=bn1_mat, ws=True)
        mc.move(pos.x, pos.y, pos.z, jnt)
        mc.select(cl=True)
        mc.parent(jnt, bn1)
        rtm_joints.append(jnt)

    etm_joints = []
    for i, pos in enumerate(span_positions(mid_vec, end_vec), start=1):
        jnt = mc.joint(n="{}_ETM_Twist_BN{}_JNT".format(name, i))
        mc.xform(jnt, m=bn2_mat, ws=True)
        mc.move(pos.x, pos.y, pos.z, jnt)
        mc.select(cl=True)
        mc.parent(jnt, bn2)
        etm_joints.append(jnt)

    # IK handles keep the reader chains aimed at the mid joint
    rtm_handle = mc.ikHandle(
        name="{}_RTM_IKS".format(name), sol="ikSCsolver", sj=rtm_ik_1, ee=rtm_ik_2
    )[0]
    etm_handle = mc.ikHandle(
        name="{}_ETM_IKS".format(name), sol="ikSCsolver", sj=etm_ik_1, ee=etm_ik_2
    )[0]

    mc.parent(rtm_ik_1, rtm_handle, bn0)
    mc.parent(etm_ik_1, etm_handle, bn3)
    mc.pointConstraint(bn2, rtm_handle, mo=False)
    mc.pointConstraint(bn2, etm_handle, mo=False)

    # Blend each twist joint between the bind joint and its twist reader,
    # constraining only rotateX (the twist axis)
    for jnt in rtm_joints:
        mc.orientConstraint(bn1, rtm_ik_1, jnt, mo=True, skip=["y", "z"])
    for jnt in etm_joints:
        mc.orientConstraint(bn3, etm_ik_1, jnt, mo=True, skip=["y", "z"])

    mc.delete(rig_group)
    mc.select(cl=True)

    logger.debug("Twist joints: %s %s", rtm_joints, etm_joints)
    mc.inViewMessage(
        amg="Twist joints built: tune the orient-constraint weights to "
        "distribute the twist falloff.",
        pos="topCenter",
        fade=True,
    )
    return rtm_joints + etm_joints
