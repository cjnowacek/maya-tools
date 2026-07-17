import maya.cmds as mc
import maya.mel as mel


def main(*args):
    AnimMacros()


class AnimMacros(object):

    # constructor
    def __init__(self):

        self.window = "AnimMacros"
        self.title = "Anim Macros"
        self.height = 120
        self.width = 150

        # close old window is open
        if mc.window(self.window, exists=True):
            mc.deleteUI(self.window, window=True)

        # create new window
        self.window = mc.window(self.window, title=self.title)

        mc.columnLayout(adjustableColumn=True)

        mc.text(self.title)
        mc.separator(height=20)

        self.resetControl_bn = mc.button(
            label="resetControl", command=self.resetControl
        )
        self.crvsSelectOnly_bn = mc.button(
            label="only Select Curves", command=self.selectOnlyCRVs
        )
        self.createLocAt_bn = mc.button(label="create Loc At", command=self.createLocAt)
        mc.separator(height=20)
        mc.text("Timeline Key Tools")
        mc.separator(height=10)
        self.cutKeys_bn = mc.button(label="Cut", command=self.cutKeys)
        self.addInbetween_bn = mc.button(label="+ Inbetween", command=self.addInbetween)
        self.removeInbetween_bn = mc.button(
            label="- Inbetween", command=self.removeInbetween
        )
        mc.separator(height=20)
        mc.text("Graph Editor Key Tools")
        mc.separator(height=10)
        self.cutKeys_bn = mc.button(label="Cut", command=self.GEcutKeys)
        self.LoopVis_bn = mc.button(
            label="Visulize Loop", command=self.graphEditorPrepPostLoop
        )
        mc.separator(height=20)
        mc.text("manipulator space")
        mc.separator(height=10)
        self.world_bn = mc.button(label="world space", command=self.wldSpace)
        self.obj_bn = mc.button(label="object space", command=self.objSpace)

        mc.setParent("..")

        # display new window
        mc.showWindow()
        mc.window(
            self.window,
            e=True,
            height=self.height,
            width=self.width,
            mnb=False,
            mxb=False,
        )

    def resetControl(self, *args):

        mel.eval("""string $ctrlName[] = `ls -sl`;
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
            """)

    def selectOnlyCRVs(self, *args):

        mc.select(cl=1)

        mel.eval('setObjectPickMask "All" 0;')
        mel.eval('setObjectPickMask "Curve" true;')

    def createLocAt(self, *args):

        list = []

        sel = mc.ls(sl=1)[0]
        loc = mc.spaceLocator()[0]

        list.append(loc)
        list.append(sel)

        mc.select(list[:])
        mel.eval("MatchTransform;")

    def addInbetween(self, *args):

        mel.eval("timeSliderEditKeys addInbetween;")

    def removeInbetween(self, *args):

        mel.eval("timeSliderEditKeys removeInbetween;")

    def objSpace(self, *args):

        mel.eval("manipMoveContext -edit -mode 0 Move;")
        mel.eval("manipRotateContext -e -mode 0 Rotate;")

    def wldSpace(self, *args):

        mel.eval("manipMoveContext -edit -mode 2 Move;")
        mel.eval("manipRotateContext -e -mode 1 Rotate;")

    def cutKeys(self, *args):

        mel.eval("timeSliderCutKey;")

    def GEcutKeys(self, *args):

        mel.eval("cutKey;")

    def graphEditorPrepPostLoop(self, *args):

        mel.eval("setInfinity -pri cycle graphEditor1FromOutliner;")
        mel.eval("setInfinity -poi cycle graphEditor1FromOutliner;")
