from maya import cmds as mc

masterNode = None
bnList = []
follower = []
driver = []
jointControls = []
matList = []

PelvisPos = None
Spine1Pos = None
Spine2Pos = None
Spine3Pos = None
ChestPos = None

PelvisMat = None
Spine1Mat = None
Spine2Mat = None
Spine3Mat = None
ChestMat = None


def main(*args):
    global masterNode, bnList, follower, driver, jointControls, matList
    global PelvisPos, Spine1Pos, Spine2Pos, Spine3Pos, ChestPos
    global PelvisMat, Spine1Mat, Spine2Mat, Spine3Mat, ChestMat

    masterNode = mc.createNode("transform", n="RibbonSpine_System")

    bnList[:] = []
    follower[:] = []
    driver[:] = []
    jointControls[:] = []
    matList[:] = []

    bnList.append("this_bn")
    bnList.append("this_bn1")
    bnList.append("this_bn2")
    bnList.append("this_bn3")
    bnList.append("this_bn4")

    PelvisPos = mc.xform(bnList[0], t=True, ws=True, q=True)
    Spine1Pos = mc.xform(bnList[1], t=True, ws=True, q=True)
    Spine2Pos = mc.xform(bnList[2], t=True, ws=True, q=True)
    Spine3Pos = mc.xform(bnList[3], t=True, ws=True, q=True)
    ChestPos = mc.xform(bnList[4], t=True, ws=True, q=True)

    PelvisMat = mc.xform(bnList[0], m=True, ws=True, q=True)
    Spine1Mat = mc.xform(bnList[1], m=True, ws=True, q=True)
    Spine2Mat = mc.xform(bnList[2], m=True, ws=True, q=True)
    Spine3Mat = mc.xform(bnList[3], m=True, ws=True, q=True)
    ChestMat = mc.xform(bnList[4], m=True, ws=True, q=True)

    matList.append(PelvisMat)
    matList.append(Spine1Mat)
    matList.append(Spine2Mat)
    matList.append(Spine3Mat)
    matList.append(ChestMat)

    buildSurface()
    dupJoints()
    createDrivers()


def buildSurface():

    crvs = mc.curve(
        d=3,
        p=[
            (PelvisPos[0], PelvisPos[1], PelvisPos[2]),
            (Spine1Pos[0], Spine1Pos[1], Spine1Pos[2]),
            (Spine2Pos[0], Spine2Pos[1], Spine2Pos[2]),
            (Spine3Pos[0], Spine3Pos[1], Spine3Pos[2]),
            (ChestPos[0], ChestPos[1], ChestPos[2]),
        ],
    )

    dupCurve = mc.duplicate(crvs, n="Ribbon_Spline_curve")
    mc.parent(dupCurve, masterNode)

    mc.xform(crvs, t=[1, 0, 0], os=True)
    dup = mc.duplicate(crvs)
    mc.xform(dup, t=[-1, 0, 0], os=True)
    mc.loft(dup, crvs, n="Ribbon_Spline_CRVS", d=3)
    mc.parent("Ribbon_Spline_CRVS", "RibbonSpine_System")
    mc.delete(dup, crvs)


def dupJoints():

    group = mc.createNode("transform", n="RS_followers")
    mc.parent(group, "RibbonSpine_System")

    for i in range(len(bnList)):
        dup = mc.duplicate(bnList[i], n=bnList[i].replace("BN", "follower"), po=True)[0]
        mc.parent(dup, "RS_followers")
        follower.append(dup)


def createDrivers():

    group = mc.createNode("transform", n="RS_drivers")
    mc.parent(group, "RibbonSpine_System")

    for i in range(len(follower)):
        dup = mc.duplicate(
            follower[i], n=follower[i].replace("follower", "driver"), po=True
        )[0]
        mc.parent(dup, "RS_drivers")
        driver.append(dup)

    for i in range(len(follower)):
        mc.connectAttr(follower[i] + ".translate", driver[i] + ".translate")
        mc.connectAttr(follower[i] + ".rotate", driver[i] + ".rotate")
        mc.connectAttr(follower[i] + ".scale", driver[i] + ".scale")


def constrainSuface():

    constList = []
    constList.append("Ribbon_Spline_CRVS")

    for i in range(len(follower)):
        constList.append(follower[i])
    print(constList)

    sel = mc.select(constList[:])
    mc.UVPin(sel)


def createHair():
    pass
