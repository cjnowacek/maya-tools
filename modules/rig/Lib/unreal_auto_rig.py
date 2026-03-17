"""
/UnrealRigBuilder.py

This script automates the creation of a control rig inside Autodesk Maya, specifically designed
for Unreal Engine workflows. It provides tools for generating IK and FK systems, twist joints,
and control curves to facilitate character rigging.

### Features:
- Generates structured IK, FK, and control rig hierarchies.
- Automates the creation of twist joints for improved deformation.
- Provides customizable control curves for easy manipulation.
- Supports pole vector constraints and IK-FK switching.
- Organizes rig components within a dedicated hierarchy for clarity.

### Usage:
1. Run the script to execute the `BuildUnrealRig` function.
2. The rig will be generated, including IK, FK, and control rigs.
3. Adjust control curves and constraints as needed within Maya.

### Metadata:
- **Author:** CJ Nowacek
- **Version:** 1.0.0
- **License:** GPL
- **Maintainer:** CJ Nowacek
- **Status:** WIP
"""

import maya.cmds as mc
import maya.mel as mel
import maya.OpenMaya as om

CONTROL_RIG_FOLDER_NAME = "Control_Rig"

(
    PELVIS,
    SPINE1,
    SPINE2,
    SPINE3,
    SPINE4,
) = (
    "pelvis",
    "spine_01",
    "spine_02",
    "spine_03",
    "spine_04",
)

IKARM, IKLEG = ["upperarm", "hand"], ["thigh", "foot"]

# bone lists
Control_Rig_Bones = []
Ik_Rig_Bones = []
Fk_Rig_Bones = []


# Create a new control rig folder
def createControlRigFolder():
    # Create a folder for the control rig
    mc.createNode("transform", n=CONTROL_RIG_FOLDER_NAME, p="RIG")


def colorCurve(crv):
    mc.setAttr((crv + ".overrideEnabled"), 1)
    if "l_" in crv:
        mc.setAttr((crv + ".overrideColor"), 6)
    elif "r_" in crv:
        mc.setAttr((crv + ".overrideColor"), 13)
    else:
        mc.setAttr((crv + ".overrideColor"), 17)


# Create twist joints down a single chain
def create_twist_joints(start_point, end_point, limb, side, divisions):
    """
    Create a joint chain in Maya between two points in space, dividing the distance evenly by the number of divisions.

    :param start_point: Tuple representing the starting point (x, y, z).
    :param end_point: Tuple representing the ending point (x, y, z).
    :param divisions: Number of joints in the chain.
    """
    mat1 = mc.xform(start_point, q=1, ws=1, m=1)
    pos1 = mc.xform(start_point, q=1, ws=1, t=1)
    pos2 = mc.xform(end_point, q=1, ws=1, t=1)
    start_point = pos1  # Starting point of the joint chain
    end_point = pos2  # Ending point of the joint chain
    # divisions = 5  # Number of joints to divide the chain into

    if divisions < 2:
        mc.error("Number of divisions must be at least 2.")
        return

    # Calculate the increment per joint
    x_inc = (end_point[0] - start_point[0]) / (divisions - 1)
    y_inc = (end_point[1] - start_point[1]) / (divisions - 1)
    z_inc = (end_point[2] - start_point[2]) / (divisions - 1)

    # Create the joints
    joint_list = []
    for i in range(divisions):
        mc.select(cl=1)
        x = start_point[0] + i * x_inc
        y = start_point[1] + i * y_inc
        z = start_point[2] + i * z_inc
        joint_name = mc.joint(
            p=(x, y, z), n="{0}_twist_0{2}_{1}".format(limb, side, i + 1)
        )
        mc.xform(joint_name, m=mat1)
        mc.xform(joint_name, t=(x, y, z))

        joint_list.append(joint_name)

    for i in range(len(joint_list) - 1):  # Stop at the second-to-last index
        mc.parent(joint_list[i + 1], joint_list[i])

    for i in range(len(joint_list)):
        mc.makeIdentity(joint_list[i], translate=1, rotate=1, scale=1, apply=1)

    mc.parent(joint_list[0], "{0}_{1}".format(limb, side))
    # Return the list of created joints
    return joint_list


# Create a new control rig done that will be parented to the bind joints
def createJointDups(suff):
    tmpboneList = []

    mc.createNode(
        "transform",
        n=CONTROL_RIG_FOLDER_NAME + "_bones_{0}".format(suff),
        p=CONTROL_RIG_FOLDER_NAME,
    )
    mc.select("root", hi=True)
    this = mc.ls(sl=1)
    for i in this:

        if mc.objectType(i) != "joint":
            mc.select(i, d=1)

    this = mc.ls(sl=1)

    for i in this:
        mc.select(cl=1)
        mat = mc.xform(i, q=1, m=1, ws=1)
        prt = mc.listRelatives(i, p=1)
        jnt = mc.joint(p=[0, 0, 0], n="{0}_{1}".format(i, suff))
        mc.xform(jnt, m=mat, ws=1)
        mc.makeIdentity(jnt, apply=True, r=True)
        tmpboneList.append(i)

        if jnt != "root_{0}".format(suff):
            print(jnt, prt)

            mc.parent(jnt, prt[0] + "_{0}".format(suff))

        if "_cr" in jnt:
            mc.parentConstraint(jnt, i, mo=1)

    mc.parent(
        "root_{0}".format(suff), CONTROL_RIG_FOLDER_NAME + "_bones_{0}".format(suff)
    )

    return tmpboneList


# Rig Setups--------------------------------------------------------------------------|


# create Basic
def createBasicIK(limb, side, sj, mj, ee, suff):

    ik_handle = mc.ikHandle(
        sj="{0}_{1}_{2}".format(sj, side, suff),
        ee="{0}_{1}_{2}".format(ee, side, suff),
        n="{0}_ik_{1}_{2}".format(limb, side, suff),
        p=2,
        sol="ikRPsolver",
        w=0.5,
    )

    ik_control = mc.curve(
        n="{0}_ik_{1}_{2}_con".format(limb, side, suff),
        d=1,
        p=[
            [-1, 1, 1],
            [-1, 1, -1],
            [-1, -1, -1],
            [-1, -1, 1],
            [-1, 1, 1],
            [1, 1, 1],
            [1, -1, 1],
            [-1, -1, 1],
            [1, -1, 1],
            [1, -1, -1],
            [1, 1, -1],
            [-1, 1, -1],
            [-1, -1, -1],
            [1, -1, -1],
            [1, 1, -1],
            [1, 1, 1],
        ],
    )

    colorCurve(ik_control)

    mc.xform(s=[4, 4, 4])
    mc.select(ik_control)
    grp = mc.group(n="{0}_{1}_{2}_grp".format(ee, side, suff))
    mc.select(grp, "{0}_{1}_{2}".format(ee, side, suff))
    mel.eval("MatchTranslation;")
    const = mc.orientConstraint(
        "{0}_{1}_{2}".format(ee, side, suff), ik_control, skip=["x", "y"]
    )
    mc.delete(const)
    mc.makeIdentity(ik_control, r=True, a=True, s=True)
    mc.parentConstraint(ik_control, "{0}_ik_{1}_{2}".format(limb, side, suff))
    mc.orientConstraint(ik_control, "{0}_{1}_{2}".format(ee, side, suff), mo=True)

    CONTROL_RIG_FOLDER_NAME + "_{0}_{1}_{2}".format(limb, side, suff)

    mc.parent(grp, CONTROL_RIG_FOLDER_NAME)
    mc.parent(ik_handle[0], CONTROL_RIG_FOLDER_NAME)

    createPoleTarget(limb, side, sj, mj, ee, suff, ik_handle[0])


# create poletarget after building basic IK
def createPoleTarget(limb, side, sj, mj, ee, suff, ikh):
    # Creating pole target--------------------------------------------------------------------|

    distance = 1.0
    root_joint_pos = mc.xform("{0}_{1}_{2}".format(sj, side, suff), q=1, ws=1, t=1)
    mid_joint_pos = mc.xform("{0}_{1}_{2}".format(mj, side, suff), q=1, ws=1, t=1)
    end_joint_pos = mc.xform("{0}_{1}_{2}".format(ee, side, suff), q=1, ws=1, t=1)

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

        return pole_vec_pos

    # Create locator at the vector position and create pole vector constraint

    def create_pv(pos, ikh):

        # create pole vector shape
        pv_group = mc.createNode(
            "transform", name="{0}_{1}_{2}_PV_GRP".format(limb, side, suff)
        )

        pv_control = mc.curve(
            n="{0}_{1}_{2}_PV_CON".format(limb, side, suff),
            d=1,
            p=[
                [-1, 1, 1],
                [-1, 1, -1],
                [-1, -1, -1],
                [-1, -1, 1],
                [-1, 1, 1],
                [1, 1, 1],
                [1, -1, 1],
                [-1, -1, 1],
                [1, -1, 1],
                [1, -1, -1],
                [1, 1, -1],
                [-1, 1, -1],
                [-1, -1, -1],
                [1, -1, -1],
                [1, 1, -1],
                [1, 1, 1],
            ],
        )

        colorCurve(pv_control)

        # Parent and move controll
        mc.parent(pv_control, pv_group)
        mc.move(pos.x, pos.y, pos.z, pv_group)
        mc.poleVectorConstraint(pv_control, ikh)

        # mc.parent(pv_group, ikh)

    pole_vec_pos = get_pole_vec_pos(root_joint_pos, mid_joint_pos, end_joint_pos)
    create_pv(pole_vec_pos, ikh)


# create FK controls on fk bones
def createFKControls(bone):

    boneList = []
    controlList = []
    groupList = []

    for i in bone:
        boneList.append(i)

    for i in range(len(boneList)):

        fk_control = mc.curve(
            n="{0}_con".format(boneList[i]),
            d=1,
            p=[
                [-1, 1, 1],
                [-1, 1, -1],
                [-1, -1, -1],
                [-1, -1, 1],
                [-1, 1, 1],
                [1, 1, 1],
                [1, -1, 1],
                [-1, -1, 1],
                [1, -1, 1],
                [1, -1, -1],
                [1, 1, -1],
                [-1, 1, -1],
                [-1, -1, -1],
                [1, -1, -1],
                [1, 1, -1],
                [1, 1, 1],
            ],
        )

        controlList.append(fk_control)

        mc.xform(s=[0.5, 4, 3])
        mc.select(fk_control)
        grp = mc.group(n="{0}_grp".format(boneList[i]), p=CONTROL_RIG_FOLDER_NAME)
        groupList.append(grp)

        mc.select(grp, "{0}".format(boneList[i]))
        mel.eval("MatchTransform;")
        mc.makeIdentity(fk_control, r=True, a=True, s=True)
    """print(controlList)
    print(groupList)
    mc.parent(groupList[4], controlList[3])
    mc.parent(groupList[3], controlList[2])
    mc.parent(groupList[2], controlList[1])
    mc.parent(groupList[1], controlList[0])
    mc.parent(groupList[0], CONTROL_RIG_FOLDER_NAME)"""

    for i in range(len(controlList)):
        mc.parentConstraint(controlList[i], boneList[i] + "_fk", mo=True)

    for i in range(len(controlList) - 1):
        mc.parent(groupList[i + 1], controlList[i])


# create IkfkSwitch
def createIkfkSwitch(limb, side, sj, mj, ee):
    # Create Blend Colors

    root_blend_color = mc.createNode(
        "blendColors", name=f"{limb}_{side}_{sj}_BLENDECOLOR"
    )
    mid_blend_color = mc.createNode(
        "blendColors", name=f"{limb}_{side}_{mj}_BLENDECOLOR"
    )
    end_blend_color = mc.createNode(
        "blendColors", name=f"{limb}_{side}_{ee}_BLENDECOLOR"
    )
    
    blenderList = []
    blenderList.append(root_blend_color)
    blenderList.append(mid_blend_color)
    blenderList.append(end_blend_color)
    
    # Connecting IKFK blender root
    mc.connectAttr(
        f"{fkjoints1}.rotate", f"{root_blend_color}.color1"
    )
    mc.connectAttr(
        f"{ikjoints1}.rotate", f"{root_blend_color}.color2"
    )
    mc.connectAttr(
        f"{root_blend_color}.output", f"{driverjoints1}.rotate"
    )
    # Connecting IKFK blender mid
    mc.connectAttr(f"{fkjoints2}.rotate", f"{mid_blend_color}.color1")
    mc.connectAttr(f"{ikjoints2}.rotate", f"{mid_blend_color}.color2")
    mc.connectAttr(
        f"{mid_blend_color}.output", f"{driverjoints2}.rotate"
    )
    # Connecting IKFK blender end
    mc.connectAttr(f"{fkjoints3}.rotate", f"{end_blend_color}.color1")
    mc.connectAttr(f"{ikjoints3}.rotate", f"{end_blend_color}.color2")
    mc.connectAttr(
        f"{end_blend_color}.output", f"{driverjoints3}.rotate"
    )
    # Create Parent Constraints--------------------------------------------------------|
    mc.parentConstraint(fkjoints0, driverjoints0, mo=True)
    mc.parentConstraint(driverjoints0, bn0, mo=True)
    mc.parentConstraint(driverjoints1, bn1, mo=True)
    mc.parentConstraint(driverjoints2, bn2, mo=True)
    mc.parentConstraint(driverjoints3, bn3, mo=True)
    # Create Container----------------------------------------------------------------|
    ikfk_attributes_Grp = mc.createNode(
        "transform", name=f"{name}_ATRIBUTES_GRP"
    )
    mc.addAttr(ln="IKFK_Switch", at="float", k=True, min=0, max=1)
    arm_attributes_asset = mc.container(name=f"{name}_ASSET")
    mc.container(arm_attributes_asset, e=True, ish=True, f=True, an=ikfk_attributes_Grp)
    mc.parent(ikfk_attributes_Grp, rigGroup)
    IKFK_reverse = mc.createNode("reverse", n=f"{name}_IKFK_reverse")
    # Connect attribute to the reverse
    mc.connectAttr(f"{ikfk_attributes_Grp}.IKFK_Switch", f"{IKFK_reverse}.input.inputX")
    # Connect the reverse to the blend color nodes
    mc.connectAttr(f"{IKFK_reverse}.input.inputX", f"{root_blend_color}.blender")
    mc.connectAttr(f"{IKFK_reverse}.input.inputX", f"{mid_blend_color}.blender")
    mc.connectAttr(f"{IKFK_reverse}.input.inputX", f"{end_blend_color}.blender")
    # Add controls to the asset
    for i in controlList, blenderList:
        mc.container(arm_attributes_asset, edit=True, addNode=i)
    # Publish name 'IKFK Switch'
    mc.container(arm_attributes_asset, e=True, pn=("IKFK_Switch"))
    # Bind ikfk attribute from the group to the container asset
    mc.container(
        arm_attributes_asset,
        e=True,
        ba=(f"{ikfk_attributes_Grp}.IKFK_Switch", "IKFK_Switch"),
    )
    pass


def createFKSpine(pelvis, spine_01, spine_02, spine_03, spine_04):

    boneList = [pelvis, spine_01, spine_02, spine_03, spine_04]
    controlList = []
    groupList = []

    for i in range(len(boneList)):

        spine_control = mc.curve(
            n="{0}_con".format(boneList[i]),
            d=1,
            p=[
                [-1, 1, 1],
                [-1, 1, -1],
                [-1, -1, -1],
                [-1, -1, 1],
                [-1, 1, 1],
                [1, 1, 1],
                [1, -1, 1],
                [-1, -1, 1],
                [1, -1, 1],
                [1, -1, -1],
                [1, 1, -1],
                [-1, 1, -1],
                [-1, -1, -1],
                [1, -1, -1],
                [1, 1, -1],
                [1, 1, 1],
            ],
        )

        controlList.append(spine_control)

        mc.xform(s=[0.5, 12, 12])
        mc.select(spine_control)
        grp = mc.group(n="{0}_grp".format(boneList[i]))
        groupList.append(grp)

        mc.select(grp, "{0}".format(boneList[i]))
        mel.eval("MatchTransform;")
        mc.makeIdentity(spine_control, r=True, a=True, s=True)
    print(controlList)
    print(groupList)
    mc.parent(groupList[4], controlList[3])
    mc.parent(groupList[3], controlList[2])
    mc.parent(groupList[2], controlList[1])
    mc.parent(groupList[1], controlList[0])
    mc.parent(groupList[0], CONTROL_RIG_FOLDER_NAME)

    for i in range(len(controlList)):
        mc.parentConstraint(controlList[i], boneList[i], mo=True)


# BuildUnrealRig Auto Rig
def BuildUnrealRig():
    # Create rig folder--------------------------------------------------------------------------|
    createControlRigFolder()

    # Create duplicate bones for the IK and FK systems--------------------------------------------------------------------------|
    Driver_Rig_Bones = createJointDups(suff="driver")
    Ik_Rig_Bones = createJointDups(suff="ik")
    Fk_Rig_Bones = createJointDups(suff="fk")

    # Creating rig modulals--------------------------------------------------------------------------|

    # createWorld()
    # createFKSpine("pelvis_cr", "spine_01_cr", "spine_02_cr", "spine_03_cr", "spine_04_cr")
    createFKControls(Fk_Rig_Bones)

    createBasicIK("leg", "l", "thigh", "calf", "foot", "ik")
    createBasicIK("leg", "r", "thigh", "calf", "foot", "ik")
    createBasicIK("arm", "l", "upperarm", "lowerarm", "hand", "ik")
    createBasicIK("arm", "r", "upperarm", "lowerarm", "hand", "ik")

    # createIkfkSwitch(Control_Rig_Bones, Ik_Rig_Bones, Fk_Rig_Bones)

    createIkfkSwitch("arm", "r", "upperarm", "lowerarm", "hand", "ik")

    # Creating twist joints---------------------------------------------------------------------------

    # Create Joints, Correctives, etc
    """
    create_twist_joints("thigh_l", "calf_l", "thigh", "l", 5)
    create_twist_joints("thigh_r", "calf_r", "thigh", "r", 5)
    create_twist_joints("calf_l", "foot_l", "calf", "l", 5)
    create_twist_joints("calf_r", "foot_r", "calf", "r", 5)
    create_twist_joints("upperarm_l", "lowerarm_l", "upperarm", "l", 4)
    create_twist_joints("upperarm_r", "lowerarm_r", "upperarm", "r", 4)
    create_twist_joints("lowerarm_l", "hand_l", "lowerarm", "l", 5)
    create_twist_joints("lowerarm_r", "hand_r", "lowerarm", "r", 5)
    """


def main(*args):
    BuildUnrealRig()


if __name__ == "__main__":
    main()
