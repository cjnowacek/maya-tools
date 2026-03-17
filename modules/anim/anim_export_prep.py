import maya.cmds as cmds
import maya.mel as mel

def main(loader_input):
    BfaOps_AnimExportPrep(loader_input)

def BfaOps_AnimExportPrep(loader_input):
    """Prepares the animation for export by merging namespaces and importing references.

    Args:
        loader_input (str): A string passed from the loader script to specify the namespace or other identifiers.
    """

    # Merge namespace with root and remove the specified namespace
    namespace = loader_input
    mel_command = f'namespace -mergeNamespaceWithRoot -removeNamespace "{namespace}";'
    mel.eval(mel_command)

    # Get all top-level references in the scene
    all_ref_paths = cmds.file(q=True, reference=True) or []

    for ref_path in all_ref_paths:
        # Import the reference if it's loaded
        if cmds.referenceQuery(ref_path, isLoaded=True):
            cmds.file(ref_path, importReference=True)

            # Collect any new top-level references from nested references
            new_ref_paths = cmds.file(q=True, reference=True)
            if new_ref_paths:
                for new_ref_path in new_ref_paths:
                    if new_ref_path not in all_ref_paths:
                        all_ref_paths.append(new_ref_path)

    # Parenting operations for 'SKL' and 'GEO' objects
    if cmds.objExists("SKL"):
        cmds.select("SKL")
        skl_children = cmds.pickWalk(direction="down")
        cmds.parent(skl_children, world=True)

    if cmds.objExists("GEO"):
        cmds.select("GEO")
        geo_children = cmds.listRelatives(children=True)
        cmds.parent(geo_children, world=True)

    # Select the 'Root' object and its hierarchy
    if cmds.objExists("Root"):
        cmds.select("Root", hierarchy=True)

# Example usage from another script
if __name__ == "__main__":
    # This is where you'd call the main function with a string from the loader script
    loader_input = "SKL_robin"  # Example string input
    main(loader_input)
