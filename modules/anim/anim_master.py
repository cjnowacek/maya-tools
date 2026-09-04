"""Animator macros, embedded in the toolset as a button panel.

The actions are plain module functions; build_ui() presents them as a Qt
panel inside the main toolset window (tier 3 of the tool contract), so no
separate window opens. Import the functions directly for shelf buttons.
"""
import logging

import maya.cmds as mc
import maya.mel as mel

try:
    from PySide6 import QtWidgets  # Maya 2025+
except ImportError:
    from PySide2 import QtWidgets  # Maya 2024 and earlier

logger = logging.getLogger(__name__)

TOOL_META = {
    "description": (
        "Animator macro palette, embedded below.\n\n"
        "General: reset the selected controls' TRS, make only curves "
        "selectable, drop a locator matched to the selection.\n"
        "Timeline keys: cut at the current frame, add/remove an inbetween.\n"
        "Graph Editor: cut selected keys, cycle pre/post infinity.\n"
        "Manipulator: world or object space.\n\n"
        "The Run button does nothing here; every action is its own button."
    ),
}


# ------------------------------------------------------------------ actions
def reset_controls():
    """Zero TRS (scale to 1) on every selected control, skipping locked attrs."""
    mel.eval("""string $ctrlName[] = `ls -sl`;
        for ($con in $ctrlName){
        catchQuiet(`setAttr ($con + ".translateX") 0`);
        catchQuiet(`setAttr ($con + ".translateY") 0`);
        catchQuiet(`setAttr ($con + ".translateZ") 0`);
        catchQuiet(`setAttr ($con + ".rotateX") 0`);
        catchQuiet(`setAttr ($con + ".rotateY") 0`);
        catchQuiet(`setAttr ($con + ".rotateZ") 0`);
        catchQuiet(`setAttr ($con + ".scaleX") 1`);
        catchQuiet(`setAttr ($con + ".scaleY") 1`);
        catchQuiet(`setAttr ($con + ".scaleZ") 1`);
        }
        """)


def select_only_curves():
    """Limit viewport picking to curves (control shapes)."""
    mc.select(clear=True)
    mel.eval('setObjectPickMask "All" 0;')
    mel.eval('setObjectPickMask "Curve" true;')


def create_loc_at():
    """Locator matched to the first selected object's transform."""
    sel = mc.ls(sl=True)
    if not sel:
        mc.warning("Select an object to place a locator at.")
        return
    loc = mc.spaceLocator()[0]
    mc.select([loc, sel[0]])
    mel.eval("MatchTransform;")


def cut_keys_timeline():
    mel.eval("timeSliderCutKey;")


def add_inbetween():
    mel.eval("timeSliderEditKeys addInbetween;")


def remove_inbetween():
    mel.eval("timeSliderEditKeys removeInbetween;")


def cut_keys_graph():
    mel.eval("cutKey;")


def loop_visualize():
    """Cycle pre/post infinity on the graph editor's curves."""
    mel.eval("setInfinity -pri cycle graphEditor1FromOutliner;")
    mel.eval("setInfinity -poi cycle graphEditor1FromOutliner;")


def obj_space():
    mel.eval("manipMoveContext -edit -mode 0 Move;")
    mel.eval("manipRotateContext -e -mode 0 Rotate;")


def wld_space():
    mel.eval("manipMoveContext -edit -mode 2 Move;")
    mel.eval("manipRotateContext -e -mode 1 Rotate;")


# ---------------------------------------------------------------------- ui
_GROUPS = [
    ("General", [("Reset Controls", reset_controls),
                 ("Select Only Curves", select_only_curves),
                 ("Locator At Selection", create_loc_at)]),
    ("Timeline Keys", [("Cut", cut_keys_timeline),
                       ("+ Inbetween", add_inbetween),
                       ("- Inbetween", remove_inbetween)]),
    ("Graph Editor", [("Cut Keys", cut_keys_graph),
                      ("Visualize Loop", loop_visualize)]),
    ("Manipulator Space", [("World", wld_space),
                           ("Object", obj_space)]),
]


def build_ui(parent):
    """Toolset contract (tier 3): return the panel to embed on selection."""
    panel = QtWidgets.QWidget(parent)
    layout = QtWidgets.QVBoxLayout(panel)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(4)
    for title, actions in _GROUPS:
        box = QtWidgets.QGroupBox(title)
        box_layout = QtWidgets.QHBoxLayout(box)
        box_layout.setContentsMargins(6, 4, 6, 6)
        for label, fn in actions:
            btn = QtWidgets.QPushButton(label)
            btn.setMinimumHeight(26)
            btn.clicked.connect(lambda checked=False, f=fn: f())
            box_layout.addWidget(btn)
        # never let the group collapse to its title bar
        box.setSizePolicy(QtWidgets.QSizePolicy.Preferred,
                          QtWidgets.QSizePolicy.Fixed)
        layout.addWidget(box)
    panel.setSizePolicy(QtWidgets.QSizePolicy.Preferred,
                        QtWidgets.QSizePolicy.Minimum)
    return panel


def main(*args):
    """Every action is a button in the embedded panel; Run has nothing to do."""
    logger.info("Anim Master's actions are the buttons in the embedded panel.")
    return None
