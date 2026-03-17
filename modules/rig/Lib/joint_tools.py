from maya import cmds
from maya import mel as mel

from core.Config import Config


class JointCreateAndOrientator(object):

    def __init__(self):
        self.baseJnt = []
        self.endJnt = []

    def createBaseJoint(self):

        sel = cmds.ls(sl=1)
        clstr = cmds.cluster()
        cmds.select(cl=1)
        self.baseJnt = cmds.joint(rad=1)
        cmds.select(cl=1)
        const = cmds.parentConstraint(clstr, self.baseJnt, mo=0)
        cmds.delete(const, clstr)
        cmds.select(sel)
        cmds.hilite(sel, tgl=1)

    def endBaseJoint(self):

        clstr = cmds.cluster()
        cmds.select(cl=1)
        self.endJnt = cmds.joint(rad=1)
        cmds.select(cl=1)
        const = cmds.parentConstraint(clstr, self.endJnt, mo=0)
        cmds.delete(const, clstr)
        self.parentAndOrient()

    def parentAndOrient(self):

        cmds.parent(self.endJnt, self.baseJnt)

        cmds.joint(self.baseJnt, e=True, oj="xyz", secondaryAxisOrient="zup", ch=True)

        cmds.joint(self.endJnt, e=True, oj="none", ch=True)

    def turnOnJointAxisVis(self):
        # bm_axisDisplay
        # Forces the Local Rotation Axis display on or off for all joints or for the selected joints
        # if no joints are selected, do it for all the joints in the scene

        if len(cmds.ls(sl=1, type="joint")) == 0:
            jointList = cmds.ls(type="joint")
        else:
            jointList = cmds.ls(sl=1, type="joint")
        # set the displayLocalAxis attribute to what the user specifies.
        for jnt in jointList:
            cmds.setAttr(jnt + ".displayLocalAxis", 1)

    def turnOffJointAxisVis(self):
        # bm_axisDisplay
        # Forces the Local Rotation Axis display on or off for all joints or for the selected joints
        # if no joints are selected, do it for all the joints in the scene

        if len(cmds.ls(sl=1, type="joint")) == 0:
            jointList = cmds.ls(type="joint")
        else:
            jointList = cmds.ls(sl=1, type="joint")
        # set the displayLocalAxis attribute to what the user specifies.
        for jnt in jointList:
            cmds.setAttr(jnt + ".displayLocalAxis", 0)

    def createControl(self):
        print("this is a placeholder")

def freeze_rotation_on_joints():
        
    # Get the currently selected objects
    selected_objects = cmds.ls(selection=True)

    # Check if there is at least one object selected
    if selected_objects:
        # Assume the first selected object is the joint to modify
        joint_name = selected_objects[0]

        # Get the current rotation values of the joint
        rotate_x_value = cmds.getAttr(f"{joint_name}.rotateX")
        rotate_y_value = cmds.getAttr(f"{joint_name}.rotateY")
        rotate_z_value = cmds.getAttr(f"{joint_name}.rotateZ")
        
        # Get the current joint orientation values of the joint
        orient_x_value = cmds.getAttr(f"{joint_name}.jointOrientX")
        orient_y_value = cmds.getAttr(f"{joint_name}.jointOrientY")
        orient_z_value = cmds.getAttr(f"{joint_name}.jointOrientZ")

        # Calculate new joint orientation values by adding current rotation to orientation
        new_x_value = rotate_x_value + orient_x_value
        new_y_value = rotate_y_value + orient_y_value
        new_z_value = rotate_z_value + orient_z_value

        # Set the new joint orientation values
        cmds.setAttr(f"{joint_name}.jointOrientX", new_x_value)
        cmds.setAttr(f"{joint_name}.jointOrientY", new_y_value)
        cmds.setAttr(f"{joint_name}.jointOrientZ", new_z_value)
        
        # Reset the joint's rotation values to zero
        cmds.setAttr(f"{joint_name}.rotateX", 0)
        cmds.setAttr(f"{joint_name}.rotateY", 0)
        cmds.setAttr(f"{joint_name}.rotateZ", 0)
        
    else:
        # Print a warning message if no object is selected
        print("No objects selected. Please select a joint.")

def always_deform():
    pass