"""
/model/Export_GeoBatcher.py

This script provides a Maya user interface for exporting selected geometries
in multiple file formats, including OBJ, FBX, and STL. Users can choose
the desired export type and specify the export path.

### Features:
- Export selected geometries as OBJ, FBX, or STL files.
- Provide feedback for STL file naming issues.
- Ensure correct handling of file paths and parent-child relationships.

### Usage:
1. Run the `main` function to launch the exporter UI.
2. Select the export format (OBJ, FBX, or STL).
3. Specify the export path.
4. Click "Export" to save the selected geometries.

### Metadata:
- **Author:** CJ Nowacek
- **Version:** 1.0.2
- **License:** GPL
- **Maintainer:** CJ Nowacek
- **Email:** cj.nowacek@gmail.com
- **Status:** Production
"""

import maya.cmds as mc
import os


TOOL_META = {
    "description": (
        'Batch geometry exporter (opens its own window).\n\n'
        'Export the selected meshes as OBJ, FBX, or STL files to a chosen '
        'path, one file per mesh. Flags STL naming issues and preserves '
        'parent/child relationships while exporting.'
    ),
}


def main(*args):
    """Launch the ToolOps Batch Geometry Exporter UI."""
    ToolOpsBatchGeoExporter()


class ToolOpsBatchGeoExporter(object):
    """A class to handle batch exporting of geometries in Maya."""

    def __init__(self):
        """Initialize the UI for the batch geometry exporter."""
        self.window = "ToolOps_BatchGeoExporter"
        self.title = "Mesh Exporter"
        self.size = (400, 150)

        self.create_ui()

    def create_ui(self):
        """Create and display the UI window."""
        # Close old window if open
        if mc.window(self.window, exists=True):
            mc.deleteUI(self.window, window=True)

        # Create new window
        self.window = mc.window(self.window, title=self.title, widthHeight=self.size)

        mc.columnLayout(adjustableColumn=True)
        mc.text(self.title, font="boldLabelFont")
        mc.separator(height=10)

        # Export type menu
        mc.text("Select Export Type:")
        self.options_menu = mc.optionMenu("exportTypeMenu", label="Export Type")
        mc.menuItem(label="OBJ")
        mc.menuItem(label="FBX")
        mc.menuItem(label="STL")

        mc.separator(height=10)

        # Path input field
        mc.text("Specify Export Path:")
        self.path_field = mc.textFieldGrp(label="Path:", text="C:/export/")

        mc.separator(height=10)

        # Export button
        self.export_btn = mc.button(
            label="Export", command=self.export_stuff, width=200
        )

        mc.showWindow()

    def export_stuff(self, *args):
        """Export selected geometries based on the chosen type and path."""
        selections = mc.ls(sl=True)

        # Get input path
        path = mc.textFieldGrp(self.path_field, q=True, text=True)
        if not path:
            mc.error("Please input a valid path.")
        corrected_path = path.replace('"', "")

        # Verify the directory exists
        if not os.path.exists(corrected_path):
            mc.error(f"Directory does not exist: {corrected_path}")
            return

        # Get export type and options
        export_type = mc.optionMenu(self.options_menu, q=True, value=True).lower()
        type_option, options = self._get_export_options(export_type)

        if not type_option:
            return

        # Export each selected object
        for obj in selections:
            mc.select(obj)

            # Handle parent nodes
            parent_node = mc.listRelatives(obj, parent=True)
            if parent_node:
                mc.parent(obj, world=True)

            # Perform export
            file_path = os.path.join(corrected_path, f"{obj}.{export_type}")
            try:
                mc.file(
                    file_path,
                    force=True,
                    options=options,
                    type=type_option,
                    preserveReferences=True,
                    exportSelected=True,
                )
            except Exception as e:
                mc.error(f"Error exporting file: {file_path}\n{str(e)}")
                return

            # Warn for STL file naming
            if export_type == "stl":
                mc.confirmDialog(
                    title="STL Warning",
                    message="STL export might not name files correctly. Add the .stl suffix manually.",
                    button=["OK"],
                )

            # Reparent objects
            if parent_node:
                mc.parent(obj, parent_node)

    def _get_export_options(self, export_type):
        """Return the appropriate file type and options based on the export type."""
        options_dict = {
            "obj": (
                "OBJexport",
                "groups=1;ptgroups=1;materials=1;smoothing=1;normals=1",
            ),
            "fbx": ("FBX export", "v=0;"),
            "stl": (
                "STLexport",
                "groups=1;ptgroups=1;materials=1;smoothing=1;normals=1",
            ),
        }

        if export_type in options_dict:
            return options_dict[export_type]
        else:
            mc.error("Please select a valid geometry export type.")
            return None, None


if __name__ == "__main__":
    main()
