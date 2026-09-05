"""One entry point for animation export flattening.

The anim folder grew three tools that do the same job by different discovery
methods; this picks the right one by parameter instead of by memory:

  namespace  -> Anim Export Prep: merge one namespace, import references
  rig        -> Anim Exporter: UI that finds *_rig transforms
  layers     -> Export Animation Prep: select via SKL_lyr / GEO_lyr
"""
import logging

import maya.cmds as mc

from modules.rig.Lib import scene_meta
from modules.anim import anim_export_prep
from modules.anim import anim_exporter
from modules.anim import export_animation_prep

logger = logging.getLogger(__name__)

TOOL_META = {
    "order": 4,
    "description": (
        "Flatten the scene for animation export, one tool, three methods.\n\n"
        "namespace: merge the given namespace into root and import every "
        "loaded reference (needs the namespace name).\n"
        "rig: opens the Anim Exporter UI, which finds *_rig transforms.\n"
        "layers: cleans namespaces and selects everything in SKL_lyr and "
        "GEO_lyr.\n\n"
        "Run AFTER animation is final; export with Character Rig Handler."
    ),
    "params": {
        "method": {
            "label": "method",
            "choices": ["namespace", "rig", "layers"],
            "tooltip": "How to find what to flatten (see description).",
        },
        "namespace": {
            "label": "namespace",
            "choices_fn": "list_namespaces",
            "editable": True,
            "tooltip": "Scene namespaces (namespace method only). "
                       "Re-select the tool to refresh the list.",
        },
    },
}


def list_namespaces():
    """Non-default namespaces in the scene, for the UI dropdown."""
    return [ns for ns in (mc.namespaceInfo(listOnlyNamespaces=True) or [])
            if ns not in ("UI", "shared")]


def main(method="namespace", namespace="", *args):
    method = (method or "namespace").lower()
    if method == "namespace":
        if not namespace:
            mc.warning("The namespace method needs the namespace parameter.")
            return None
        result = anim_export_prep.main(namespace)
        scene_meta.record("flatten", info={"method": method, "namespace": namespace})
        return result
    if method == "rig":
        return anim_exporter.main()
    if method == "layers":
        result = export_animation_prep.main()
        scene_meta.record("flatten", info={"method": method})
        return result
    mc.warning("Unknown method: {}".format(method))
    return None
