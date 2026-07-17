# ------------------------------
# Imports
# ------------------------------
import maya.cmds as cmds
import os
import shutil
import json
import heapq
import logging

from core.Config import Config

logger = logging.getLogger(__name__)


def main(*args):
    Config.update_paths()

    logger.debug(Config.filepath)
    logger.debug(Config.filename)
    logger.debug(Config.raw_name)
    logger.debug(Config.extension)

    Config.desktop_path = os.path.join(
        # "C:\\" + "Dropbox\\Art\\Rigs\\__RigCompiler",
        "C:\\",
        # os.path.expanduser("~"),
        # "Desktop",
        # "characterCompilerTest",
        f"{Config.raw_name}",
    )


# ------------------------------
# Functions
# ------------------------------
def get_texture_path(mesh):
    """Retrieve the texture file path from the material assigned to the mesh."""

    # Get the shape node of the mesh
    shapes = cmds.listRelatives(mesh, shapes=True) or []
    if not shapes:
        logger.warning(
            f"No shape found for {mesh}. It may be a group or empty transform."
        )
        return None
    shape_node = shapes[0]

    # Get the shading group using listSets
    shading_groups = cmds.listSets(
        object=shape_node, type=1
    )  # Type=1 ensures it's a shading group
    if not shading_groups:
        logger.warning(f"No shading group found for {mesh}. Material might be missing.")
        return None
    shading_group = shading_groups[0]

    # Get the material from the shading group
    materials = cmds.listConnections(f"{shading_group}.surfaceShader") or []
    if not materials:
        logger.warning(f"No material found for {mesh}.")
        return None
    material = materials[0]

    # Find file nodes connected to the material
    file_nodes = cmds.listConnections(material, type="file") or []
    if not file_nodes:
        logger.warning(
            f"No file texture node found for {mesh}. It may be using procedural textures."
        )
        return None

    # Return the first valid texture path
    for file_node in file_nodes:
        if cmds.attributeQuery("fileTextureName", node=file_node, exists=True):
            file_path = cmds.getAttr(f"{file_node}.fileTextureName")
            if file_path:
                logger.info(f"Texture path for {mesh}: {file_path}")
                return file_path

    logger.warning(f"No valid texture file found for {mesh}")
    return None


def write_bone_data():
    bones = cmds.ls(type="joint")
    bone_data = {}
    parent_map = {}  # Store parent-child relationships

    os.makedirs(
        Config.desktop_path, exist_ok=True
    )  # Create the folder if it doesn’t exist

    # Step 1: Unparent all bones to get absolute orientations
    for bone in bones:
        parent = cmds.listRelatives(bone, parent=True, type="joint")
        if parent:
            parent_map[bone] = parent[0]  # Store original parent
            cmds.parent(bone, world=True)  # Temporarily unparent

    # Step 2: Gather bone data with correct orientations
    for bone in bones:
        position = cmds.xform(bone, q=True, ws=True, translation=True)
        orientation = [float(x) for x in cmds.getAttr(f"{bone}.jointOrient")[0]]
        radius = cmds.getAttr(f"{bone}.radius")

        bone_data[bone] = {
            "parent": parent_map.get(bone, None),  # Restore parent info
            "position": position,
            "orientation": orientation,
            "radius": radius,
        }

    # Step 3: Restore original parenting
    for bone, parent in parent_map.items():
        cmds.parent(bone, parent)  # Reparent bones

    # Step 4: Save data to JSON
    with open(os.path.join(Config.desktop_path, "skeleton.json"), "w") as file:
        json.dump(bone_data, file, indent=4)

    logger.info(
        f"✅ Bone data saved correctly to {os.path.join(Config.desktop_path, 'skeleton.json')}"
    )


def get_selected_meshes():
    this = cmds.ls(sl=1)
    return this


# ------------------------------
# Mesh Functions
# ------------------------------


def export_selected_meshes():
    """Exports selected meshes as OBJ files and saves a JSON file with texture paths."""
    logger.debug("=== EXPORT MESHES STARTING ===")

    # Debug print statements to verify paths
    logger.debug(f"Desktop path: {Config.desktop_path}")

    # Make sure desktop_path is an absolute path
    if not os.path.isabs(Config.desktop_path):
        logger.warning(f"{Config.desktop_path} is not an absolute path!")
        Config.desktop_path = os.path.abspath(Config.desktop_path)
        logger.debug(f"Converted to absolute path: {Config.desktop_path}")

    # Create main directory with error handling
    try:
        os.makedirs(Config.desktop_path, exist_ok=True)
        logger.debug(f"Created/verified directory: {Config.desktop_path}")
    except Exception as e:
        logger.debug(f"Error creating main directory: {e}")
        return

    # Create texture folder with improved error handling
    texture_folder = os.path.join(Config.desktop_path, "textures")
    try:
        os.makedirs(texture_folder, exist_ok=True)
        logger.debug(f"Created/verified texture directory: {texture_folder}")
    except PermissionError as e:
        logger.debug(f"Permission error creating texture directory: {e}")
        logger.debug("Trying alternative texture directory...")
        # Try creating in a more accessible location
        texture_folder = os.path.join(os.path.expanduser("~"), "maya_temp_textures")
        os.makedirs(texture_folder, exist_ok=True)
        logger.debug(f"Using alternative texture folder: {texture_folder}")
    except Exception as e:
        logger.debug(f"Error creating texture directory: {e}")
        return

    mesh_data = {}

    selected_transforms = cmds.ls(selection=True, type="transform")
    if not selected_transforms:
        logger.debug("No meshes selected!")
        return

    selected_meshes = []
    for transform in selected_transforms:
        shapes = cmds.listRelatives(transform, shapes=True, type="mesh")
        if shapes:
            selected_meshes.append(transform)

    if not selected_meshes:
        logger.debug("No valid mesh objects found!")
        return

    for mesh in selected_meshes:
        obj_file = os.path.join(Config.desktop_path, f"{mesh}.obj")

        logger.debug(f"Exporting OBJ: {obj_file}")

        cmds.select(mesh)
        cmds.file(
            obj_file,
            force=True,
            options="groups=1;ptgroups=1;materials=1;smoothing=1;normals=1",
            type="OBJexport",
            exportSelected=True,
        )

        texture_path = get_texture_path(mesh)

        # Copy texture to the textures folder and update its path
        new_texture_path = None
        if texture_path and os.path.exists(texture_path):
            new_texture_path = os.path.join(
                texture_folder, os.path.basename(texture_path)
            )
            shutil.copy(texture_path, new_texture_path)  # Copy the texture file

        mesh_data[mesh] = {"texture": new_texture_path}  # Store new relative path

    json_file = os.path.join(Config.desktop_path, "texture_data.json")
    with open(json_file, "w") as file:
        json.dump(mesh_data, file, indent=4)

    logger.info(f"Meshes and textures exported to {Config.desktop_path}")
    logger.debug("=== EXPORT MESHES COMPLETED ===")


def import_meshes_and_weights():
    """Imports OBJ files one at a time and re-links textures from the textures folder."""
    texture_folder = os.path.join(Config.desktop_path, "textures")

    json_file = os.path.join(Config.desktop_path, "texture_data.json")
    if not os.path.exists(json_file):
        logger.debug("No texture_data.json found!")
        return

    with open(json_file, "r") as file:
        mesh_data = json.load(file)

    for mesh, data in mesh_data.items():
        obj_file = os.path.join(Config.desktop_path, f"{mesh}.obj")
        if not os.path.exists(obj_file):
            logger.debug(f"OBJ file missing for {mesh}, skipping import.")
            continue

        logger.debug(f"Importing: {obj_file}")

        before_import = set(cmds.ls(transforms=True))
        cmds.file(obj_file, i=True, renameAll=False, mergeNamespacesOnClash=False)
        after_import = set(cmds.ls(transforms=True))
        imported_objects = list(after_import - before_import)

        logger.debug(f"Imported Objects: {imported_objects}")

        imported_mesh = None
        for obj in imported_objects:
            if obj.lower().startswith(mesh.lower()):
                imported_mesh = obj
                break

        if not imported_mesh:
            logger.debug(
                f"Could not find {mesh} after import! Check object names in Maya."
            )
            continue

        if imported_mesh != mesh:
            cmds.rename(imported_mesh, mesh)
            imported_mesh = mesh

        logger.debug(f"Final Imported Mesh Name: {imported_mesh}")

        material_name = f"{mesh}_mat"
        shading_group = f"{material_name}_SG"
        file_node = f"{mesh}_tex"
        place2d_node = f"{mesh}_place2d"

        if not cmds.objExists(material_name):
            material = cmds.shadingNode(
                "standardSurface", asShader=True, name=material_name
            )
            shading_group = cmds.sets(
                renderable=True, noSurfaceShader=True, empty=True, name=shading_group
            )
            cmds.connectAttr(
                f"{material}.outColor", f"{shading_group}.surfaceShader", force=True
            )
        else:
            material = material_name

        cmds.sets(mesh, edit=True, forceElement=shading_group)

        # Re-link the texture from the textures folder
        texture_path = data.get("texture")
        if texture_path and os.path.exists(texture_path):
            if not cmds.objExists(file_node):
                file_texture = cmds.shadingNode("file", asTexture=True, name=file_node)
            else:
                file_texture = file_node

            if not cmds.objExists(place2d_node):
                place2d_texture = cmds.shadingNode(
                    "place2dTexture", asUtility=True, name=place2d_node
                )
            else:
                place2d_texture = place2d_node

            cmds.setAttr(f"{file_texture}.fileTextureName", texture_path, type="string")

            if not cmds.isConnected(
                f"{file_texture}.outColor", f"{material}.baseColor"
            ):
                cmds.connectAttr(
                    f"{file_texture}.outColor", f"{material}.baseColor", force=True
                )

            cmds.connectAttr(
                f"{place2d_texture}.outUV", f"{file_texture}.uvCoord", force=True
            )
            cmds.connectAttr(
                f"{place2d_texture}.outUvFilterSize",
                f"{file_texture}.uvFilterSize",
                force=True,
            )
            cmds.setAttr(f"{material}.specularRoughness", 0.75)

            logger.debug(f"Texture re-linked: {texture_path} to {mesh}")
        else:
            logger.debug(
                f"Texture file missing for {mesh}, skipping texture assignment."
            )

    logger.info("Meshes imported and textures re-linked.")

    import_skin_weights()


# ------------------------------
# Skin Weight Functions
# ------------------------------
def export_skin_weights():
    """Exports skin weights of selected meshes to a JSON file, keeping only the 4 highest influences per vertex."""
    os.makedirs(Config.desktop_path, exist_ok=True)  # Ensure the directory exists

    weights_data = {}  # Store weights for all selected meshes

    selected_meshes = cmds.ls(selection=True, type="transform")
    if not selected_meshes:
        logger.debug("No meshes selected!")
        return

    for mesh in selected_meshes:
        skin_clusters = cmds.ls(cmds.listHistory(mesh), type="skinCluster")
        if not skin_clusters:
            logger.warning(f"No skinCluster found for {mesh}, skipping weight export.")
            continue

        skin_cluster = skin_clusters[0]  # Get the first skinCluster found
        influences = cmds.skinCluster(
            skin_cluster, query=True, influence=True
        )  # Get all joints affecting mesh
        vertex_count = cmds.polyEvaluate(mesh, vertex=True)  # Number of vertices

        mesh_weights = {}  # Store vertex weights

        for i in range(vertex_count):
            vertex = f"{mesh}.vtx[{i}]"  # Construct vertex name
            weights = cmds.skinPercent(
                skin_cluster, vertex, query=True, value=True
            )  # Get joint weights

            # Filter only the highest 4 influences per vertex
            top_influences = heapq.nlargest(
                4, zip(influences, weights), key=lambda x: x[1]
            )

            # Remove zero-weight influences
            filtered_weights = {
                joint: weight for joint, weight in top_influences if weight > 0
            }

            if filtered_weights:
                mesh_weights[i] = filtered_weights  # Store weights per vertex

        # Store weights for this mesh
        weights_data[mesh] = mesh_weights

    # Save weight data to JSON
    weights_file = os.path.join(Config.desktop_path, "skin_weights.json")
    with open(weights_file, "w") as file:
        json.dump(weights_data, file, indent=4)

    logger.info(f"✅ Skin weights exported to {weights_file}")


def import_skin_weights():
    """Reads the skin weights JSON and applies them to imported meshes manually."""
    weights_file = os.path.join(Config.desktop_path, "skin_weights.json")

    if not os.path.exists(weights_file):
        logger.error("No mesh_weights.json file found. Cannot import weights.")
        return

    with open(weights_file, "r") as file:
        mesh_weights = json.load(file)  # Read weight data from file

    selected_meshes = cmds.ls(selection=True, type="transform")
    if not selected_meshes:
        logger.warning("No meshes selected. Attempting to apply to all stored meshes.")
        selected_meshes = list(
            mesh_weights.keys()
        )  # Use all meshes from JSON if none are selected

    for mesh in selected_meshes:
        if mesh not in mesh_weights:
            logger.warning(f"No weight data found for {mesh}, skipping import.")
            continue

        logger.debug(f"🔄 Importing weights for: {mesh}")

        # **Unlock transformations to prevent errors**
        for attr in [
            "translateX",
            "translateY",
            "translateZ",
            "rotateX",
            "rotateY",
            "rotateZ",
            "scaleX",
            "scaleY",
            "scaleZ",
        ]:
            if cmds.attributeQuery(attr, node=mesh, exists=True) and cmds.getAttr(
                f"{mesh}.{attr}", lock=True
            ):
                cmds.setAttr(f"{mesh}.{attr}", lock=False)
                logger.debug(f"🔓 Unlocked {attr} on {mesh}")

        # **Find or create a skinCluster for the mesh**
        skin_clusters = cmds.ls(cmds.listHistory(mesh), type="skinCluster")
        if not skin_clusters:
            logger.info(
                f"No skinCluster found on {mesh}, binding joints before importing weights."
            )

            # Get all joints listed in the stored weight data
            all_joints = set()
            for vertex_data in mesh_weights[mesh].values():
                all_joints.update(
                    vertex_data.keys()
                )  # Collect all joints affecting any vertex

            all_joints = list(
                filter(cmds.objExists, all_joints)
            )  # Ensure joints exist in the scene
            if not all_joints:
                logger.error(
                    f"No valid joints found for {mesh}. Skipping weight import."
                )
                continue

            # Create a new skinCluster with the correct joints
            skin_cluster = cmds.skinCluster(
                all_joints, mesh, toSelectedBones=True, normalizeWeights=1
            )[0]
        else:
            skin_cluster = skin_clusters[0]

        # **Apply stored weights per vertex**
        for vertex_index, influences in mesh_weights[mesh].items():
            vertex = f"{mesh}.vtx[{vertex_index}]"

            # **Filter out missing joints**
            valid_influences = {
                joint: weight
                for joint, weight in influences.items()
                if cmds.objExists(joint)
            }

            # **Apply weights using skinPercent**
            if valid_influences:
                cmds.skinPercent(
                    skin_cluster, vertex, transformValue=list(valid_influences.items())
                )

        logger.info(f"✅ Successfully imported weights for {mesh}")


# ------------------------------
# Bone Functions
# ------------------------------
def create_bones():
    """Creates bones from stored skeleton data with correct orientation."""
    if not Config.desktop_path:
        logger.debug("No file found")
        return

    file_path = os.path.join(Config.desktop_path, "skeleton.json")

    if not os.path.exists(file_path):
        logger.debug("No skeleton.json file found in the selected directory!")
        return

    with open(file_path, "r") as file:
        bone_data = json.load(file)

    created_bones = {}

    # Step 1: Create bones without parenting
    for bone, data in bone_data.items():
        new_bone = cmds.createNode("joint", name=bone)

        # Set bone position
        cmds.xform(new_bone, ws=True, translation=data["position"])

        # Ensure correct joint orientation
        if data["orientation"]:
            cmds.setAttr(f"{new_bone}.jointOrientX", data["orientation"][0])
            cmds.setAttr(f"{new_bone}.jointOrientY", data["orientation"][1])
            cmds.setAttr(f"{new_bone}.jointOrientZ", data["orientation"][2])

        # Set bone radius
        cmds.setAttr(f"{new_bone}.radius", data["radius"])

        created_bones[bone] = new_bone

    # Step 2: Parent bones in correct hierarchy
    for bone, data in bone_data.items():
        if data["parent"] and data["parent"] in created_bones:
            cmds.parent(created_bones[bone], created_bones[data["parent"]])

    logger.info("✅ Bones recreated with correct hierarchy and orientations.")


def run(path, operation):
    logger.debug(f"Operation: {operation}")
    logger.debug(f"Path argument: {path}")

    # Update paths to make sure we have current file info
    Config.update_paths()
    logger.debug(f"Config.filepath: {Config.filepath}")
    logger.debug(f"Config.raw_name: {Config.raw_name}")

    # Check if we have a saved file
    if not Config.filepath or Config.filepath == "":
        cmds.warning("Please save your Maya file before compiling/decompiling.")
        return

    # If user provided a path, use that instead of the default
    if path and path.strip():
        Config.desktop_path = path.strip()
    else:
        # Default path based on filename
        Config.desktop_path = os.path.join("C:\\", f"{Config.raw_name}")

    logger.debug(f"Using output path: {Config.desktop_path}")

    # Make sure the directory exists
    try:
        os.makedirs(Config.desktop_path, exist_ok=True)
        logger.debug(f"Created/verified directory: {Config.desktop_path}")
    except Exception as e:
        cmds.warning(f"Error creating directory: {e}")
        return

    # Now run the requested operation
    if operation == "decompile":
        export_selected_meshes()
        export_skin_weights()
        write_bone_data()
    elif operation == "compile":
        create_bones()
        import_meshes_and_weights()
    else:
        cmds.warning(f"Unknown operation: {operation}")
