"""
#-------------------------------------------------------------#
#Leg Auto rig

Builds out the IKFK fuctionality on top of existing BN joints

Current feature are:
Auto IKFK Switch
Auto Pole Vector

Future Plans:
Auto Roll Joints
#-------------------------------------------------------------#
"""


import maya.cmds as mc
import maya.mel as mel
from maya import OpenMaya as om
from maya import OpenMayaUI as omui

def main():
    RigOps_LegIKFKSwitch()
    
rigType = "Leg"
side = ""
controlerSize = 6


def RigOps_LegIKFKSwitch(side="L"):
    rigGroup = mc.group(em=True, n="{}_Leg_Grp".format(side))
    name = side + rigType

    # getting xform data from bind joints
    xform0 = mc.xform("{}_Thigh_BN_JNT".format(side), q=True, m=True, ws=True)
    xform1 = mc.xform("{}_Calf_BN_JNT".format(side), q=True, m=True, ws=True)
    xform2 = mc.xform("{}_Ankle_BN_JNT".format(side), q=True, m=True, ws=True)

    # getting xform data from bind joints
    BN0_mat = mc.xform("{}_Thigh_BN_JNT".format(side), q=True, m=True, ws=True)
    BN1_mat = mc.xform("{}_Calf_BN_JNT".format(side), q=True, m=True, ws=True)
    BN2_mat = mc.xform("{}_Ankle_BN_JNT".format(side), q=True, m=True, ws=True)

    BN0_pos = mc.xform("{}_Thigh_BN_JNT".format(side), q=True, t=True, ws=True)
    BN1_pos = mc.xform("{}_Calf_BN_JNT".format(side), q=True, t=True, ws=True)
    BN2_pos = mc.xform("{}_Ankle_BN_JNT".format(side), q=True, t=True, ws=True)

    # Duplicate Base Arm

    mc.duplicate(
        "{}_Thigh_BN_JNT".format(side),
        n="{}_Thigh_BN_JNT".format(side).replace("BN", "DRIVER"),
        po=True,
    )[0]
    mc.duplicate(
        "{}_Calf_BN_JNT".format(side),
        n="{}_Calf_BN_JNT".format(side).replace("BN", "DRIVER"),
        po=True,
    )[0]
    mc.duplicate(
        "{}_Ankle_BN_JNT".format(side),
        n="{}_Ankle_BN_JNT".format(side).replace("BN", "DRIVER"),
        po=True,
    )[0]

    mc.duplicate(
        "{}_Thigh_BN_JNT".format(side),
        n="{}_Thigh_BN_JNT".format(side).replace("BN", "FK"),
        po=True,
    )[0]
    mc.duplicate(
        "{}_Calf_BN_JNT".format(side),
        n="{}_Calf_BN_JNT".format(side).replace("BN", "FK"),
        po=True,
    )[0]
    mc.duplicate(
        "{}_Ankle_BN_JNT".format(side),
        n="{}_Ankle_BN_JNT".format(side).replace("BN", "FK"),
        po=True,
    )[0]

    mc.duplicate(
        "{}_Thigh_BN_JNT".format(side),
        n="{}_Thigh_BN_JNT".format(side).replace("BN", "IK"),
        po=True,
    )[0]
    mc.duplicate(
        "{}_Calf_BN_JNT".format(side),
        n="{}_Calf_BN_JNT".format(side).replace("BN", "IK"),
        po=True,
    )[0]
    mc.duplicate(
        "{}_Ankle_BN_JNT".format(side),
        n="{}_Ankle_BN_JNT".format(side).replace("BN", "IK"),
        po=True,
    )[0]

    mc.parent(
        "{}_Ankle_BN_JNT".format(side).replace("BN", "DRIVER"),
        "{}_Calf_BN_JNT".format(side).replace("BN", "DRIVER"),
    )
    mc.parent(
        "{}_Calf_BN_JNT".format(side).replace("BN", "DRIVER"),
        "{}_Thigh_BN_JNT".format(side).replace("BN", "DRIVER"),
    )
    mc.parent("{}_Thigh_BN_JNT".format(side).replace("BN", "DRIVER"), rigGroup)
    mc.parent(
        "{}_Ankle_BN_JNT".format(side).replace("BN", "FK"),
        "{}_Calf_BN_JNT".format(side).replace("BN", "FK"),
    )
    mc.parent(
        "{}_Calf_BN_JNT".format(side).replace("BN", "FK"),
        "{}_Thigh_BN_JNT".format(side).replace("BN", "FK"),
    )
    mc.parent("{}_Thigh_BN_JNT".format(side).replace("BN", "FK"), rigGroup)
    mc.parent(
        "{}_Ankle_BN_JNT".format(side).replace("BN", "IK"),
        "{}_Calf_BN_JNT".format(side).replace("BN", "IK"),
    )
    mc.parent(
        "{}_Calf_BN_JNT".format(side).replace("BN", "IK"),
        "{}_Thigh_BN_JNT".format(side).replace("BN", "IK"),
    )
    mc.parent("{}_Thigh_BN_JNT".format(side).replace("BN", "IK"), rigGroup)

    # Create FK chain list

    chainList = []
    chainList.append("{}_Thigh_BN_JNT".format(side).replace("BN", "FK"))
    chainList.append("{}_Calf_BN_JNT".format(side).replace("BN", "FK"))
    chainList.append("{}_Ankle_BN_JNT".format(side).replace("BN", "FK"))
    mc.select(cl=True)

    newchainList = []
    topnode = []
    controlList = []

    sdkcheck = 0
    offcheck = 0

    for i in chainList:

        if "BN_JNT" in i:
            namereplace = "BN_JNT"
        elif "FK_JNT" in i:
            namereplace = "FK_JNT"
        elif "IK_JNT" in i:
            namereplace = "IK_JNT"

        con = mc.circle(
            n=i.replace(namereplace, "CON"), nr=[1, 0, 0], sw=360, r=controlerSize
        )
        if sdkcheck:
            sdkgrp = mc.group(n=i.replace(namereplace, "SDK_GRP"))
        if offcheck:
            offgrp = mc.group(n=i.replace(namereplace, "OFF_GRP"))
        grp = mc.group(n=i.replace(namereplace, "GRP"))
        const = mc.parentConstraint(i, grp, mo=0)
        mc.delete(const)
        mc.parentConstraint(con, i, mo=True)

        newchainList.append(grp)
        newchainList.append(con[0])
        controlList.append(con[0])
        topnode.append(grp)

    # connect fk controls

    newchainList.pop(0)

    for i in range(int(len(newchainList) / 2)):
        i = i * 2
        mc.parent(newchainList[i + 1], newchainList[i])

    mc.parent(topnode[0], rigGroup)

    # create ik
    IKR_GRP = mc.createNode("transform", n="{}_Leg_IKR_GRP".format(side))

    IKR_Handle = mc.ikHandle(
        n="{}_Leg_IKR".format(side),
        sol="ikRPsolver",
        sj="{}_Thigh_BN_JNT".format(side).replace("BN", "IK"),
        ee="{}_Ankle_BN_JNT".format(side).replace("BN", "IK"),
    )[0]

    # Create Control
    IKR_ankle_control = mc.curve(
        n="{}_Leg_ik_CON".format(side),
        d=1,
        p=[
            [-0.989623460780981, 1.0031016006564133, 1.0031016006564133],
            [-0.989623460780981, 1.0031016006564133, -1.0031016006564133],
            [-0.989623460780981, -1.0031016006564133, -1.0031016006564133],
            [-0.989623460780981, -1.0031016006564133, 1.0031016006564133],
            [-0.989623460780981, 1.0031016006564133, 1.0031016006564133],
            [0.989623460780981, 1.0031016006564133, 1.0031016006564133],
            [0.989623460780981, -1.0031016006564133, 1.0031016006564133],
            [-0.989623460780981, -1.0031016006564133, 1.0031016006564133],
            [0.989623460780981, -1.0031016006564133, 1.0031016006564133],
            [0.989623460780981, -1.0031016006564133, -1.0031016006564133],
            [0.989623460780981, 1.0031016006564133, -1.0031016006564133],
            [-0.989623460780981, 1.0031016006564133, -1.0031016006564133],
            [-0.989623460780981, -1.0031016006564133, -1.0031016006564133],
            [0.989623460780981, -1.0031016006564133, -1.0031016006564133],
            [0.989623460780981, 1.0031016006564133, -1.0031016006564133],
            [0.989623460780981, 1.0031016006564133, 1.0031016006564133],
        ],
    )
    # ik rotate control creation
    ik_rotate_control = mc.circle(
        n="{}_ik_rotate_CON".format(name), nr=[1, 0, 0], sw=360, r=controlerSize / 0.9
    )[0]
    ik_rotate_ik_rotate_control_grp = mc.group(n=ik_rotate_control + "_grp")

    # Parenting
    mc.xform(IKR_ankle_control, t=BN2_pos, ws=True)
    mc.xform(ik_rotate_ik_rotate_control_grp, m=BN2_mat, ws=True)
    mc.makeIdentity(IKR_ankle_control, t=True, a=True)
    mc.parent(IKR_Handle, IKR_ankle_control)
    mc.parent(IKR_ankle_control, IKR_GRP)
    mc.parent(ik_rotate_ik_rotate_control_grp, IKR_GRP)
    mc.parent(IKR_GRP, rigGroup)

    mc.parentConstraint(IKR_ankle_control, ik_rotate_ik_rotate_control_grp, mo=1)

    controlList.append(IKR_ankle_control)
    controlList.append(ik_rotate_control)

    # Orient constraint to the ik ankle

    mc.orientConstraint(
        ik_rotate_control, "{}_Ankle_BN_JNT".format(side).replace("BN", "IK"), mo=1
    )

    mc.setAttr(IKR_ankle_control + ".rx", l=True)
    mc.setAttr(IKR_ankle_control + ".ry", l=True)
    mc.setAttr(IKR_ankle_control + ".rz", l=True)

    mc.setAttr(ik_rotate_control + ".tx", l=True)
    mc.setAttr(ik_rotate_control + ".ty", l=True)
    mc.setAttr(ik_rotate_control + ".tz", l=True)

    # Create Blend Colors

    root_blend_color = mc.createNode(
        "blendColors", n="{}_Thigh_BLENDECOLOR".format(side)
    )
    mid_blend_color = mc.createNode("blendColors", n="{}_Knee_BLENDECOLOR".format(side))
    end_blend_color = mc.createNode(
        "blendColors", n="{}_Ankle_BLENDECOLOR".format(side)
    )

    blenderList = []
    blenderList.append(root_blend_color)
    blenderList.append(mid_blend_color)
    blenderList.append(end_blend_color)

    # Connecting IKFK blender root
    mc.connectAttr(
        ("{}.rotate".format("{}_Thigh_BN_JNT".format(side).replace("BN", "FK"))),
        "{}.color1".format(root_blend_color),
    )
    mc.connectAttr(
        ("{}.rotate".format("{}_Thigh_BN_JNT".format(side).replace("BN", "IK"))),
        "{}.color2".format(root_blend_color),
    )
    mc.connectAttr(
        ("{}.output".format(root_blend_color)),
        "{}.rotate".format("{}_Thigh_BN_JNT".format(side).replace("BN", "DRIVER")),
    )

    # Connecting IKFK blender mid
    mc.connectAttr(
        ("{}.rotate".format("{}_Calf_BN_JNT".format(side).replace("BN", "FK"))),
        "{}.color1".format(mid_blend_color),
    )
    mc.connectAttr(
        ("{}.rotate".format("{}_Calf_BN_JNT".format(side).replace("BN", "IK"))),
        "{}.color2".format(mid_blend_color),
    )
    mc.connectAttr(
        ("{}.output".format(mid_blend_color)),
        "{}.rotate".format("{}_Calf_BN_JNT".format(side).replace("BN", "DRIVER")),
    )

    # Connecting IKFK blender end
    mc.connectAttr(
        ("{}.rotate".format("{}_Ankle_BN_JNT".format(side).replace("BN", "FK"))),
        "{}.color1".format(end_blend_color),
    )
    mc.connectAttr(
        ("{}.rotate".format("{}_Ankle_BN_JNT".format(side).replace("BN", "IK"))),
        "{}.color2".format(end_blend_color),
    )
    mc.connectAttr(
        ("{}.output".format(end_blend_color)),
        "{}.rotate".format("{}_Ankle_BN_JNT".format(side).replace("BN", "DRIVER")),
    )

    # Create Parent Constraints--------------------------------------------------------|

    # mc.parentConstraint('{}_Thigh_BN_JNT'.format(side).replace('BN', 'FK'), '{}_Thigh_BN_JNT'.format(side), mo=True)
    mc.parentConstraint(
        "{}_Thigh_BN_JNT".format(side).replace("BN", "DRIVER"),
        "{}_Thigh_BN_JNT".format(side),
        mo=True,
    )
    mc.parentConstraint(
        "{}_Calf_BN_JNT".format(side).replace("BN", "DRIVER"),
        "{}_Calf_BN_JNT".format(side),
        mo=True,
    )
    mc.parentConstraint(
        "{}_Ankle_BN_JNT".format(side).replace("BN", "DRIVER"),
        "{}_Ankle_BN_JNT".format(side),
        mo=True,
    )

    # Create Container----------------------------------------------------------------|

    ikfk_attributes_Grp = mc.createNode(
        "transform", n="{}_Leg_ATRIBUTES_GRP".format(side)
    )
    mc.addAttr(ln="IKFK_Switch", at="float", k=True, min=0, max=1)

    arm_attributes_asset = mc.container(n="{}_Leg_ASSET".format(side))
    mc.container(arm_attributes_asset, e=True, ish=True, f=True, an=ikfk_attributes_Grp)

    IKFK_reverse = mc.createNode("reverse", n="{}_Leg_IKFK_reverse".format(side))

    # Connect attribute to the reverse
    mc.connectAttr(ikfk_attributes_Grp + ".IKFK_Switch", IKFK_reverse + ".input.inputX")

    # Connect the reverse to the blend color nodes
    mc.connectAttr(IKFK_reverse + ".input.inputX", root_blend_color + ".blender")
    mc.connectAttr(IKFK_reverse + ".input.inputX", mid_blend_color + ".blender")
    mc.connectAttr(IKFK_reverse + ".input.inputX", end_blend_color + ".blender")

    # Add controls to the asset

    for i in controlList, blenderList:

        mc.container(arm_attributes_asset, edit=True, addNode=i)

    # Publish name 'IKFK Switch'
    mc.container(arm_attributes_asset, e=True, pn=("IKFK_Switch"))

    # Bind ikfk attribute from the group to the container asset
    mc.container(
        arm_attributes_asset,
        e=True,
        ba=(ikfk_attributes_Grp + ".IKFK_Switch", "IKFK_Switch"),
    )

    # Creating pole target--------------------------------------------------------------------|

    distance = 1.0
    root_joint_pos = mc.xform(
        "{}_Thigh_BN_JNT".format(side).replace("BN", "IK"), q=1, ws=1, t=1
    )
    mid_joint_pos = mc.xform(
        "{}_Calf_BN_JNT".format(side).replace("BN", "IK"), q=1, ws=1, t=1
    )
    end_joint_pos = mc.xform(
        "{}_Ankle_BN_JNT".format(side).replace("BN", "IK"), q=1, ws=1, t=1
    )

    # Create locator at the vector position and create pole vector constraint

    def create_pv(pos, IKR=IKR_Handle):

        # create pole vector shape
        pv_group = mc.createNode("transform", n="{}_Leg_PV_Grp".format(side))

        pv_control = mc.curve(
            n="{}_Leg_PV_CON".format(side),
            d=1,
            p=[
                [-0.989623460780981, 1.0031016006564133, 1.0031016006564133],
                [-0.989623460780981, 1.0031016006564133, -1.0031016006564133],
                [-0.989623460780981, -1.0031016006564133, -1.0031016006564133],
                [-0.989623460780981, -1.0031016006564133, 1.0031016006564133],
                [-0.989623460780981, 1.0031016006564133, 1.0031016006564133],
                [0.989623460780981, 1.0031016006564133, 1.0031016006564133],
                [0.989623460780981, -1.0031016006564133, 1.0031016006564133],
                [-0.989623460780981, -1.0031016006564133, 1.0031016006564133],
                [0.989623460780981, -1.0031016006564133, 1.0031016006564133],
                [0.989623460780981, -1.0031016006564133, -1.0031016006564133],
                [0.989623460780981, 1.0031016006564133, -1.0031016006564133],
                [-0.989623460780981, 1.0031016006564133, -1.0031016006564133],
                [-0.989623460780981, -1.0031016006564133, -1.0031016006564133],
                [0.989623460780981, -1.0031016006564133, -1.0031016006564133],
                [0.989623460780981, 1.0031016006564133, -1.0031016006564133],
                [0.989623460780981, 1.0031016006564133, 1.0031016006564133],
            ],
        )

        mc.setAttr((pv_group + ".overrideEnabled"), 1)
        if "L_" in pv_control:
            mc.setAttr((pv_group + ".overrideColor"), 6)
        elif "R_" in pv_control:
            mc.setAttr((pv_group + ".overrideColor"), 13)
        else:
            mc.setAttr((pv_group + ".overrideColor"), 17)

        # Parent and move controll
        mc.parent(pv_control, pv_group)
        mc.move(pos.x, pos.y, pos.z, pv_group)
        mc.poleVectorConstraint(pv_control, IKR)
        mc.parent(pv_group, rigGroup)
        mc.container(arm_attributes_asset, edit=True, addNode=pv_control)

    # Get pole vector position

    def get_pole_vec_pos(root_pos, mid_pos, end_pos):

        root_joint_vec = om.MVector(root_pos[0], root_pos[1], root_pos[2])
        mid_joint_vec = om.MVector(mid_pos[0], mid_pos[1], mid_pos[2])
        end_joint_vec = om.MVector(end_pos[0], end_pos[1], end_pos[2])

        # Getting vectors of the joint chain
        line = end_joint_vec - root_joint_vec
        point = mid_joint_vec - root_joint_vec

        # MVector automatically does the dot product((line.length*point.length)cos theta)
        # MVector adds the cos automatically
        scale_value = (line * point) / (line * line)
        proj_vec = line * scale_value + root_joint_vec

        root_to_mid_len = (mid_joint_vec - root_joint_vec).length()
        mid_to_end_len = (end_joint_vec - mid_joint_vec).length()
        totaL_len = root_to_mid_len + mid_to_end_len

        pole_vec_pos = (
            mid_joint_vec - proj_vec
        ).normal() * distance * totaL_len + mid_joint_vec

        create_pv(pole_vec_pos)

    get_pole_vec_pos(root_joint_pos, mid_joint_pos, end_joint_pos)
    if bool(mc.objExists("Pelvis_CON")):
        mc.parentConstraint("Pelvis_CON", rigGroup, mo=1)
    mc.addAttr(
        "{}_Leg_PV_CON".format(side), ln="SpaceSwitch", at="enum", en="world:leg:pelvis"
    )
    mc.setAttr("{}_Leg_PV_CON.SpaceSwitch".format(side), e=1, k=1)

    # Visiblity connections

    leg_condition = mc.shadingNode(
        "condition", au=True, n="{}_leg_condition".format(name)
    )

    mc.connectAttr(ikfk_attributes_Grp + ".IKFK_Switch", leg_condition + ".firstTerm")
    mc.connectAttr(leg_condition + ".outColor.outColorR", topnode[0] + ".visibility")
    mc.connectAttr(leg_condition + ".outColor.outColorG", IKR_GRP + ".visibility")

    mc.setAttr(leg_condition + ".colorIfTrueR", 0)
    mc.setAttr(leg_condition + ".colorIfTrueG", 1)
    mc.setAttr(leg_condition + ".colorIfFalseR", 1)
    mc.setAttr(leg_condition + ".colorIfFalseG", 0)
