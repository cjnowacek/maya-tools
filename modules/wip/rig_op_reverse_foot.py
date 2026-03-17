import maya.cmds as mc


class FootOps_ReverseFoot(object):

    # constructor
    def __init__(self):

        self.side = "L"

        self.ankle = "L_Ankle_BN_JNT"
        self.ball = ""
        self.toe = ""
        self.heel = ""

        self.window = "FootOps_ReverseFoot"
        self.title = "FootOps_ReverseFoot"
        self.size = (400, 80)

        # close old window is open
        if mc.window(self.window, exists=True):
            mc.deleteUI(self.window, window=True)

        # create new window
        self.window = mc.window(self.window, title=self.title, widthHeight=(self.size))

        mc.columnLayout(adjustableColumn=True)

        mc.text(self.title)
        mc.separator(height=20)

        self.name = mc.textFieldGrp(label="Side:")
        self.export_bn = mc.button(label="Export", command=self.exportStuff)
        mc.setParent("..")

        # display new window
        mc.showWindow()

    def createGuides(self, *args):
        sel = mc.ls(sl=1)

        path = mc.textFieldGrp(self.name, q=True, text=True)
        newpath = str(path.replace('"', ""))

        for i in sel:
            mc.select(i)
            parentNode = mc.listRelatives(p=True)
            hasParent = bool(mc.listRelatives(i, parent=True))
            if hasParent:
                mc.parent(i, world=True)
            mc.file(
                "{}{}{}{}".format(newpath, "\\", i, ".fbx"),
                f=True,
                options="v=0;",
                typ="FBX export",
                pr=True,
                es=True,
            )
            if hasParent:
                mc.parent(i, parentNode)


def main(*args):
    global myWindow
    myWindow = FootOps_ReverseFoot()


if __name__ == "__main__":
    main()
