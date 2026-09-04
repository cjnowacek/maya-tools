"""
File: FlipUpAxis.py
Author: CJ Nowacek
Created Date: NA
Description: Flips scene between Y and Z up
"""

import maya.cmds as cmds


TOOL_META = {
    "description": (
        'Toggle the scene up axis between Y-up and Z-up.\n\n'
        'Reads the current axis and flips to the other, rotating the view '
        'to match. Existing objects are not rotated.'
    ),
}


def main(*args):

    FlipUpAxis()


def FlipUpAxis():
    # check the current axis
    current_axis = cmds.upAxis(query=True, axis=True)

    if current_axis == "z":
        cmds.upAxis(axis="y", rotateView=True)
    else:
        cmds.upAxis(axis="z", rotateView=True)
