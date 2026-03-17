import maya.cmds as mc
import maya.mel as mel

def main():
    RipOps_CreateControls()
    
def RipOps_CreateControls():

    sel = mc.ls(sl=True)

    chainList = []
    newchainList = []
    namereplace = ""

    for i in sel:

        namereplace = "JNT"
        """
        if 'BN_JNT' in i:
            namereplace = 'BN_JNT'
        elif 'FK_JNT' in i:
            namereplace = 'FK_JNT'
        """
        con = mc.circle(n=i.replace(namereplace, "CON"), nr=[1, 0, 0], sw=360)
        # sdkgrp = mc.group(n = i.replace(namereplace, 'SDK_GRP'))
        offgrp = mc.group(n=i.replace(namereplace, "OFF_GRP"))
        grp = mc.group(n=i.replace(namereplace, "GRP"))
        const = mc.parentConstraint(i, grp, mo=0)
        mc.delete(const)
        mc.parentConstraint(con, i, mo=True)

        newchainList.append(grp)
        newchainList.append(con[0])

    newchainList.pop(0)

    for i in range(int(len(newchainList) / 2)):
        i = i * 2
        mc.parent(newchainList[i + 1], newchainList[i])
