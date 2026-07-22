# config.py
"""
Configuration module for Maya rigging tools.
Centralizes paths, settings and constants used across the toolset.
"""

import os
import maya.cmds as cmds


class Config:
    """Configuration class for Maya rigging tools."""

    # Root directory is the directory where this file is located
    ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Tool categories and their directories
    # Keys must match the on-disk folder casing exactly; Windows tolerates
    # mismatches but Linux/macOS do not
    TOOL_PATHS = {
        "model": os.path.join(ROOT_DIR, "modules", "model"),
        "rig": os.path.join(ROOT_DIR, "modules", "rig"),
        "anim": os.path.join(ROOT_DIR, "modules", "anim"),
        "scene": os.path.join(ROOT_DIR, "modules", "scene"),
        "wip": os.path.join(ROOT_DIR, "modules", "wip"),
    }

    # UI settings
    UI = {
        "toolset_master": {"title": "Toolset Master", "width": 400, "height": 125},
        "rig_master": {"title": "Rig Master", "width": 400, "height": 500},
    }

    # Default values
    DEFAULTS = {"joint_radius": 1.0, "orientation": "xyz", "secondary_axis": "zup"}

    # Class variables - shared across all uses of this class
    filepath = ""
    filename = ""
    raw_name = ""
    extension = ""
    desktop_path = ""

    @classmethod
    def update_paths(cls):
        # Updates the class variables using the cls parameter
        cls.filepath = cmds.file(q=True, sn=True)
        cls.filename = os.path.basename(cls.filepath)
        cls.raw_name, cls.extension = os.path.splitext(cls.filename)

    @classmethod
    def get_tool_path(cls, category):
        """Get the directory path for a specific tool category."""
        return cls.TOOL_PATHS.get(category.lower(), "")

    @classmethod
    def get_ui_config(cls, tool_name):
        """Get UI configuration for a specific tool."""
        return cls.UI.get(tool_name, {})
