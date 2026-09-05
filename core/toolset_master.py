# toolset_master.py
"""
Main UI module for Maya rigging tools.

A dockable UI for Autodesk Maya designed to streamline rigging workflows.
This script provides a framework for accessing various toolsets for creating,
orienting, and visualizing joint structures, batch renaming, and additional utility widgets.

Features:
    - Enables access to a variety of rigging tools through a tabbed interface
    - Dynamically loads available scripts from configured directories
    - Seamlessly integrates into Maya's workspace as a dockable interface

Author: CJ Nowacek
Version: 2.0.0
License: GPL
"""

import ast
import os
import sys
import inspect
import importlib
import logging
from typing import Dict, List, Optional

try:
    from PySide6 import QtCore, QtWidgets  # Maya 2025+
    from shiboken6 import wrapInstance, isValid as _wrapper_is_valid
except ImportError:
    from PySide2 import QtCore, QtWidgets  # Maya 2024 and earlier
    from shiboken2 import wrapInstance, isValid as _wrapper_is_valid

from maya import cmds
from maya import OpenMayaUI
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

from core.Config import Config

logger = logging.getLogger(__name__)

TOOL_DISPLAY_NAME = "CJ's Maya Tools"


def get_maya_main_window() -> QtWidgets.QWidget:
    main_window_ptr = OpenMayaUI.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)


def format_display_name(module_name: str) -> str:
    return module_name.replace("_", " ").title()


def _tool_order(script_path: str, module_name: str):
    """TOOL_META['order'] read via ast (no import, no side effects)."""
    try:
        with open(os.path.join(script_path, module_name + ".py"),
                  encoding="utf-8") as f:
            tree = ast.parse(f.read())
        for node in tree.body:
            if (isinstance(node, ast.Assign)
                    and getattr(node.targets[0], "id", "") == "TOOL_META"):
                return ast.literal_eval(node.value).get("order")
    except Exception:
        logger.debug("order unreadable for %s", module_name, exc_info=True)
    return None


def list_modules(script_path: str) -> List[str]:
    """Tool modules in a category directory.

    Sorted by TOOL_META['order'] where declared (pipeline sequence, e.g.
    the Workflow tab), alphabetically otherwise; unordered tools list after
    ordered ones.
    """
    if not os.path.exists(script_path):
        cmds.warning(f"Path does not exist: {script_path}")
        return []

    module_names = []
    for file in os.listdir(script_path):
        if file.endswith(".py") and not file.startswith("__"):
            module_names.append(file.split(".")[0])

    def key(name):
        order = _tool_order(script_path, name)
        return (order if order is not None else 10 ** 6, name)

    return sorted(module_names, key=key)


class _CurrentPageTabWidget(QtWidgets.QTabWidget):
    """A QTabWidget that sizes to the CURRENT page only.

    Stock QTabWidget reports the height of its tallest page (the inner
    QStackedWidget takes the max of every page's sizeHint), so a tall tool on
    a background tab pads the window forever. Overriding the hints to follow
    the current page is the only reliable fix; size policies and
    maximumHeight on hidden pages do not affect QTabWidget's own hint.
    """

    def _hint(self, base):
        page = self.currentWidget()
        if page is None:
            return base
        bar = self.tabBar().sizeHint()
        ph = page.sizeHint()
        # width from the widest page (stable tabs), height from the current one
        return QtCore.QSize(max(base.width(), ph.width()),
                            ph.height() + bar.height() + 8)

    def sizeHint(self):
        return self._hint(super().sizeHint())

    def minimumSizeHint(self):
        page = self.currentWidget()
        if page is None:
            return super().minimumSizeHint()
        bar = self.tabBar().minimumSizeHint()
        return QtCore.QSize(super().minimumSizeHint().width(),
                            page.minimumSizeHint().height() + bar.height() + 8)


class ToolsetTab(QtWidgets.QWidget):
    """
    Tab widget for each tool category. Dynamically renders parameter inputs
    based on the selected script's main() signature.
    """

    def __init__(self, script_path: str, parent: Optional[QtWidgets.QWidget] = None):
        super(ToolsetTab, self).__init__(parent)
        self.script_path = script_path
        self.param_widgets: Dict[str, QtWidgets.QWidget] = {}

        self.script_combobox = QtWidgets.QComboBox()
        self.run_button = QtWidgets.QPushButton("Run")

        # Tool description, always visible
        self.desc_label = QtWidgets.QLabel("No description available.")
        self.desc_label.setWordWrap(True)
        self.desc_label.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        self.desc_label.setStyleSheet(
            "QLabel { background: rgba(0, 0, 0, 40); border-radius: 3px; padding: 6px; }"
        )

        # Generic fallback input (shown when main has no named params)
        self.generic_label = QtWidgets.QLabel("Parameters:")
        self.generic_input = QtWidgets.QLineEdit("")
        self.generic_input.setPlaceholderText("Optional parameters")

        # Custom per-tool panel (tier 3: module-level build_ui(parent))
        self.custom_container = QtWidgets.QWidget()
        self.custom_layout = QtWidgets.QVBoxLayout(self.custom_container)
        self.custom_layout.setContentsMargins(0, 0, 0, 0)
        self.custom_widget: Optional[QtWidgets.QWidget] = None

        # Dynamic per-parameter inputs
        self.params_container = QtWidgets.QWidget()
        self.params_form = QtWidgets.QFormLayout(self.params_container)
        self.params_form.setContentsMargins(0, 0, 0, 0)

        generic_row = QtWidgets.QHBoxLayout()
        generic_row.addWidget(self.generic_label)
        generic_row.addWidget(self.generic_input)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(QtWidgets.QLabel("Select Script:"))
        layout.addWidget(self.script_combobox)
        layout.addWidget(self.desc_label)
        layout.addWidget(self.custom_container)
        layout.addWidget(self.params_container)
        layout.addLayout(generic_row)
        layout.addWidget(self.run_button)
        layout.setAlignment(QtCore.Qt.AlignTop)

        self.script_combobox.currentIndexChanged.connect(self._on_script_changed)

    def _resize_to_fit(self) -> None:
        """Keep the window tight: shrink to content, stretch only when the
        description or parameter fields need the space.

        Three window situations, three behaviors:
          * plain ToolsetMaster dialog       -> Qt adjustSize
          * floating workspaceControl        -> cmds.workspaceControl
            resizeHeight (Qt adjustSize on the wrapper collapses the content
            to its minimum hint, so the resize must go through Maya)
          * docked in Maya's main window     -> leave alone (Maya's dock
            splitters own the geometry; adjustSize there resizes ALL of Maya)
        """
        # two passes: immediately after the event loop settles, and once more
        # shortly after, because a freshly embedded panel's sizeHint can grow
        # when styles/polish land a tick later
        QtCore.QTimer.singleShot(0, self._apply_resize)
        QtCore.QTimer.singleShot(120, self._apply_resize)

    def _apply_resize(self) -> None:
        win = self.window()
        if win is None:
            return
        if type(win).__name__ == "ToolsetMaster":
            win.adjustSize()
            return
        if win.objectName() == "MayaWindow":
            return
        try:
            # find the enclosing workspaceControl by walking up the parents
            ctrl = None
            w = self.parentWidget()
            while w is not None:
                name = w.objectName()
                if name and cmds.workspaceControl(name, q=True, exists=True):
                    ctrl = name
                    break
                w = w.parentWidget()
            if not ctrl or not cmds.workspaceControl(ctrl, q=True, floating=True):
                return
            # size to the ToolsetMaster content (title + tabs + this tab)
            owner = self.parentWidget()
            while owner is not None and type(owner).__name__ != "ToolsetMaster":
                owner = owner.parentWidget()
            target = owner or self
            # our tab widget overrides sizeHint; that does NOT invalidate the
            # parent's cached layout, so nudge it before measuring, or the
            # window keeps the previous (taller) tool's height
            tabw = getattr(owner, "tab_widget", None)
            if tabw is not None:
                tabw.updateGeometry()
            self.updateGeometry()
            # Measure the LAYOUT's sizeHint, not the widget's: the dockable
            # QDialog's own sizeHint() gets stuck at the tallest tool ever
            # shown (Maya's mixin overrides it), while the layout hint tracks
            # the current content live.
            if target.layout() is not None:
                target.layout().invalidate()
                target.layout().activate()
                height = target.layout().sizeHint().height() + 8
            else:
                height = target.sizeHint().height() + 8
            # a control whose height is fixed/preferred ignores resizeHeight
            try:
                cmds.workspaceControl(ctrl, e=True, heightProperty="free")
            except Exception:
                pass
            cmds.workspaceControl(ctrl, e=True, resizeHeight=height)
        except Exception:
            logger.debug("workspaceControl resize skipped", exc_info=True)

    def _set_description(self, text: Optional[str]) -> None:
        self.desc_label.setText(text or "No description available.")

    def _on_script_changed(self, index: int) -> None:
        module_name = self.script_combobox.itemData(index)
        self._refresh_params(module_name)

    def _refresh_params(self, script_name: str) -> None:
        """Inspect the selected module's main() and render per-parameter inputs."""
        # Clear dynamic fields
        while self.params_form.rowCount():
            self.params_form.removeRow(0)
        self.param_widgets.clear()
        if self.custom_widget is not None:
            self.custom_widget.setParent(None)
            self.custom_widget.deleteLater()
            self.custom_widget = None
            self.custom_container.setMinimumHeight(0)

        if not script_name or not self.script_path:
            self._set_description(None)
            self._show_generic(True)
            self._resize_to_fit()
            return

        try:
            if self.script_path not in sys.path:
                sys.path.append(self.script_path)

            if script_name in sys.modules:
                # Reload so edits to TOOL_META / docstrings / signatures show
                # up on selection, not only after a Run (which reloads too).
                try:
                    mod = importlib.reload(sys.modules[script_name])
                except Exception:
                    mod = sys.modules[script_name]
            else:
                mod = importlib.import_module(script_name)

            meta = getattr(mod, "TOOL_META", None) or {}
            doc = meta.get("description") or inspect.getdoc(mod)
            if not doc and hasattr(mod, "main"):
                doc = inspect.getdoc(mod.main)
            self._set_description(doc)

            # Tier 3: the tool supplies its own panel. The contract is
            # predictable: build_ui(parent) returns a QWidget, embedded here;
            # Run calls main(**ui_kwargs(widget)) if ui_kwargs exists, else
            # main(). No build_ui -> declarative TOOL_META fields as usual.
            if hasattr(mod, "build_ui"):
                try:
                    w = mod.build_ui(self.custom_container)
                except Exception:
                    logger.warning("build_ui failed for %r; falling back to "
                                   "declarative params", script_name, exc_info=True)
                    w = None
                if w is not None:
                    self.custom_layout.addWidget(w)
                    self.custom_widget = w
                    # reserve the panel's natural height so a deeply nested
                    # custom widget cannot be collapsed to nothing by the
                    # intermediate layouts (e.g. group boxes -> title only)
                    self.custom_container.setMinimumHeight(
                        w.sizeHint().height()
                    )
                    self._show_generic(False)
                    self._resize_to_fit()
                    return

            if not hasattr(mod, "main"):
                self._show_generic(False)
                return

            sig = inspect.signature(mod.main)
            named_params = [
                (name, param)
                for name, param in sig.parameters.items()
                if param.kind
                not in (
                    inspect.Parameter.VAR_POSITIONAL,
                    inspect.Parameter.VAR_KEYWORD,
                )
            ]

            if named_params:
                self._show_generic(False)
                param_meta = meta.get("params", {})
                group_forms = {}

                def form_for(pmeta):
                    group = pmeta.get("group")
                    if not group:
                        return self.params_form
                    if group not in group_forms:
                        box = QtWidgets.QGroupBox(group)
                        form = QtWidgets.QFormLayout(box)
                        form.setContentsMargins(8, 4, 8, 6)
                        self.params_form.addRow(box)
                        group_forms[group] = form
                    return group_forms[group]

                for name, param in named_params:
                    default = (
                        param.default
                        if param.default is not inspect.Parameter.empty
                        else None
                    )
                    pmeta = param_meta.get(name, {})
                    # dynamic choices: the module names a function that
                    # returns the options for THIS scene (e.g. namespaces)
                    fn = pmeta.get("choices_fn")
                    if fn and hasattr(mod, fn):
                        try:
                            choices = list(getattr(mod, fn)() or [])
                            if choices:
                                pmeta = dict(pmeta, choices=choices)
                        except Exception:
                            logger.warning("choices_fn %r failed for %r",
                                           fn, script_name, exc_info=True)
                    field = self._widget_for_default(default, pmeta)
                    label = pmeta.get("label", name) + ":"
                    if pmeta.get("tooltip"):
                        field.setToolTip(pmeta["tooltip"])
                    form_for(pmeta).addRow(label, field)
                    self.param_widgets[name] = field
            else:
                self._show_generic(True)

        except Exception:
            logger.warning("Could not inspect tool %r", script_name, exc_info=True)
            self._set_description(None)
            self._show_generic(True)

        self._resize_to_fit()

    @staticmethod
    def _widget_for_default(default, pmeta: Optional[dict] = None) -> QtWidgets.QWidget:
        """A typed input widget matched to the parameter's default value.

        ``pmeta`` (from the module's TOOL_META['params'][name]) can refine it:
        ``choices`` renders a dropdown, ``min``/``max`` clamp the spinboxes.
        """
        pmeta = pmeta or {}
        choices = pmeta.get("choices")
        if choices and pmeta.get("radio"):
            # mutually exclusive build choices: radio row
            container = QtWidgets.QWidget()
            row = QtWidgets.QHBoxLayout(container)
            row.setContentsMargins(0, 0, 0, 0)
            group = QtWidgets.QButtonGroup(container)
            container._radio_group = group
            for c in choices:
                btn = QtWidgets.QRadioButton(str(c))
                btn._value = c
                group.addButton(btn)
                row.addWidget(btn)
                if c == default:
                    btn.setChecked(True)
            row.addStretch()
            return container
        if choices:
            widget = QtWidgets.QComboBox()
            for c in choices:
                widget.addItem(str(c), c)
            if default is not None and default in choices:
                widget.setCurrentIndex(list(choices).index(default))
            if pmeta.get("editable"):
                widget.setEditable(True)
            return widget
        if isinstance(default, bool):
            widget = QtWidgets.QCheckBox()
            widget.setChecked(default)
        elif isinstance(default, int):
            widget = QtWidgets.QSpinBox()
            widget.setRange(int(pmeta.get("min", -1000000)), int(pmeta.get("max", 1000000)))
            widget.setValue(default)
        elif isinstance(default, float):
            widget = QtWidgets.QDoubleSpinBox()
            widget.setRange(
                float(pmeta.get("min", -1000000.0)), float(pmeta.get("max", 1000000.0))
            )
            widget.setDecimals(3)
            widget.setValue(default)
        else:
            widget = QtWidgets.QLineEdit()
            if default is not None:
                widget.setText(str(default))
        return widget

    def _show_generic(self, visible: bool) -> None:
        self.generic_label.setVisible(visible)
        self.generic_input.setVisible(visible)

    def apply_presets(self, presets: dict) -> None:
        """Fill the rendered param widgets with the given values."""
        for name, value in (presets or {}).items():
            widget = self.param_widgets.get(name)
            if widget is None:
                continue
            if hasattr(widget, "_radio_group"):
                for btn in widget._radio_group.buttons():
                    if btn._value == value:
                        btn.setChecked(True)
            elif isinstance(widget, QtWidgets.QComboBox):
                idx = widget.findData(value)
                if idx < 0:
                    idx = widget.findText(str(value))
                if idx >= 0:
                    widget.setCurrentIndex(idx)
                elif widget.isEditable():
                    widget.setEditText(str(value))
            elif isinstance(widget, QtWidgets.QCheckBox):
                widget.setChecked(bool(value))
            elif isinstance(widget, (QtWidgets.QSpinBox, QtWidgets.QDoubleSpinBox)):
                widget.setValue(value)
            else:
                widget.setText(str(value))

    def get_kwargs(self) -> dict:
        """Return named parameter values from the typed widgets."""
        result = {}
        for name, widget in self.param_widgets.items():
            if hasattr(widget, "_radio_group"):
                checked = widget._radio_group.checkedButton()
                result[name] = checked._value if checked else None
            elif isinstance(widget, QtWidgets.QComboBox):
                if widget.isEditable():
                    # typed text wins: currentData() keeps returning the last
                    # ITEM's data even after the user types something else
                    text = widget.currentText()
                    idx = widget.findText(text)
                    result[name] = widget.itemData(idx) if idx >= 0 else text
                else:
                    result[name] = widget.currentData()
            elif isinstance(widget, QtWidgets.QCheckBox):
                result[name] = widget.isChecked()
            elif isinstance(widget, (QtWidgets.QSpinBox, QtWidgets.QDoubleSpinBox)):
                result[name] = widget.value()
            else:
                text = widget.text()
                for cast in (int, float):
                    try:
                        text = cast(text)
                        break
                    except (ValueError, TypeError):
                        pass
                result[name] = text
        return result


class ToolsetMaster(MayaQWidgetDockableMixin, QtWidgets.QDialog):
    """
    Main dockable window containing the ToolsetMaster UI.
    Provides access to various tools through a tabbed interface.
    """

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
        parent = parent or get_maya_main_window()
        super(ToolsetMaster, self).__init__(parent)

        ui_config = Config.get_ui_config("toolset_master")
        self.setWindowTitle(TOOL_DISPLAY_NAME)
        self.setMinimumSize(ui_config.get("width", 400), ui_config.get("height", 125))

        if cmds.about(ntOS=True):
            self.setWindowFlags(
                self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint
            )
        elif cmds.about(macOS=True):
            self.setWindowFlags(QtCore.Qt.Tool)

        self.module_names = {}
        for category, path in Config.TOOL_PATHS.items():
            self.module_names[category] = list_modules(path)

        self.create_widgets()
        self.create_layout()
        self.create_connections()

    def create_widgets(self) -> None:
        # tab label -> tool category (folder key in Config.TOOL_PATHS);
        # "Manual" shows the wip folder: hand-run building blocks, several
        # of which are unfinished or destined to be wrapped into workflow
        # composites
        self.tab_categories = {
            "Workflow": "workflow",
            "Rig": "rig",
            "Anim": "anim",
            "Model": "model",
            "Scene": "scene",
            "Manual": "wip",
        }
        self.tabs = {}
        for label, category in self.tab_categories.items():
            path = Config.get_tool_path(category)
            self.tabs[label] = ToolsetTab(path)

        for label, tab in self.tabs.items():
            category = self.tab_categories[label]
            for module_name in self.module_names.get(category, []):
                tab.script_combobox.addItem(
                    format_display_name(module_name), module_name
                )

        self.tab_widget = _CurrentPageTabWidget()
        for name, tab in self.tabs.items():
            self.tab_widget.addTab(tab, name)
        # resize the window whenever the tab itself changes; the workflow
        # tab also re-reads the scene state whenever it is shown
        self.tab_widget.currentChanged.connect(self._on_tab_changed)

    def _on_tab_changed(self, index: int) -> None:
        self.tab_widget.widget(index)._resize_to_fit()

    def create_layout(self) -> None:
        main_layout = QtWidgets.QVBoxLayout(self)
        title_label = QtWidgets.QLabel(TOOL_DISPLAY_NAME)
        title_label.setAlignment(QtCore.Qt.AlignCenter)
        title_label.setStyleSheet("font-weight: bold; font-size: 13px; padding: 4px;")
        main_layout.addWidget(title_label)
        main_layout.addWidget(self.tab_widget)

    def create_connections(self) -> None:
        for label, tab in self.tabs.items():
            tab.run_button.clicked.connect(
                lambda checked=False, lbl=label: self.run_script(lbl)
            )

    def run_script(self, label: str) -> None:
        script_path = Config.get_tool_path(self.tab_categories[label])
        tab = self.tabs[label]
        selected_script = tab.script_combobox.currentData()

        if not selected_script:
            cmds.warning(f"No script selected in {category} tab")
            return

        if script_path not in sys.path:
            sys.path.append(script_path)

        try:
            if selected_script in sys.modules:
                importlib.reload(sys.modules[selected_script])
            else:
                importlib.import_module(selected_script)

            module = sys.modules[selected_script]

            if not hasattr(module, "main"):
                cmds.warning(f"No main() found in {selected_script}")
                return

            if tab.custom_widget is not None:
                if hasattr(module, "ui_kwargs"):
                    result = module.main(**module.ui_kwargs(tab.custom_widget))
                else:
                    result = module.main()
            elif tab.param_widgets:
                result = module.main(**tab.get_kwargs())
            else:
                user_input = tab.generic_input.text()
                result = module.main(user_input) if user_input else module.main()

            if result and hasattr(result, "show"):
                result.show()

        except ImportError as e:
            cmds.warning(f"Error importing {selected_script}: {e}")
        except Exception as e:
            cmds.warning(f"Error running {selected_script}: {e}")
            logger.error(f"[{selected_script}] {e}")


def show_ui() -> ToolsetMaster:
    try:
        # allWidgets(), not topLevelWidgets(): once shown, the dialog is
        # reparented INTO its workspaceControl and stops being top level,
        # so the old scan missed every live instance and left them behind
        for widget in QtWidgets.QApplication.allWidgets():
            try:
                # a wrapper whose C++ side died with its deleted
                # workspaceControl raises "Internal C++ object already
                # deleted" from the mixin's close(); skip those
                if not _wrapper_is_valid(widget):
                    continue
                # match by CLASS NAME, not isinstance: importlib.reload gives
                # ToolsetMaster a new class object, so old instances fail an
                # isinstance check and would be left alive - their dead
                # wrappers then fire mayaMixin callbacks (the recurring
                # "Internal C++ object already deleted" at mixin line 462)
                if type(widget).__name__ == "ToolsetMaster":
                    widget.setParent(None)
                    widget.close()
                    widget.deleteLater()
            except RuntimeError:
                pass
        # Closing the dialog does NOT remove its workspaceControl wrapper:
        # every relaunch would otherwise leave a ghost window behind (and the
        # user ends up looking at a stale copy while resizes go to the new
        # one). Delete all previous wrappers explicitly.
        for ctrl in cmds.lsUI(type="workspaceControl") or []:
            if ctrl.startswith("ToolsetMaster_"):
                try:
                    cmds.deleteUI(ctrl)
                except RuntimeError:
                    pass
    except Exception as e:
        cmds.warning(f"Error closing existing widget: {e}")

    ui = ToolsetMaster()
    ui.show(dockable=True, floating=True)
    return ui


if __name__ == "__main__":
    show_ui()
