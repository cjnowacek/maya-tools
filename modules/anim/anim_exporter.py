import logging
import maya.cmds as mc

logger = logging.getLogger(__name__)


class AnimOpsExportPrep(object):
    """
    Prepares Maya scene for animation export by managing namespaces and selecting objects.
    """

    def __init__(self):
        self.skl_sel = []
        self.geo_sel = []
        self.final_sel = []
        self.rigs = []
        self.window_name = "animOpsExportPrepUI"

    def run(self):
        """
        Main execution method that runs the namespace cleanup and selection process.
        """
        self._find_rigs()
        self._show_ui()

    def _find_rigs(self):
        """
        Find all transforms named 'rig' in the scene.
        """
        # Find all transforms in the scene
        all_transforms = mc.ls(type="transform")

        # Filter for transforms that are named 'rig' or end with 'rig'
        self.rigs = [
            transform
            for transform in all_transforms
            if transform == "rig" or transform.endswith("_rig")
        ]

        return self.rigs

    def _manage_namespaces(self):
        """
        Handle namespaces: remove unwanted ones and merge with parent.
        """
        default_namespaces = ["UI", "shared"]
        namespaces = mc.namespaceInfo(lon=True)

        for ns in namespaces:
            if ns not in default_namespaces:
                try:
                    mc.namespace(removeNamespace=ns, mergeNamespaceWithParent=True)
                except Exception as e:
                    logger.warning(f"Could not merge namespace '{ns}': {e}")

    def _process_rig(self, rig_name):
        """
        Process a specific rig to find its geometry and skeleton components.

        Args:
            rig_name (str): The name of the rig to process
        """
        self.skl_sel = []
        self.geo_sel = []
        self.final_sel = []

        # Look for SKL_lyr and GEO_lyr under this rig
        skl_layer = f"{rig_name}:SKL_lyr"
        geo_layer = f"{rig_name}:GEO_lyr"

        # If no namespace, try without it
        if not mc.objExists(skl_layer):
            skl_layer = "SKL_lyr"

        if not mc.objExists(geo_layer):
            geo_layer = "GEO_lyr"

        # Process skeleton layer
        if mc.objExists(skl_layer):
            mc.select(skl_layer)
            connections = mc.listConnections(skl_layer) or []
            self.skl_sel = connections[1:] if len(connections) > 1 else []
        else:
            logger.debug(f"'{skl_layer}' not found for rig '{rig_name}'")

            # Try to find skeleton parts by naming convention
            potential_skeletons = (
                mc.listRelatives(rig_name, allDescendents=True, type="joint") or []
            )
            if potential_skeletons:
                self.skl_sel = potential_skeletons
                logger.debug(
                    f"Found {len(self.skl_sel)} skeleton parts by hierarchy for '{rig_name}'"
                )

        # Process geometry layer
        if mc.objExists(geo_layer):
            mc.select(geo_layer)
            connections = mc.listConnections(geo_layer) or []
            self.geo_sel = connections[1:] if len(connections) > 1 else []
        else:
            logger.debug(f"'{geo_layer}' not found for rig '{rig_name}'")

            # Try to find geometry parts by naming convention
            potential_geo = (
                mc.listRelatives(rig_name, allDescendents=True, type="mesh") or []
            )
            # Get the transform nodes of the meshes
            if potential_geo:
                geo_transforms = [
                    mc.listRelatives(geo, parent=True)[0] for geo in potential_geo
                ]
                self.geo_sel = list(set(geo_transforms))  # Remove duplicates
                logger.debug(
                    f"Found {len(self.geo_sel)} geometry parts by hierarchy for '{rig_name}'"
                )

        # Compile final selection
        self.final_sel = self.geo_sel + self.skl_sel

        if self.final_sel:
            mc.select(self.final_sel)
            return True
        else:
            logger.warning(f"No objects found to select for '{rig_name}'")
            return False

    def _select_and_compile_all(self, *args):
        """
        Process all selected rigs in the UI.
        """
        # Get selected items from the list
        selected_rigs = mc.textScrollList("rigList", query=True, selectItem=True) or []

        if not selected_rigs:
            mc.confirmDialog(
                title="Warning",
                message="Please select at least one rig from the list.",
                button=["OK"],
                defaultButton="OK",
            )
            return

        all_selected = []
        for rig in selected_rigs:
            self._process_rig(rig)
            all_selected.extend(self.final_sel)

        if all_selected:
            self.final_sel = all_selected
            mc.select(self.final_sel)

            # Optionally manage namespaces if checkbox is checked
            if mc.checkBox("namespaceCheckbox", query=True, value=True):
                self._manage_namespaces()

            mc.confirmDialog(
                title="Success",
                message=f"Selected {len(self.final_sel)} objects from {len(selected_rigs)} rigs.",
                button=["OK"],
                defaultButton="OK",
            )
        else:
            mc.confirmDialog(
                title="Warning",
                message="No objects found to select.",
                button=["OK"],
                defaultButton="OK",
            )

    def _refresh_rig_list(self, *args):
        """
        Refresh the list of rigs in the scene.
        """
        self._find_rigs()
        mc.textScrollList("rigList", edit=True, removeAll=True)
        if self.rigs:
            mc.textScrollList("rigList", edit=True, append=self.rigs)
        else:
            mc.confirmDialog(
                title="Info",
                message="No rigs found in the scene. Look for transforms named 'rig' or ending with '_rig'.",
                button=["OK"],
                defaultButton="OK",
            )

    def _show_ui(self):
        """
        Create and display the UI for rig selection and export prep.
        """
        # Close existing window if it exists
        if mc.window(self.window_name, exists=True):
            mc.deleteUI(self.window_name)

        # Create window
        window = mc.window(
            self.window_name,
            title="Animation Export Preparation",
            width=400,
            height=400,
        )

        # Main layout
        main_layout = mc.columnLayout(adjustableColumn=True, columnAlign="center")

        # Header
        mc.text(
            label="Animation Export Preparation",
            height=30,
            backgroundColor=[0.2, 0.2, 0.2],
            font="boldLabelFont",
        )
        mc.separator(height=10, style="none")

        # Rig list section
        mc.frameLayout(
            label="Available Rigs", collapsable=False, marginWidth=10, marginHeight=10
        )
        mc.rowLayout(
            numberOfColumns=2,
            columnWidth2=(320, 60),
            adjustableColumn=1,
            columnAlign=(1, "left"),
        )

        # Rig list
        mc.textScrollList(
            "rigList", numberOfRows=8, allowMultiSelection=True, width=320, height=150
        )

        # Refresh button
        mc.columnLayout(adjustableColumn=True)
        mc.button(label="Refresh", command=self._refresh_rig_list, width=60, height=30)
        mc.setParent("..")  # Return to row layout

        mc.setParent("..")  # Return to frame layout
        mc.setParent("..")  # Return to main layout

        # Options section
        mc.frameLayout(
            label="Options", collapsable=False, marginWidth=10, marginHeight=10
        )
        mc.columnLayout(adjustableColumn=True)

        # Namespace option
        mc.checkBox("namespaceCheckbox", label="Clean up namespaces", value=False)

        mc.setParent("..")  # Return to frame layout
        mc.setParent("..")  # Return to main layout

        # Buttons section
        mc.separator(height=10)
        mc.rowLayout(
            numberOfColumns=2,
            columnWidth2=(180, 180),
            adjustableColumn=1,
            columnAlign=(1, "center"),
        )

        # Action buttons
        mc.button(
            label="Process Selected Rigs",
            command=self._select_and_compile_all,
            width=180,
            height=40,
        )
        mc.button(
            label="Close",
            command=lambda *args: mc.deleteUI(self.window_name),
            width=180,
            height=40,
        )

        mc.setParent("..")  # Return to main layout

        # Status info
        mc.separator(height=10)
        rig_count = len(self.rigs)
        status_message = (
            f"Found {rig_count} rig{'s' if rig_count != 1 else ''} in the scene."
        )
        mc.text(label=status_message, height=20)

        # Show window
        mc.showWindow(window)

        # Populate the list
        self._refresh_rig_list()


def main(*args):
    """
    Main function to run the export preparation process.
    """
    exporter = AnimOpsExportPrep()
    exporter.run()
    return exporter


if __name__ == "__main__":
    main()
