"""Scene metadata node: lets the tools know what has been built.

One `network` node (TOOLSET_META) carries:
  * a JSON string attr recording which workflow steps ran, when, with info
  * one multi message attr per step, connected to the nodes that step built

Message connections are the point: they survive renames and reparenting,
so tools can find "the skeleton root" without guessing at names. Name-based
lookups stay as fallback for scenes built before the meta node existed.

    from modules.rig.Lib import scene_meta
    scene_meta.record("skeleton", nodes=[root], info={"chains": 3})
    scene_meta.done("skeleton")        -> True
    scene_meta.linked("skeleton")      -> ["BN_Skeleton"]
    scene_meta.summary()               -> ordered status report string
"""
import json
import logging
from datetime import datetime

import maya.cmds as mc

logger = logging.getLogger(__name__)

NODE = "TOOLSET_META"
DATA_ATTR = "toolsetData"

# canonical order, used by summary() to suggest the next step
STEP_ORDER = [
    ("guides", "Build Biped (guides phase; place them!)"),
    ("skeleton", "Build Biped (skeleton phase)"),
    ("leg_L", "Leg Setup Full (L)"),
    ("leg_R", "Leg Setup Full (R)"),
    ("arm_L", "Arm IKFK Switch (L)"),
    ("arm_R", "Arm IKFK Switch (R)"),
    ("controls", "FK Controls Finish"),
    ("skin", "bind + Skin Painter + Always Deform"),
    ("flatten", "Anim Flatten (animation scenes)"),
]

# step -> (tab name, tool module, param presets); the adaptive Workflow tab
# uses this to jump to the right builder with the right values filled in
STEP_TOOLS = {
    "guides": ("Workflow", "build_biped", {"action": "guides"}),
    "skeleton": ("Workflow", "build_biped", {"action": "skeleton"}),
    "leg_L": ("Workflow", "leg_setup_full", {"side": "L"}),
    "leg_R": ("Workflow", "leg_setup_full", {"side": "R"}),
    "arm_L": ("Manual", "rig_op_arm_ikfk_switch", {"side": "L"}),
    "arm_R": ("Manual", "rig_op_arm_ikfk_switch", {"side": "R"}),
    "controls": ("Workflow", "fk_controls_finish", {}),
    "skin": ("Rig", "always_deform", {}),
    "flatten": ("Workflow", "anim_flatten", {}),
}


def node(create=True):
    """The meta node's name, creating it on first use."""
    if mc.objExists(NODE):
        return NODE
    if not create:
        return None
    n = mc.createNode("network", name=NODE, skipSelect=True)
    mc.addAttr(n, longName=DATA_ATTR, dataType="string")
    mc.setAttr(n + "." + DATA_ATTR, "{}", type="string")
    logger.info("Created scene meta node %s", n)
    return n


def _load():
    n = node(create=False)
    if not n:
        return {}
    try:
        return json.loads(mc.getAttr(n + "." + DATA_ATTR) or "{}")
    except (ValueError, RuntimeError):
        logger.warning("Corrupt %s data; starting fresh", NODE, exc_info=True)
        return {}


def _save(data):
    mc.setAttr(node() + "." + DATA_ATTR, json.dumps(data, indent=0), type="string")


def record(step, nodes=None, info=None):
    """Mark a step done: timestamp + info in the JSON, message links to nodes."""
    data = _load()
    data[step] = {"time": datetime.now().isoformat(timespec="seconds"),
                  "info": info or {}}
    _save(data)
    attr = "link_" + step
    n = node()
    if not mc.attributeQuery(attr, node=n, exists=True):
        mc.addAttr(n, longName=attr, attributeType="message", multi=True)
    for i, built in enumerate(nodes or []):
        if not mc.objExists(built):
            continue
        try:
            mc.connectAttr(built + ".message", "{}.{}[{}]".format(n, attr, i),
                           force=True)
        except RuntimeError:
            logger.debug("could not link %s to %s", built, attr, exc_info=True)
    logger.info("Recorded step %r (%d linked nodes)", step, len(nodes or []))


def done(step):
    return step in _load()


def info(step):
    return _load().get(step)


def linked(step):
    """Nodes a step registered, found through message connections (rename-proof)."""
    n = node(create=False)
    attr = "link_" + step
    if not n or not mc.attributeQuery(attr, node=n, exists=True):
        return []
    return mc.listConnections("{}.{}".format(n, attr)) or []


def find(step, name_fallback=None):
    """First linked node for a step, else the name fallback if it exists."""
    hits = linked(step)
    if hits:
        return hits[0]
    if name_fallback and mc.objExists(name_fallback):
        return name_fallback
    return None


def label(step):
    """Human name of a step's builder tool."""
    return dict(STEP_ORDER).get(step, step)


def next_step():
    """(step, builder label) of the first canonical step not yet done."""
    data = _load()
    for step, lbl in STEP_ORDER:
        if step not in data:
            return step, lbl
    return None, None


def summary():
    """Ordered report: what ran (when, where), what has not, what's next."""
    data = _load()
    lines = []
    next_step = None
    for step, label in STEP_ORDER:
        if step in data:
            entry = data[step]
            nodes_ = linked(step)
            lines.append("[done] {:<10} {}  ({}){}".format(
                step, entry.get("time", "?"), label,
                "  -> " + ", ".join(nodes_) if nodes_ else ""))
        else:
            lines.append("[    ] {:<10} {}".format(step, label))
            if next_step is None:
                next_step = label
    extras = [s for s in data if s not in dict(STEP_ORDER)]
    for step in extras:
        lines.append("[done] {:<10} {}".format(step, data[step].get("time", "?")))
    if next_step:
        lines.append("")
        lines.append("Next: " + next_step)
    return "\n".join(lines)
