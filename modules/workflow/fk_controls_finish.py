"""FK controls + side colors in one run.

Composite of: Rig Ops Create Controls, then Rig Ops Create Control Colors on
the controls it just made. Select only the chain ROOT; the chain is expanded
top-down automatically.
"""
import logging

import maya.cmds as mc

from modules.rig.Lib import scene_meta
from modules.wip import rig_ops_create_controls
from modules.wip import rig_ops_create_control_colors

logger = logging.getLogger(__name__)

TOOL_META = {
    "order": 3,
    "description": (
        "Build an FK control chain and color it, from one selected root.\n\n"
        "Expands the selected joint to its full chain (top-down), builds "
        "the CON + zeroed GRP chain (Rig Ops Create Controls), then colors "
        "the new controls by side: L_ blue, R_ red, center yellow.\n\n"
        "Run AFTER: the skeleton (and any IKFK setups) exist.\n"
        "Select: the chain's root joint only."
    ),
    "params": {
        "name_token": {
            "label": "name token",
            "tooltip": "Joint-name token replaced to name controls (JNT -> CON/GRP).",
        },
    },
}


def main(name_token="JNT", *args):
    return build_fk_controls(name_token or "JNT")


def build_fk_controls(name_token="JNT"):
    sel = mc.ls(sl=True, type="joint")
    if not sel:
        if not scene_meta.done("skeleton"):
            mc.warning("Nothing selected and no skeleton recorded. Redirect: "
                       "run '{}' first.".format(scene_meta.label("skeleton")))
        else:
            mc.warning("Select the chain's root joint.")
        return None

    # expand root -> ordered chain, top-down
    chain = [sel[0]]
    while True:
        kids = mc.listRelatives(chain[-1], children=True, type="joint") or []
        if len(kids) != 1:
            break
        chain.append(kids[0])
    mc.select(chain)

    controls = rig_ops_create_controls.create_fk_controls(name_token)
    if not controls:
        return None
    mc.select(controls)
    rig_ops_create_control_colors.set_control_colors(0)
    scene_meta.record("controls", nodes=controls[:1],
                      info={"count": len(controls), "root": chain[0]})
    mc.select(controls)
    logger.info("FK chain finished: %d controls", len(controls))
    return controls
