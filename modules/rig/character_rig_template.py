import logging
import maya.cmds as cmds

logger = logging.getLogger(__name__)

TOOL_META = {
    "description": (
        "Create the standard character rig hierarchy template.\n\n"
        "Builds the empty group structure the rig tools expect:\n"
        "RIG > Controls / Meshes (ExportMeshes, bak) / Skeleton.\n\n"
        "Run once at the start of a new character; Character Rig Handler "
        "detects and fills this structure."
    ),
}


def main(*args):
    CharacterTemplate()


def CharacterTemplate():
    # Create the top-level node
    rig_node = cmds.createNode("transform", name="RIG")

    # Create 'Controls" nodes under 'RIG'
    cmds.createNode("transform", name="Controls", parent=rig_node)

    # Create 'Meshes' nodes under 'RIG'
    meshes_node = cmds.createNode("transform", name="Meshes", parent=rig_node)

    # Create 'ExportMeshes' and 'bak' nodes under 'Meshes'
    cmds.createNode("transform", name="ExportMeshes", parent=meshes_node)
    cmds.createNode("transform", name="bak", parent=meshes_node)

    # Create 'Skeleton' nodes under 'RIG'
    cmds.createNode("transform", name="Skeleton", parent=rig_node)

    # Log the created hierarchy for verification
    logger.debug("Hierarchy created: %s", cmds.ls(rig_node, dag=True))
