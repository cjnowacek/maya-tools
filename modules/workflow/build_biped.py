"""Build Biped: guides phase + skeleton phase in one tool.

Replaces Skeleton From Guides. Composite of: Build Locators, then the
guides-to-skeleton build (joints named {guide}_JNT, oriented, mirrored,
assembled: thighs under pelvis, clavicles under chest).

The action parameter defaults to auto: the TOOLSET_META scene node decides
which phase you are in. First run builds the guide locators; you place them;
the next run detects they exist and builds the skeleton.
"""
import logging

import maya.cmds as mc

from modules.rig.Lib import scene_meta
from modules.rig.Lib import build_locators
from modules.wip import rig_ops_mirror_joints

logger = logging.getLogger(__name__)

TOOL_META = {
    "order": 1,
    "description": (
        "Build a biped in two phases, one button.\n\n"
        "auto: the scene's meta node decides. No guides yet -> builds the "
        "guide locators (place them, then Run again). Guides placed -> "
        "builds the skeleton: joints at the guides named {guide}_JNT (the "
        "name the IKFK builders expect), oriented X-down-bone / Y-up with "
        "end joints zeroed, L_ chains mirrored to R_, thighs parented "
        "under the pelvis and clavicles under the chest, all under "
        "BN_Skeleton.\n\n"
        "Run BEFORE: Leg Setup Full / Arm IKFK / controls.\n"
        "Force a phase with the action dropdown."
    ),
    "params": {
        "action": {
            "label": "action",
            "choices": ["auto", "guides", "skeleton"],
            "tooltip": "auto: meta node picks the phase. Or force one.",
        },
        "mirror": {
            "label": "mirror L to R",
            "choices": [1, 0],
            "tooltip": "Skeleton phase: mirror every L_ chain to R_ across YZ.",
        },
        "guides_group": {
            "label": "guides group",
            "tooltip": "Top group holding the guide locator chains.",
        },
    },
}


def main(action="auto", mirror=1, guides_group="Guides", *args):
    action = (action or "auto").lower()
    mirror = bool(int(mirror))
    guides_group = guides_group or "Guides"

    if action == "guides":
        return build_guides_phase(guides_group)
    if action == "skeleton":
        return build_skeleton(mirror, guides_group)

    # auto: let the scene state route
    if scene_meta.done("skeleton"):
        return build_skeleton(mirror, guides_group)   # emits the redirect
    if scene_meta.find("guides", name_fallback=guides_group):
        return build_skeleton(mirror, guides_group)
    return build_guides_phase(guides_group)


def build_guides_phase(guides_group="Guides"):
    existing = scene_meta.find("guides", name_fallback=guides_group)
    if existing:
        mc.warning("Guides already exist ({}). Place them, then Run again "
                   "to build the skeleton.".format(existing))
        mc.select(existing)
        return existing
    made = build_locators.build_guides("L")
    mc.warning("Guides built. PLACE THEM to fit the character, then Run "
               "again (auto) to build the skeleton.")
    return made


def _chain_roots(guides_group):
    return mc.listRelatives(guides_group, children=True, fullPath=True) or []


def _build_joints(guide, parent_joint):
    """Recursively create a joint per guide locator, named {guide}_JNT."""
    short = guide.split("|")[-1]
    name = short + "_JNT"
    if mc.objExists(name):
        mc.warning("{} already exists; skipping this chain.".format(name))
        return None
    mc.select(clear=True)
    jnt = mc.joint(name=name, position=mc.xform(guide, q=True, ws=True, t=True))
    if parent_joint:
        mc.parent(jnt, parent_joint)
    for child in mc.listRelatives(guide, children=True, type="transform", fullPath=True) or []:
        if mc.listRelatives(child, shapes=True, type="locator"):
            _build_joints(child, jnt)
    return jnt


def _orient_chain(root):
    mc.select(root)
    mc.joint(edit=True, orientJoint="xyz", secondaryAxisOrient="yup",
             children=True, zeroScaleOrient=True)
    for jnt in mc.listRelatives(root, allDescendents=True, type="joint") or [root]:
        if not mc.listRelatives(jnt, children=True, type="joint"):
            mc.setAttr(jnt + ".jointOrient", 0, 0, 0)


def build_skeleton(mirror=True, guides_group="Guides"):
    if scene_meta.done("skeleton"):
        existing = scene_meta.find("skeleton", name_fallback="BN_Skeleton")
        _, nxt = scene_meta.next_step()
        mc.warning("Skeleton already built ({}). Next step: {}".format(
            existing, nxt or "see Scene Status"))
        if existing:
            mc.select(existing)
        return existing

    found = scene_meta.find("guides", name_fallback=guides_group)
    if not found:
        mc.warning("No '{}' group found. Run the guides phase first "
                   "(action: guides, or just auto).".format(guides_group))
        return None
    guides_group = found

    roots = []
    for guide_root in _chain_roots(guides_group):
        jnt_root = _build_joints(guide_root, None)
        if jnt_root:
            _orient_chain(jnt_root)
            roots.append(jnt_root)

    if mirror:
        mirrored = []
        for root in list(roots):
            if root.split("|")[-1].startswith("L_"):
                mc.select(root)
                new = rig_ops_mirror_joints.mirror_joints("L_", "R_")
                if new:
                    mirrored += new
        roots += mirrored

    # assembly: thighs under pelvis, clavicles under chest
    top = "BN_Skeleton" if mc.objExists("BN_Skeleton") else mc.group(empty=True, name="BN_Skeleton")
    for root in roots:
        short = root.split("|")[-1]
        target = top
        if "Thigh" in short and mc.objExists("Pelvis_BN_JNT"):
            target = "Pelvis_BN_JNT"
        elif "Clavicle" in short and mc.objExists("Chest_BN_JNT"):
            target = "Chest_BN_JNT"
        if (mc.listRelatives(root, parent=True) or [None])[0] != target:
            try:
                mc.parent(root, target)
            except RuntimeError:
                pass
    for spine_root in ("Pelvis_BN_JNT",):
        if mc.objExists(spine_root) and not mc.listRelatives(spine_root, parent=True):
            mc.parent(spine_root, top)

    mc.setAttr(guides_group + ".visibility", 0)
    scene_meta.record("skeleton", nodes=[top], info={"chains": len(roots)})
    mc.select(top)
    logger.info("Skeleton built under %s (%d chains)", top, len(roots))
    return top
