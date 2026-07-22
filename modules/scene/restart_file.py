import os
import maya.cmds as mc


def main(*args):
    ReloadFile()


class ReloadFile(object):

    def __init__(self):
        filepath = mc.file(q=True, sn=True)
        newfilepath = os.path.join(
            os.path.dirname(filepath) or os.getcwd(), "untitled.ma"
        )

        try:
            mc.file(filepath, open=True, force=True)
        except:
            mc.file(newfilepath, save=1, force=True)
            filepath = mc.file(q=True, sn=True)
            mc.file(filepath, open=True, force=True)
