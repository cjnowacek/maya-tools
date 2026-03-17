from maya import cmds as mc
import maya.mel as mel
from maya import OpenMaya as om
from maya import OpenMayaUI as omui

def main():
    RigOps_CreateRollJoints()


class RigOps_CreateRollJoints(object):

    sel = mc.ls(sl = True)
    JointSize = mc.getAttr((sel[0] + '.radius'))
    rigGroup = mc.group(em = True, n = 'Twist_Grp')

    twistJointCount = 2

    #refactoring list of selected joints

    bn0 = sel[0]
    bn1 = sel[1]
    bn2 = sel[2]
    bn3 = sel[3]

    name = 'twist'

    #getting xform data from bind joints
    BN0_mat = mc.xform(bn0, q = True, m = True, ws = True)
    BN1_mat = mc.xform(bn1, q = True, m = True, ws = True)
    BN2_mat = mc.xform(bn2, q = True, m = True, ws = True)
    BN3_mat = mc.xform(bn3, q = True, m = True, ws = True)


    BN0_pos = mc.xform(bn0, q=True, t=True, ws=True)
    BN1_pos = mc.xform(bn1, q=True, t=True, ws=True)
    BN2_pos = mc.xform(bn2, q=True, t=True, ws=True)
    BN3_pos = mc.xform(bn3, q=True, t=True, ws=True)

    def create_twist_joints(twistJointCount = twistJointCount, Init_JNT0 = bn1, Init_JNT1 = bn2, Init_JNT2 = bn3):
        
        # Clearing selection to avoid errors
        mc.select(cl=True)

        # Throw an error if twist_joint_count is less than 1 of greater than 5
        #if twistJointCount < 1 or twistJointCount > 5:
        #   om.MGlobal_displayError(
        #      'IKFK Tool: Too many or too few twist joints. 1-5 only')

        # Vector values for twist joints
        root_twist_xform = mc.xform(Init_JNT0, q=True, ws=True, t=True)
        mid_twist_xform = mc.xform(Init_JNT1, q=True, ws=True, t=True)
        end_twist_xform = mc.xform(Init_JNT2, q=True, ws=True, t=True)

        root_twist_vec = om.MVector(root_twist_xform[0], root_twist_xform[1], root_twist_xform[2])
        mid_twist_vec = om.MVector(mid_twist_xform[0], mid_twist_xform[1], mid_twist_xform[2])
        end_twist_vec = om.MVector(end_twist_xform[0], end_twist_xform[1], end_twist_xform[2])

        twist_joint_rtm_ik_1 = mc.joint(n='{}_RTM_Root_Twist_BN_JNT'.format(name), rad=JointSize*2)
        twist_joint_rtm_ik_2 = mc.joint(n='{}_RTM_Mid_Twist_JNT'.format(name), rad=JointSize*2)
        mc.parent(twist_joint_rtm_ik_1, rigGroup)
        mc.select(cl=True)
        twist_joint_ETM_ik_1 = mc.joint(n='{}_ETM_End_Twist_BN_JNT'.format(name), rad=JointSize*2)
        twist_joint_ETM_ik_2 = mc.joint(n='{}_ETM_Mid_Twist_JNT'.format(name), rad=JointSize*2)
        mc.parent(twist_joint_ETM_ik_1, rigGroup)
        mc.select(cl=True)

        mc.xform(twist_joint_rtm_ik_1, m=BN1_mat, ws=True)
        mc.xform(twist_joint_rtm_ik_2, m=BN1_mat, ws=True)
        mc.xform(twist_joint_rtm_ik_2, t=BN2_pos, ws=True)
        mc.select(cl=True)

        mc.xform(twist_joint_ETM_ik_1, m=BN3_mat, ws=True)
        mc.xform(twist_joint_ETM_ik_2, m=BN2_mat, ws=True)
        # mc.xform(self.twist_joint_ETM_ik_1, t=end_pos, ws=True)

        #mc.parent(twist_joint_ETM_ik_2, twist_joint_ETM_ik_1)
        
        # Get the vector from root joint to mid joint
        root_to_mid_vec = mid_twist_vec - root_twist_vec
        mid_to_end_vec = end_twist_vec - mid_twist_vec

        # Create multiplier to iterate through move than one twist joint
        tJC = twistJointCount + 1
        rtm_multiple = twistJointCount
        ETM_multiple = twistJointCount
        root_to_mid_joint_locations = []
        mid_to_end_joint_locations = []

        # Get positions of the twist joints from the root to mid.
        # Dependent on the specified number of twist joints
        for i in range(twistJointCount):

            # Interate through positions depending of the amount of twist joints.
            # Cycle through the positions
            joint_location = (
                (root_to_mid_vec - ((root_to_mid_vec/tJC) * rtm_multiple)) + root_twist_vec
            )

            root_to_mid_joint_locations.append(joint_location)
            rtm_multiple = rtm_multiple - 1

        # Get positions of the twist joints from the mid to end.
        # Dependent on the specified number of twist joints
        for i in range(twistJointCount):

            # Interate through positions depending of the amount of twist joints.
            # Cycle through the positions
            joint_location = (
                (mid_to_end_vec - ((mid_to_end_vec/tJC) * ETM_multiple)) + mid_twist_vec
            )

            mid_to_end_joint_locations.append(joint_location)
            ETM_multiple = ETM_multiple - 1

        rtm_twist_joints = []
        ETM_twist_joints = []

        #rtm_multiple = twistJointCount
        #ETM_multiple = twistJointCount
        rtm_multiple = 1
        ETM_multiple = 1

        # Create joints from the root to mid
        for i in root_to_mid_joint_locations:

            jnt = mc.joint(n='{}_RTM_Twist_BN{}_JNT'.format(name, rtm_multiple))
            mc.xform(jnt, m=BN1_mat, ws=True)
            mc.move(i.x, i.y, i.z, jnt)
            rtm_multiple = rtm_multiple + 1
            mc.select(cl=True)
            rtm_twist_joints.append(jnt)
            mc.parent(jnt, rigGroup)

        # Create joints from the mid to end
        for i in mid_to_end_joint_locations:

            jnt = mc.joint(n='{}_ETM_RTM_Twist_BN{}_JNT'.format(name, ETM_multiple))
            mc.xform(jnt, m=BN2_mat, ws=True)
            mc.move(i.x, i.y, i.z, jnt)
            ETM_multiple = ETM_multiple + 1
            mc.select(cl=True)
            ETM_twist_joints.append(jnt)
            mc.parent(jnt, rigGroup)

        for i in rtm_twist_joints:
            # Need to fix naming error before I can parent joints to root
            mc.parent(i, bn1)
            pass
        
        for i in ETM_twist_joints:
            # Need to fix naming error before I can parent joints to root
            mc.parent(i, bn2)
            pass
        
        RTM_IKS_Handle = mc.ikHandle(
            name='{}_RTM_IKS'.format(name), sol='ikSCsolver', sj=twist_joint_rtm_ik_1, ee=twist_joint_rtm_ik_2)[0]
        ETM_IKS_Handle = mc.ikHandle(
            name='{}_RTM_IKS'.format(name), sol='ikSCsolver', sj=twist_joint_ETM_ik_1, ee=twist_joint_ETM_ik_2)[0]
        
        mc.parent(RTM_IKS_Handle, rigGroup)
        mc.parent(ETM_IKS_Handle, rigGroup)
        
        mc.parent(twist_joint_rtm_ik_1, RTM_IKS_Handle, bn0)
        mc.parent(twist_joint_ETM_ik_1, ETM_IKS_Handle, bn3)
        
        mc.pointConstraint(bn2, RTM_IKS_Handle, mo=0)
        mc.pointConstraint(bn2, ETM_IKS_Handle, mo=0)
        #----------------------------------------------------------------------------------|
        #
        #Creating constraints
        #
        #----------------------------------------------------------------------------------|

        #constraint list initialization
        rtm_constraints = []
        etm_constraints = []
        
        # creating constrains
        for i in rtm_twist_joints:
                
            oriConst = mc.orientConstraint(bn1, twist_joint_rtm_ik_1, i, mo=True, skip = ['y','z'])[0]
            rtm_constraints.append(oriConst)
            
        for i in ETM_twist_joints:
                
            oriConst = mc.orientConstraint(bn3, twist_joint_ETM_ik_1, i, mo=True, skip = ['y','z'])[0]
            etm_constraints.append(oriConst)
        
        # editing constrain values 
        for i in range(len(rtm_constraints)):
            weightAmount = 1
            mc.setAttr((rtm_constraints[i] + '.' + bn1 + 'W0'), 1)
            mc.setAttr((rtm_constraints[i] + '.' +  twist_joint_rtm_ik_1 + 'W1'), 1)

        # editing constrain values 
        for i in range(len(etm_constraints)):
            mc.setAttr((etm_constraints[i] + '.' + bn3 + 'W0'), 1 + (i-.5))
            mc.setAttr((etm_constraints[i] + '.' +  twist_joint_ETM_ik_1 + 'W1'), 1)
            
        mc.rename(sel[1], sel[1].replace('BN', 'Trash'))
        mc.rename(twist_joint_rtm_ik_2, twist_joint_rtm_ik_2.replace('BN', 'Trash'))
        mc.rename(twist_joint_ETM_ik_1, twist_joint_ETM_ik_1.replace('BN', 'Trash'))
        mc.rename(twist_joint_ETM_ik_2, twist_joint_ETM_ik_2.replace('BN', 'Trash'))
        
        om.MGlobal_displayInfo('remember to set the value of the constraints')
        
        mc.delete(rigGroup)
        
    create_twist_joints()