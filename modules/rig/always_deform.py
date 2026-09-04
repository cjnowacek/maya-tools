"""Rebind the selected mesh without losing its skin weights.

Select a skinned mesh and run. The tool finds every skin cluster on the mesh,
exports its weights to JSON (under the project's sourceimages/tmp), unbinds,
rebinds the same joints with standard settings (classic linear, max 4
influences, normalized), and re-imports the weights by vertex index.

Use it when a bind has accumulated bad settings or stale influences and you
want a clean skinCluster with identical deformation. Requires a saved scene
inside a Maya project (the JSON path is derived from the scenes directory).
"""

import os
import logging
from maya import cmds as mc

logger = logging.getLogger(__name__)

# Read by the toolset UI (core/toolset_master.py): description fills the
# collapsible panel, params refine the auto-generated input widgets.
TOOL_META = {
    "description": (
        "Rebind the selected mesh without losing its skin weights.\n\n"
        "Finds every skin cluster on the selected mesh, exports its weights "
        "to JSON (sourceimages/tmp), unbinds, rebinds the same joints with "
        "clean settings (classic linear, max 4 influences, normalized), and "
        "re-imports the weights by vertex index.\n\n"
        "Requires: a skinned mesh selected, and a saved scene inside a Maya "
        "project (the JSON path is derived from the scenes directory)."
    ),
}

# TODO: Add functionality for multiple meshes

jointList = []
unique_names = []
meshSelected = []
file_path = ""
directory = ""
directorySourceimages = ""
directorySourceimagesTmp = ""


def GetBoneNames():
    """Finds all the joints connected to the selected mesh's skin cluster."""
    descendants = mc.listRelatives(meshSelected, allDescendents=True) or []
    printed_skin_clusters = set()

    logger.debug("----- Always Deform Readout -----")

    for obj in descendants:
        if mc.objectType(obj) == "mesh":
            logger.debug(f"mesh FOUND! -> {obj}")
            meshConnections = mc.listConnections(obj, type="skinCluster")
            for skin_cluster in meshConnections:
                if skin_cluster not in printed_skin_clusters:
                    logger.debug(f"skinCluster FOUND! -> {skin_cluster}")
                    printed_skin_clusters.add(skin_cluster)
                jointConnections = mc.listConnections(skin_cluster, type="joint")
                for joint in jointConnections:
                    if mc.objectType(joint) == "joint":
                        jointList.append(joint)
        else:
            logger.debug("No mesh found on this descendant.")

    # Filter unique joint names
    for joint in jointList:
        if joint not in unique_names:
            unique_names.append(joint)

    return unique_names, list(printed_skin_clusters)


def ExportSkinCluster(skin_clusters, joint_names):
    """Exports skin weights of the specified skin clusters to a JSON file."""
    if file_path:
        os.makedirs(directorySourceimages, exist_ok=True)
        os.makedirs(directorySourceimagesTmp, exist_ok=True)

        if skin_clusters:
            for skin_cluster in skin_clusters:
                mc.select(skin_cluster)
                export_name = f"{meshSelected[0]}_skinWeights.json"
                logger.debug(f"Exporting weights to {directorySourceimagesTmp}")
                mc.deformerWeights(
                    export_name,
                    ex=True,
                    df=skin_cluster,
                    fm="JSON",
                    p=directorySourceimagesTmp,
                )
                mc.skinCluster(skin_cluster, edit=True, unbind=True)

                new_SC = mc.skinCluster(
                    joint_names,
                    meshSelected[0],
                    n=meshSelected[0] + "_SC",
                    toSelectedBones=True,
                    bindMethod=0,
                    maximumInfluences=4,
                    skinMethod=0,
                    normalizeWeights=1,
                )

                mc.deformerWeights(
                    export_name,
                    im=True,
                    method="index",
                    deformer=new_SC[0],
                    p=directorySourceimagesTmp,
                )
        else:
            logger.warning("No skin clusters provided to select.")
    else:
        logger.warning("No valid scene file found.")


def run():
    """Main function to run the skin cluster export and reset."""
    global meshSelected, file_path, directory, directorySourceimages, directorySourceimagesTmp
    global jointList, unique_names

    jointList = []
    unique_names = []
    meshSelected = mc.ls(sl=1)

    if not meshSelected:
        logger.warning("No mesh selected.")
        return

    file_path = mc.file(query=True, sceneName=True)
    directory = os.path.dirname(file_path)
    directorySourceimages = directory.replace("scenes", "sourceimages")
    directorySourceimagesTmp = directory.replace("scenes", "sourceimages/tmp")

    joint_names, skin_clusters = GetBoneNames()

    logger.debug(f"FULL JOINT LIST for mesh -> {meshSelected[0]}")

    if joint_names:
        logger.debug(f"UNIQUE JOINT NAMES -> {joint_names}")
    else:
        logger.debug("No unique joints found.")

    if skin_clusters:
        logger.debug(f"SKIN CLUSTERS FOUND -> {skin_clusters}")
    else:
        logger.debug("No skin clusters found.")

    ExportSkinCluster(skin_clusters, joint_names)


def main(*args):
    run()


if __name__ == "__main__":
    main()
