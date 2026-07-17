import maya.cmds as mc


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
