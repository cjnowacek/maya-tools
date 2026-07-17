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

import os
import sys
import inspect
import importlib
import logging
from typing import Dict, List, Optional

from PySide2 import QtCore, QtWidgets
from shiboken2 import wrapInstance

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


def list_modules(script_path: str) -> List[str]:
    if not os.path.exists(script_path):
        cmds.warning(f"Path does not exist: {script_path}")
        return []

    module_names = []
    for file in os.listdir(script_path):
        if file.endswith(".py") and not file.startswith("__"):
            module_names.append(file.split(".")[0])
    return module_names


class ToolsetTab(QtWidgets.QWidget):
    """
    Tab widget for each tool category. Dynamically renders parameter inputs
    based on the selected script's main() signature.
    """

    def __init__(self, script_path: str, parent: Optional[QtWidgets.QWidget] = None):
        super(ToolsetTab, self).__init__(parent)
        self.script_path = script_path
        self.param_widgets: Dict[str, QtWidgets.QLineEdit] = {}

        self.script_combobox = QtWidgets.QComboBox()
        self.run_button = QtWidgets.QPushButton("Run")

        # Generic fallback input (shown when main has no named params)
        self.generic_label = QtWidgets.QLabel("Parameters:")
        self.generic_input = QtWidgets.QLineEdit("")
        self.generic_input.setPlaceholderText("Optional parameters")

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
        layout.addWidget(self.params_container)
        layout.addLayout(generic_row)
        layout.addWidget(self.run_button)
        layout.setAlignment(QtCore.Qt.AlignTop)

        self.script_combobox.currentIndexChanged.connect(self._on_script_changed)

    def _on_script_changed(self, index: int) -> None:
        module_name = self.script_combobox.itemData(index)
        self._refresh_params(module_name)

    def _refresh_params(self, script_name: str) -> None:
        """Inspect the selected module's main() and render per-parameter inputs."""
        # Clear dynamic fields
        while self.params_form.rowCount():
            self.params_form.removeRow(0)
        self.param_widgets.clear()

        if not script_name or not self.script_path:
            self._show_generic(True)
            return

        try:
            if self.script_path not in sys.path:
                sys.path.append(self.script_path)

            if script_name in sys.modules:
                mod = sys.modules[script_name]
            else:
                mod = importlib.import_module(script_name)

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
                for name, param in named_params:
                    field = QtWidgets.QLineEdit()
                    if param.default is not inspect.Parameter.empty:
                        field.setText(str(param.default))
                    self.params_form.addRow(name + ":", field)
                    self.param_widgets[name] = field
            else:
                self._show_generic(True)

        except Exception:
            self._show_generic(True)

    def _show_generic(self, visible: bool) -> None:
        self.generic_label.setVisible(visible)
        self.generic_input.setVisible(visible)

    def get_kwargs(self) -> dict:
        """Return named parameter values, casting to float/int where possible."""
        result = {}
        for name, widget in self.param_widgets.items():
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
        self.tabs = {
            "Rig": ToolsetTab(Config.get_tool_path("rig")),
            "Anim": ToolsetTab(Config.get_tool_path("anim")),
            "Model": ToolsetTab(Config.get_tool_path("model")),
            "Scene": ToolsetTab(Config.get_tool_path("scene")),
            "Wip": ToolsetTab(Config.get_tool_path("wip")),
        }

        for key, tab in self.tabs.items():
            for module_name in self.module_names.get(key.lower(), []):
                tab.script_combobox.addItem(
                    format_display_name(module_name), module_name
                )

        self.tab_widget = QtWidgets.QTabWidget()
        for name, tab in self.tabs.items():
            self.tab_widget.addTab(tab, name)

    def create_layout(self) -> None:
        main_layout = QtWidgets.QVBoxLayout(self)
        title_label = QtWidgets.QLabel(TOOL_DISPLAY_NAME)
        title_label.setAlignment(QtCore.Qt.AlignCenter)
        title_label.setStyleSheet("font-weight: bold; font-size: 13px; padding: 4px;")
        main_layout.addWidget(title_label)
        main_layout.addWidget(self.tab_widget)

    def create_connections(self) -> None:
        for category, tab in self.tabs.items():
            tab.run_button.clicked.connect(
                lambda checked=False, cat=category.lower(): self.run_script(cat)
            )

    def run_script(self, category: str) -> None:
        script_path = Config.get_tool_path(category)
        tab = self.tabs[category.capitalize()]
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

            if tab.param_widgets:
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
        for widget in QtWidgets.QApplication.topLevelWidgets():
            if isinstance(widget, ToolsetMaster):
                widget.close()
                widget.deleteLater()
    except Exception as e:
        cmds.warning(f"Error closing existing widget: {e}")

    ui = ToolsetMaster()
    ui.show(dockable=True, floating=True)
    return ui


if __name__ == "__main__":
    show_ui()
