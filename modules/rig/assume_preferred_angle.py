import maya.cmds as mc
import maya.mel as mel


def main(*args):
    currentSel = mc.ls(sl=1)

    if not currentSel:
        mc.warning("Select a root joint first.")
        return

    rootJoint = currentSel[0]

    mel.eval("""
            select -r {0};
            SelectHierarchy;
            select -d {0};
            joint -e -apa -ch;
            select -d;
            """.format(rootJoint))

    mc.select(currentSel)


if __name__ == "__main__":
    main()
