import maya.cmds as mc

TOOL_META = {
    "description": (
        "Move all animation from one object to another.\n\n"
        "Select the SOURCE object, then the TARGET, and run. Keys are CUT "
        "from the source (it loses its animation) and pasted onto the "
        "target, replacing whatever was there."
    ),
}


def main(*args):
    CopyPasteKeys()


class CopyPasteKeys(object):

    def __init__(self):
        sel = mc.ls(sl=True)
        if len(sel) < 2:
            mc.warning("Select a source object and at least one target object.")
            return
        mc.cutKey(sel[0], animation="objects", option="keys")
        mc.pasteKey(sel[1], animation="objects", option="replaceCompletely")
