import maya.cmds as mc
import maya.mel as mel


def main():
    ReloadFile()


class ReloadFile(object):
    
    
    filepath = mc.file(q=True, sn=True)
    newfilepath = filepath + "untitled.ma"
    
    try:
        
        mc.file(filepath, open=True, force=True)
    except:
        mc.file(newfilepath, save = 1, force=True)
        filepath = mc.file(q=True, sn=True)
        mc.file(filepath, open=True, force=True)