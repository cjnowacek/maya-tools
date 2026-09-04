import maya.cmds as mc
import maya.mel as mel

TOOL_META = {
    "description": (
        "Assume Preferred Angle on a whole joint hierarchy.\n\n"
        "Select the root joint and run: every joint BELOW the root (the root "
        "itself is excluded) snaps to its stored preferred angle. Handy for "
        "restoring a bent rest pose before building IK, or recovering a "
        "chain after zeroing rotations. Selection is restored afterward."
    ),
}


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
