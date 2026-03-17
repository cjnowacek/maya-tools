from maya import cmds as mc
from maya import mel as mel

def main(sphere_name="default_sphere", *args):
    MeshOps_createSphere(sphere_name)

class MeshOps_createSphere(object):
    def __init__(self, name):
        self.create_sphere(name)

    def create_sphere(self, name):
        # Check if an object with the given name already exists
        if mc.objExists(name):
            mc.warning(f"A sphere with the name '{name}' already exists.")
        else:
            # Create the sphere with the specified name
            mel.eval(f'polySphere -r 1 -sx 20 -sy 20 -ax 0 1 0 -cuv 2 -ch 1 -name "{name}";')

# Example of how you would call this function from your script launcher:
# main("my_custom_sphere")
