import os
from maya import cmds as mc

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
    descendants = mc.listRelatives(meshSelected, allDescendents=True)
    printed_skin_clusters = set()

    print('\n|-------------------------------------------------------------------------------------------|')
    print('-----------------------------------Always Deform Readout------------------------------------')
    print('|-------------------------------------------------------------------------------------------|\n')

    for obj in descendants:
        print('\n|-------------------------------------------------------------------------------------------|')
        if mc.objectType(obj) == 'mesh':
            print(f'mesh FOUND! -> {obj}')
            meshConnections = mc.listConnections(obj, type='skinCluster')
            for skin_cluster in meshConnections:
                if skin_cluster not in printed_skin_clusters:
                    print(f'\nskinCluster FOUND! -> {skin_cluster}')
                    printed_skin_clusters.add(skin_cluster)
                jointConnections = mc.listConnections(skin_cluster, type='joint')
                for joint in jointConnections:
                    if mc.objectType(joint) == 'joint':
                        jointList.append(joint)
        else:
            print('NO MESH FOUND!')
        print('|-------------------------------------------------------------------------------------------|\n')

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
                export_name = f'{meshSelected[0]}_skinWeights.json'
                print(directorySourceimagesTmp)
                mc.deformerWeights(export_name, ex=True, df=skin_cluster, fm="JSON", p=directorySourceimagesTmp)
                mc.skinCluster(skin_cluster, edit=True, unbind=True)

                new_SC = mc.skinCluster(joint_names, meshSelected[0],
                                        n=meshSelected[0] + '_SC',
                                        toSelectedBones=True, bindMethod=0,
                                        maximumInfluences=4,
                                        skinMethod=0, normalizeWeights=1)

                mc.deformerWeights(export_name, im=True, method="index", deformer=new_SC[0], p=directorySourceimagesTmp)
        else:
            print("No skin clusters provided to select.")
    else:
        print("No valid scene file found.")


def run():
    """Main function to run the skin cluster export and reset."""
    global meshSelected, file_path, directory, directorySourceimages, directorySourceimagesTmp
    global jointList, unique_names

    jointList = []
    unique_names = []
    meshSelected = mc.ls(sl=1)

    file_path = mc.file(query=True, sceneName=True)
    directory = os.path.dirname(file_path)
    directorySourceimages = directory.replace('scenes', 'sourceimages')
    directorySourceimagesTmp = directory.replace('scenes', 'sourceimages/tmp')

    joint_names, skin_clusters = GetBoneNames()

    if meshSelected:
        print(f'FULL JOINT LIST for mesh -> {meshSelected[0]}')
    else:
        print('No mesh selected.')

    if joint_names:
        print(f'UNIQUE JOINT NAMES -> {joint_names}')
    else:
        print('No unique joints found.')

    if skin_clusters:
        print(f'SKIN CLUSTERS FOUND -> {skin_clusters}')
    else:
        print('No skin clusters found.')

    ExportSkinCluster(skin_clusters, joint_names)


def main(*args):
    run()


if __name__ == "__main__":
    main()
