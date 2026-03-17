import maya.cmds as mc
import maya.mel as mel

def main():
    AnimOps_Macros()


class main(object):

    # constructor
    def __init__(self):

        self.window = "SkinOps_Painter"
        self.title = "Skin Painter"
        self.size = (400, 120)

        # skining varibles

        self.image1 = "paintSkinWeights.png"
        self.image2 = "vacantCell.png"
        self.image3 = "vacantCell.png"
        self.tangentOutline = 1
        self.surfaceConformedBrushVertices = 0
        self.record = 0
        self.importreassign = 0
        self.selectclonesource = 0
        self.preserveclonesource = 1
        self.dynclonemode = 1
        self.pickColor = 0
        self.expandfilename = 0
        self.usepressure = 1
        self.reflectionaboutorigin = 0
        self.reflection = 0
        self.projective = 0
        self.showactive = 1
        self.brushfeedback = 1
        self.outwhilepaint = 0
        self.outline = 1
        self.accopacity = 0
        self.brushalignment = 1
        self.exportaspectratio = 1
        self.stampDepth = 0.5
        self.stampSpacing = 0.1
        self.screenRadius = 1
        self.worldRadius = 1
        self.lowerradius = 0.001
        self.opacity = 0
        self.reflectionaxis = "x"
        self.exportfiletype = "IFF"
        self.exportfilemode = "luminance"
        self.importfilemode = "luminance"
        self.strokesmooth = "spline"
        self.mappressure = "Opacity"
        self.paintmode = "tangent"
        self.paintoperationtype = "Paint"
        self.dragSlider = "none"
        self.radius = 1
        self.stampProfile = "poly"
        self.exportfilesizex = 256
        self.exportfilesizey = 256
        self.whichTool = "skinWeights"
        self.selectedattroper = "absolute"
        self.value = 1
        self.minvalue = 0
        self.maxvalue = 1
        self.clamplower = 0
        self.clampupper = 1
        self.alphaclamplower = 0
        self.alphaclampupper = 1
        self.clamp = "none"
        self.alphaclamp = "none"
        self.dataTypeIndex = 1
        self.colorfeedback = 1
        self.colorfeedbackOverride = 0
        self.disablelighting = 1
        self.colorrangelower = 0
        self.colorrangeupper = 1
        self.interactiveUpdate = 1
        self.colorAlphaValue = 1
        self.useColorRamp = 0
        self.useMaxMinColor = 0
        self.rampMinColor = [0, 0, 0]
        self.rampMaxColor = [1, 1, 1]
        self.colorRamp = "1,0,0,1,1,1,0.5,0,0.8,1,1,1,0,0.6,1,0,1,0,0.4,1,0,0,1,0,1"
        self.xrayJoints = 0
        self.skinPaintMode = 1
        self.paintSelectMode = 1

        # close old window is open
        if mc.window(self.window, exists=True):
            mc.deleteUI(self.window, window=True)

        # create new window
        self.window = mc.window(self.window, title=self.title)

        mc.columnLayout(adjustableColumn=True)

        mc.text(self.title)

        mc.separator(height=20)
        self.paintToolMenu_bn = mc.button(
            label="Paint Tool Menu", command=self.paintToolMenu
        )
        self.componentEditor_bn = mc.button(
            label="Component Editor", command=self.componentEditor
        )

        mc.separator(height=20)
        self.changeToObjectMode_bn = mc.button(
            label="Object Mode", command=self.changeToObjectMode
        )
        self.changeToComponentModeVerts_bn = mc.button(
            label="Select Verts", command=self.changeToComponentModeVerts
        )
        self.changeToComponentModeLine_bn = mc.button(
            label="Select Edges", command=self.changeToComponentModeLine
        )
        mc.separator(height=20)
        self.growSelection_bn = mc.button(label="Grow", command=self.growSelection)
        self.shrinkSelection_bn = mc.button(
            label="Shrink", command=self.shrinkSelection
        )
        mc.separator(height=20)
        self.add_bn = mc.button(label="Paint Mode: Add", command=self.add)
        self.smooth_bn = mc.button(label="Paint Mode: Smooth", command=self.smooth)
        mc.separator(height=20)
        self.selectTool_bn = mc.button(label="Box Select", command=self.selectTool)
        self.lassoTool_bn = mc.button(label="Lasso Select", command=self.lassoTool)
        mc.separator(height=20)
        self.selectOnlyGeo_bn = mc.button(
            label="Select only Geo", command=self.selectOnlyGeo
        )
        self.selectOnlyJNT_bn = mc.button(
            label="Select only Jnts", command=self.selectOnlyJNT
        )
        self.selectAll_bn = mc.button(label="Select All", command=self.selectAll)

        mc.separator(height=20)
        self.copy_bn = mc.button(label="copy", command=self.copy)
        self.paste_bn = mc.button(label="paste", command=self.paste)
        self.hammer_bn = mc.button(label="hammer", command=self.hammer)

        mc.separator(height=20)
        self.resetControl_bn = mc.button(
            label="resetControl", command=self.resetControl
        )
        self.mirror_bn = mc.button(label="mirror skin weights", command=self.mirror)

        mc.setParent("..")

        # display new window
        mc.showWindow()

    def paintToolMenu(self, *args):
        sel = mc.ls(sl=1)[0]
        mel.eval(
            "ArtPaintSkinWeightsToolOptions; paintSkinWeightsChangeSelectMode {0};".format(
                sel
            )
        )
        mel.eval(
            "setSelectMode components Components; selectType -smp 0 -sme 0 -smf 0 -smu 0 -pv 0 -pe 0 -pf 0 -puv 0 -meshComponents 1; HideManipulators;"
        )
        mel.eval("selectType -cv false;")
        mel.eval("selectType -latticePoint false;")
        mel.eval("selectType -particle true;")
        mel.eval('setComponentPickMask "Point" true;')
        mel.eval('setComponentPickMask "ParmPoint" false;')
        mel.eval('setComponentPickMask "Line" false;')
        mel.eval('setComponentPickMask "Facet" false;')
        mel.eval('setComponentPickMask "Hull" false;')
        mel.eval('setComponentPickMask "Pivot" false;')
        mel.eval('setComponentPickMask "Marker" false;')
        mel.eval('setComponentPickMask "Other" false;')
        mel.eval('setComponentPickMask "Hull" false;')
        mel.eval(
            "artAttrCtx -e -useColorRamp true artAttrSkinContext ; artisanUpdateRampColorEnable;"
        )

    def componentEditor(self, *args):
        mel.eval("ComponentEditor;")

    def changeToObjectMode(self, *args):
        mel.eval("changeSelectMode -object;")

    def changeToComponentModeVerts(self, *args):
        mel.eval("SelectVertexMask;")
        mel.eval("artAttrSkinSetPaintMode 0")
        mel.eval("changeSelectMode -component;")
        mel.eval('setComponentPickMask "Point" true;')
        mel.eval("selectType -cv false;")
        mel.eval("selectType -latticePoint false;")
        mel.eval("selectType -particle false;")
        mel.eval('setComponentPickMask "ParmPoint" false;')
        mel.eval('setComponentPickMask "Line" false;')
        mel.eval('setComponentPickMask "Facet" false;')
        mel.eval('setComponentPickMask "Hull" false;')
        mel.eval('setComponentPickMask "Pivot" false;')
        mel.eval('setComponentPickMask "Marker" false;')
        mel.eval('setComponentPickMask "Other" false;')
        mel.eval('setComponentPickMask "Hull" false;')

    def changeToComponentModeLine(self, *args):
        mel.eval("SelectEdgeMask;")
        mel.eval("artAttrSkinSetPaintMode 0")
        mel.eval("changeSelectMode -component;")
        mel.eval('setComponentPickMask "Point" false;')
        mel.eval("selectType -cv false;")
        mel.eval("selectType -latticePoint false;")
        mel.eval("selectType -particle false;")
        mel.eval('setComponentPickMask "ParmPoint" false;')
        mel.eval('setComponentPickMask "Line" true;')
        mel.eval('setComponentPickMask "Facet" false;')
        mel.eval('setComponentPickMask "Hull" false;')
        mel.eval('setComponentPickMask "Pivot" false;')
        mel.eval('setComponentPickMask "Marker" false;')
        mel.eval('setComponentPickMask "Other" false;')
        mel.eval('setComponentPickMask "Hull" false;')

    def growSelection(self, *args):
        mel.eval("select `ls -sl`;PolySelectTraverse 1;select `ls -sl`;")

    def shrinkSelection(self, *args):
        mel.eval("select `ls -sl`;PolySelectTraverse 2;select `ls -sl`;")

    def add(self, *args):
        self.paintToolMenu()
        mel.eval("selectType -cv false;")
        mel.eval("selectType -latticePoint false;")
        mel.eval("selectType -particle true;")
        mel.eval('setComponentPickMask "Point" true;')
        mel.eval('setComponentPickMask "ParmPoint" false;')
        mel.eval('setComponentPickMask "Line" false;')
        mel.eval('setComponentPickMask "Facet" false;')
        mel.eval('setComponentPickMask "Hull" false;')
        mel.eval('setComponentPickMask "Pivot" false;')
        mel.eval('setComponentPickMask "Marker" false;')
        mel.eval('setComponentPickMask "Other" false;')
        mel.eval('setComponentPickMask "Hull" false;')

        sel = mc.ls(sl=1)
        mc.select(sel[:])
        mel.eval("artAttrSkinSetPaintMode 1")

        mel.eval("artAttrPaintOperation artAttrSkinPaintCtx Add")
        mel.eval("artSkinInflListChanged artAttrSkinPaintCtx;")

    def smooth(self, *args):
        self.paintToolMenu()
        mel.eval("artAttrSkinSetPaintMode 1")
        mel.eval("artAttrPaintOperation artAttrSkinPaintCtx Smooth")

    def selectOnlyJNT(self, *args):

        mel.eval('setObjectPickMask "All" 0;')
        mel.eval('setObjectPickMask "Joint" true;')

    def selectOnlyGeo(self, *args):

        mel.eval('setObjectPickMask "All" 0;')
        mel.eval('setObjectPickMask "Surface" true;')

    def selectAll(self, *args):

        mel.eval('setObjectPickMask "All" 1;')

    def lassoTool(self, *args):

        mc.setToolTo(mel.eval("$tempVar = $gLasso"))

    def selectTool(self, *args):

        mc.setToolTo("selectSuperContext")

    def copy(self, *args):

        mel.eval("artAttrSkinWeightCopy;")

    def paste(self, *args):
        mel.eval("artAttrSkinWeightPaste;")

    def hammer(self, *args):
        mel.eval("weightHammerVerts;")

    def resetControl(self, *args):

        mesh = mc.ls(sl=1)

        mel.eval("SelectAllNURBSCurves;")

        mel.eval(
            """string $ctrlName[] = `ls -sl`;
            for ($con in $ctrlName){
            catchQuiet(`setAttr ($con + ".translateX") 0`);
            catchQuiet(`setAttr ($con + ".translateY") 0`);
            catchQuiet(`setAttr ($con + ".translateZ") 0`);
            catchQuiet(`setAttr ($con + ".rotateX") 0`);
            catchQuiet(`setAttr ($con + ".rotateY") 0`);
            catchQuiet(`setAttr ($con + ".rotateZ") 0`);
            catchQuiet(`setAttr ($con + ".scaleX") 1`);
            catchQuiet(`setAttr ($con + ".scaleY") 1`);
            catchQuiet(`setAttr ($con + ".scaleZ") 1`);
            }
            """
        )

        mc.select(mesh)
        self.paintToolMenu()
        self.add()

    def mirror(self, *args):

        mesh = mc.ls(sl=1)

        mel.eval("SelectAllNURBSCurves;")

        mel.eval(
            """string $ctrlName[] = `ls -sl`;
            for ($con in $ctrlName){
            catchQuiet(`setAttr ($con + ".translateX") 0`);
            catchQuiet(`setAttr ($con + ".translateY") 0`);
            catchQuiet(`setAttr ($con + ".translateZ") 0`);
            catchQuiet(`setAttr ($con + ".rotateX") 0`);
            catchQuiet(`setAttr ($con + ".rotateY") 0`);
            catchQuiet(`setAttr ($con + ".rotateZ") 0`);
            catchQuiet(`setAttr ($con + ".scaleX") 1`);
            catchQuiet(`setAttr ($con + ".scaleY") 1`);
            catchQuiet(`setAttr ($con + ".scaleZ") 1`);
            }
            """
        )

        mc.select(mesh)

        mel.eval("MirrorSkinWeightsOptions;")
        mel.eval("performMirrorSkinWeights true;")


# myWindow = SkinOps_Painter()
