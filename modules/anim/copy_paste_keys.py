import maya.cmds as mc
import maya.mel as mel


def main():
    CopyPasteKeys()


class CopyPasteKeys(object):

    def __init__(self):
        sel = mc.ls(sl=True)
        mc.cutKey(sel[0], animation='objects', option='keys')
        mc.pasteKey(sel[1], animation='objects', option='replaceCompletely')
