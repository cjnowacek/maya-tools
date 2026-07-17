import maya.cmds as cmds
import os


def get_paths():
    """Set global file paths based on the currently opened Maya scene."""
    global ier_filepath, ier_filename, ier_raw_name, ier_extension

    ier_filepath = cmds.file(q=True, sn=True)  # Get full file path
    ier_filename = os.path.basename(ier_filepath)  # Extract file name
    ier_raw_name, ier_extension = os.path.splitext(ier_filename)  # Split extension

    return ier_filepath, ier_filename, ier_raw_name, ier_extension
