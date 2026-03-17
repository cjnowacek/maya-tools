"""
#-------------------------------------------------------------#
#Arm Auto rig

Builds out the rig on top of existing BN joints as a base

Auto IKFK Switch
Auto Pole Vector
#-------------------------------------------------------------#
"""

import maya.cmds as mc
import maya.mel as mel
from maya import OpenMaya as om
from maya import OpenMayaUI as omui


def main():
    RigOps_ArmIKFKSwitch()


rigType = "Arm"
side = ""
controlerSize = 6


def RigOps_ArmIKFKSwitch(side="L"):

    if "L" in side:
        pass
    elif "R" in side:
        pass
    else:
        mc.error('Side must be "L" or "R"')

    sel = mc.ls(sl=True)
    JointSize = mc.getAttr((sel[0] + ".radius"))
    name = side + "_" + rigType
    rigGroup = mc.group(em=True, n=name + "_Grp")

    # refactoring list of selected joints

    bn0 = sel[0]
    bn1 = sel[1]
    bn2 = sel[2]
    bn3 = sel[3]

    # getting xform data from bind joints
    BN0_mat = mc.xform(bn0, q=True, m=True, ws=True)
    BN1_mat = mc.xform(bn1, q=True, m=True, ws=True)
    BN2_mat = mc.xform(bn2, q=True, m=True, ws=True)
    BN3_mat = mc.xform(bn3, q=True, m=True, ws=True)

    BN0_pos = mc.xform(bn0, q=True, t=True, ws=True)
    BN1_pos = mc.xform(bn1, q=True, t=True, ws=True)
    BN2_pos = mc.xform(bn2, q=True, t=True, ws=True)
    BN3_pos = mc.xform(bn3, q=True, t=True, ws=True)

    # Duplicate Base Arm

    driverjoints0 = mc.duplicate(bn0, n=bn0.replace("BN", "DRIVER"), po=True)[0]
    driverjoints1 = mc.duplicate(bn1, n=bn1.replace("BN", "DRIVER"), po=True)[0]
    driverjoints2 = mc.duplicate(bn2, n=bn2.replace("BN", "DRIVER"), po=True)[0]
    driverjoints3 = mc.duplicate(bn3, n=bn3.replace("BN", "DRIVER"), po=True)[0]
    mc.parent(driverjoints3, driverjoints2)
    mc.parent(driverjoints2, driverjoints1)
    mc.parent(driverjoints1, driverjoints0)
    mc.parent(driverjoints0, rigGroup)

    fkjoints0 = mc.duplicate(bn0, n=bn0.replace("BN", "FK"), po=True)[0]
    fkjoints1 = mc.duplicate(bn1, n=bn1.replace("BN", "FK"), po=True)[0]
    fkjoints2 = mc.duplicate(bn2, n=bn2.replace("BN", "FK"), po=True)[0]
    fkjoints3 = mc.duplicate(bn3, n=bn3.replace("BN", "FK"), po=True)[0]
    mc.parent(fkjoints3, fkjoints2)
    mc.parent(fkjoints2, fkjoints1)
    mc.parent(fkjoints1, fkjoints0)
    mc.parent(fkjoints0, rigGroup)

    ikjoints1 = mc.duplicate(bn1, n=bn1.replace("BN", "IK"), po=True)[0]
    ikjoints2 = mc.duplicate(bn2, n=bn2.replace("BN", "IK"), po=True)[0]
    ikjoints3 = mc.duplicate(bn3, n=bn3.replace("BN", "IK"), po=True)[0]
    mc.parent(ikjoints3, ikjoints2)
    mc.parent(ikjoints2, ikjoints1)
    mc.parent(ikjoints1, fkjoints0)

    # Add Controls to FK

    chainList = []
    chainList.append(bn0.replace("BN", "FK"))
    chainList.append(bn1.replace("BN", "FK"))
    chainList.append(bn2.replace("BN", "FK"))
    chainList.append(bn3.replace("BN", "FK"))

    mc.select(cl=True)

    sdkcheck = 0
    offcheck = 0

    newchainList = []
    topnode = []
    controlList = []

    for i in chainList:

        if "BN_JNT" in i:
            namereplace = "BN_JNT"
        elif "FK_JNT" in i:
            namereplace = "FK_JNT"
        elif "IK_JNT" in i:
            namereplace = "FK_JNT"

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
    IKR_GRP = mc.createNode("transform", name="{}_IKR_GRP".format(name))

    IKR_Handle = mc.ikHandle(
        name="{}_IKR".format(name), sol="ikRPsolver", sj=ikjoints1, ee=ikjoints3
    )[0]

    # Create Control
    IKR_wrist_control = mc.curve(
        n="{}_ik_CON".format(name),
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
    mc.xform(IKR_wrist_control, t=BN3_pos, ws=True)
    mc.xform(ik_rotate_ik_rotate_control_grp, m=BN3_mat, ws=True)
    mc.makeIdentity(IKR_wrist_control, t=True, a=True)
    mc.parent(IKR_Handle, IKR_wrist_control)
    mc.parent(IKR_wrist_control, IKR_GRP)
    mc.parent(ik_rotate_ik_rotate_control_grp, IKR_GRP)
    mc.parent(IKR_GRP, rigGroup)

    mc.parentConstraint(IKR_wrist_control, ik_rotate_ik_rotate_control_grp, mo=1)

    controlList.append(IKR_wrist_control)
    controlList.append(ik_rotate_control)

    # Orient constraint to the ik wrist

    mc.orientConstraint(ik_rotate_control, ikjoints3, mo=1)

    mc.setAttr(IKR_wrist_control + ".rx", l=True)
    mc.setAttr(IKR_wrist_control + ".ry", l=True)
    mc.setAttr(IKR_wrist_control + ".rz", l=True)

    mc.setAttr(ik_rotate_control + ".tx", l=True)
    mc.setAttr(ik_rotate_control + ".ty", l=True)
    mc.setAttr(ik_rotate_control + ".tz", l=True)

    # Create Blend Colors

    root_blend_color = mc.createNode(
        "blendColors", name="{}_Shoulder_BLENDECOLOR".format(name)
    )
    mid_blend_color = mc.createNode(
        "blendColors", name="{}_Elbow_BLENDECOLOR".format(name)
    )
    end_blend_color = mc.createNode(
        "blendColors", name="{}_Wrist_BLENDECOLOR".format(name)
    )

    blenderList = []
    blenderList.append(root_blend_color)
    blenderList.append(mid_blend_color)
    blenderList.append(end_blend_color)

    # Connecting IKFK blender root
    mc.connectAttr(
        ("{}.rotate".format(fkjoints1)), "{}.color1".format(root_blend_color)
    )
    mc.connectAttr(
        ("{}.rotate".format(ikjoints1)), "{}.color2".format(root_blend_color)
    )
    mc.connectAttr(
        ("{}.output".format(root_blend_color)), "{}.rotate".format(driverjoints1)
    )

    # Connecting IKFK blender mid
    mc.connectAttr(("{}.rotate".format(fkjoints2)), "{}.color1".format(mid_blend_color))
    mc.connectAttr(("{}.rotate".format(ikjoints2)), "{}.color2".format(mid_blend_color))
    mc.connectAttr(
        ("{}.output".format(mid_blend_color)), "{}.rotate".format(driverjoints2)
    )

    # Connecting IKFK blender end
    mc.connectAttr(("{}.rotate".format(fkjoints3)), "{}.color1".format(end_blend_color))
    mc.connectAttr(("{}.rotate".format(ikjoints3)), "{}.color2".format(end_blend_color))
    mc.connectAttr(
        ("{}.output".format(end_blend_color)), "{}.rotate".format(driverjoints3)
    )

    # Create Parent Constraints--------------------------------------------------------|

    mc.parentConstraint(fkjoints0, driverjoints0, mo=True)
    mc.parentConstraint(driverjoints0, bn0, mo=True)
    mc.parentConstraint(driverjoints1, bn1, mo=True)
    mc.parentConstraint(driverjoints2, bn2, mo=True)
    mc.parentConstraint(driverjoints3, bn3, mo=True)

    # Create Container----------------------------------------------------------------|

    ikfk_attributes_Grp = mc.createNode(
        "transform", name="{}_ATRIBUTES_GRP".format(name)
    )
    mc.addAttr(ln="IKFK_Switch", at="float", k=True, min=0, max=1)

    arm_attributes_asset = mc.container(name="{}_ASSET".format(name))
    mc.container(arm_attributes_asset, e=True, ish=True, f=True, an=ikfk_attributes_Grp)
    mc.parent(ikfk_attributes_Grp, rigGroup)

    IKFK_reverse = mc.createNode("reverse", n="{}_IKFK_reverse".format(name))

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
    root_joint_pos = mc.xform(ikjoints1, q=1, ws=1, t=1)
    mid_joint_pos = mc.xform(ikjoints2, q=1, ws=1, t=1)
    end_joint_pos = mc.xform(ikjoints3, q=1, ws=1, t=1)

    # Create locator at the vector position and create pole vector constraint

    def create_pv(pos, IKR=IKR_Handle):

        # create pole vector shape
        pv_group = mc.createNode("transform", name="{}_PV_GRP".format(name))

        pv_control = mc.curve(
            n="{}_PV_CON".format(name),
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
        mc.parent(pv_group, IKR_GRP)
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
        total_len = root_to_mid_len + mid_to_end_len

        pole_vec_pos = (
            mid_joint_vec - proj_vec
        ).normal() * distance * total_len + mid_joint_vec

        create_pv(pole_vec_pos)

    get_pole_vec_pos(root_joint_pos, mid_joint_pos, end_joint_pos)

    print(topnode)

    # Visiblity connections

    arm_condition = mc.shadingNode(
        "condition", au=True, n="{}_Arm_condition".format(name)
    )

    mc.connectAttr(ikfk_attributes_Grp + ".IKFK_Switch", arm_condition + ".firstTerm")
    mc.connectAttr(arm_condition + ".outColor.outColorR", topnode[1] + ".visibility")
    mc.connectAttr(arm_condition + ".outColor.outColorG", IKR_GRP + ".visibility")

    mc.setAttr(arm_condition + ".colorIfTrueR", 0)
    mc.setAttr(arm_condition + ".colorIfTrueG", 1)
    mc.setAttr(arm_condition + ".colorIfFalseR", 1)
    mc.setAttr(arm_condition + ".colorIfFalseG", 0)
