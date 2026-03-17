"""
File: FlipUpAxis.py
Author: CJ Nowacek
Created Date: NA
Description: Flips scene between Y and Z up
"""
import maya.cmds as cmds


def main(*args):

    FlipUpAxis()


def FlipUpAxis():
    # check the current axis
    current_axis = cmds.upAxis(query=True, axis=True)

    if current_axis == 'z':
        cmds.upAxis(axis='y', rotateView=True)
    else:
        cmds.upAxis(axis='z', rotateView=True)
