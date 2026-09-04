"""
/rig/Tool_RigMaster.py

This script provides a dockable UI inside Autodesk Maya for rigging workflows.
It includes tools for joint creation, orientation, axis visibility, renaming, and miscellaneous widgets.

### Features:
- Supports creation, modification, and visualization of hierarchical structures.
- Provides batch processing tools for efficient renaming and organization.
- Includes interactive UI components such as sliders, dropdowns, and numeric inputs.
- Designed for seamless integration within an existing workspace for enhanced accessibility.

### Usage:
1. Run the script to launch the `QuickToolsWindow` UI.
2. Navigate through different tool tabs to access functionalities.
3. Click buttons to execute rigging-related operations.

### Metadata:
- **Author:** CJ Nowacek
- **Version:** 1.0.0
- **License:** GPL
- **Maintainer:** CJ Nowacek
- **Status:** Production
"""

# ------------------------------
# Imports
# ------------------------------
import logging
import maya.cmds as cmds
import maya.OpenMayaUI as omui
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
try:
    from shiboken6 import wrapInstance  # Maya 2025+
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QWidget,
        QPushButton,
        QLineEdit,
        QSlider,
        QRadioButton,
        QHBoxLayout,
        QVBoxLayout,
        QGroupBox,
        QLabel,
        QComboBox,
        QSpinBox,
        QTabWidget,
        QMenuBar,
        QMenu,
    )
except ImportError:
    from shiboken2 import wrapInstance  # Maya 2024 and earlier
    from PySide2.QtCore import Qt
    from PySide2.QtWidgets import (
        QWidget,
        QPushButton,
        QLineEdit,
        QSlider,
        QRadioButton,
        QHBoxLayout,
        QVBoxLayout,
        QGroupBox,
        QLabel,
        QComboBox,
        QSpinBox,
        QTabWidget,
        QMenuBar,
        QMenu,
    )


from modules.rig.Lib import joint_tools as jt

logger = logging.getLogger(__name__)


# ------------------------------
# Utility Functions
# ------------------------------
TOOL_META = {
    "description": (
        'Quick Tools rigging window (opens its own window).\n\n'
        'Dockable tabs for joint work: toggle local rotation axes, create '
        'and aim joints, orient joints with axis pickers, batch renaming, '
        'and the rig compiler.'
    ),
}


def print_widget_name(widget_name):
    """Helper to log the name of interacted widgets."""
    logger.debug(f"Widget '{widget_name}' was interacted with.")


def get_maya_main_window():
    """Returns the main Maya window as a QWidget instance."""
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QWidget)


# ------------------------------
# Main UI Class
# ------------------------------
class QuickToolsWindow(MayaQWidgetDockableMixin, QWidget):
    """Main UI class for RigMaster, containing tool tabs and layouts."""

    def __init__(self, parent=None):
        super(QuickToolsWindow, self).__init__(parent=parent)
        self.setWindowTitle("Rig Toolset")
        self.setObjectName("RigMasterWindow")

        # Initialize the modules
        self.joint_module = jt.JointCreateAndOrientator()

        # 🔹 Create main layout
        main_layout = QVBoxLayout(self)

        # 🔹 Create Menu Bar (Manually Add It)
        self.menu_bar = QMenuBar(self)
        main_layout.addWidget(self.menu_bar)  # ✅ Add menu bar as a widget

        # 🔹 Add File Menu
        file_menu = self.menu_bar.addMenu("File")
        file_menu.addAction("New", self.new_action)
        file_menu.addAction("Open", self.open_action)
        file_menu.addAction("Save", self.save_action)
        file_menu.addSeparator()
        file_menu.addAction("Exit", self.close)

        # 🔹 Add Macros Menu
        macros_menu = self.menu_bar.addMenu("Macros")
        macros_menu.addAction("Unreal Auto Control Rig", self.unrealcontrolrig_action)
        macros_menu.addAction("Redo", self.redo_action)

        # 🔹 Add Help Menu
        help_menu = self.menu_bar.addMenu("Help")
        help_menu.addAction("About", self.about_action)

        # 🔹 Level 1: Create "Export" Submenu
        export_menu = QMenu("Export", self)

        # 🔹 Level 2: Create "3D Models" Submenu inside "Export"
        models_menu = QMenu("3D Models", self)

        # 🔹 Level 3: Add Export Options inside "3D Models"
        models_menu.addAction("Export as FBX", self.export_fbx_action)
        models_menu.addAction("Export as OBJ", self.export_obj_action)

        # Attach "3D Models" submenu inside "Export"
        export_menu.addMenu(models_menu)

        # Attach "Export" submenu inside "File"
        file_menu.addMenu(export_menu)

        # 🔹 Create and add tab widget
        self.tabs = QTabWidget(self)
        main_layout.addWidget(self.tabs)

        # 🔹 Create first tab (Quick Tools)
        first_tab = QWidget()
        first_tab.setLayout(self.create_first_tab())
        self.tabs.addTab(first_tab, "Quick Tools")

        # 🔹 Create second tab
        second_tab = QWidget()
        second_tab.setLayout(self.create_second_tab())
        self.tabs.addTab(second_tab, "Renamer")

        # 🔹 Create third tab
        third_tab = QWidget()
        third_tab.setLayout(self.create_third_tab())
        self.tabs.addTab(third_tab, "Rig Compiler")

        # 🔹 Set main layout
        self.setLayout(main_layout)

    # ------------------------------
    # Menu Actions
    # ------------------------------
    def new_action(self):
        logger.debug("New File Created")

    def open_action(self):
        logger.debug("Open File Dialog Triggered")

    def save_action(self):
        logger.debug("Save File Dialog Triggered")

    def unrealcontrolrig_action(self):
        from modules.rig.Lib import unreal_auto_rig as bUR

        bUR.BuildUnrealRig()

    def redo_action(self):
        logger.debug("Redo Action")

    def about_action(self):
        logger.debug("About Dialog Triggered")

    def export_fbx_action(self):
        logger.debug("Exporting as FBX...")

    def export_obj_action(self):
        logger.debug("Exporting as OBJ...")

    # ------------------------------
    # First Tab (Quick Tools)
    # ------------------------------
    def create_first_tab(self):
        """Creates layout for the Quick Tools tab."""
        layout = QVBoxLayout()

        # Add joint axis visibility buttons
        layout.addLayout(self.create_joint_axis_widget())

        # Add create and aim joint buttons
        layout.addLayout(self.create_create_aim_widgets())

        # Add axis radio button groups
        layout.addWidget(self.create_axis_radio_group("Aim"))
        layout.addWidget(self.create_axis_radio_group("Up"))

        # Add orient joints button
        layout.addLayout(self.create_orient_joints_widget())

        # Additional UI elements (Slider, ComboBox, SpinBox, Label)
        # layout.addLayout(self.create_slider_widget())
        # layout.addLayout(self.create_combo_box_widget())
        # layout.addLayout(self.create_spin_box_widget())
        # layout.addLayout(self.create_label_widget())

        return layout

    # ------------------------------
    # Second Tab
    # ------------------------------
    def create_second_tab(self):
        """Creates layout for the second tab."""
        layout = QVBoxLayout()

        # Add rename widgets
        sr_rename_wdgt, ps_rename_wdgt = self.create_rename_widgets()
        layout.addLayout(sr_rename_wdgt)
        layout.addLayout(ps_rename_wdgt)

        # Add placeholder label and button
        label = QLabel("This is the second tab")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)

        button = QPushButton("Button in Second Tab")
        button.clicked.connect(lambda: print_widget_name("Second Tab Button"))
        layout.addWidget(button)

        return layout

    # ------------------------------
    # Third Tab
    # ------------------------------
    def create_third_tab(self):
        """Creates layout for the Rig Compiler tab."""
        layout = QVBoxLayout()

        # layout.addLayout(self.compile_rig())

        sr_rename_wdgt, ps_rename_wdgt = self.compile_rig()
        layout.addLayout(sr_rename_wdgt)
        layout.addLayout(ps_rename_wdgt)

        return layout

    # ------------------------------
    # Widgets
    # ------------------------------
    def create_joint_axis_widget(self):
        """Creates widget for controlling joint axis visibility."""
        layout = QHBoxLayout()
        show_axis_btn = QPushButton("Show Axis")
        hide_axis_btn = QPushButton("Hide Axis")
        show_axis_btn.clicked.connect(self.joint_module.turnOnJointAxisVis)
        hide_axis_btn.clicked.connect(self.joint_module.turnOffJointAxisVis)
        layout.addWidget(show_axis_btn)
        layout.addWidget(hide_axis_btn)
        return layout

    def create_create_aim_widgets(self):
        """Creates widget for creating and aiming joints."""
        layout = QHBoxLayout()
        create_jnt_btn = QPushButton("Joint at component")
        aim_jnt_btn = QPushButton("Aim at component")
        create_jnt_btn.clicked.connect(self.joint_module.createBaseJoint)
        aim_jnt_btn.clicked.connect(self.joint_module.endBaseJoint)
        layout.addWidget(create_jnt_btn)
        layout.addWidget(aim_jnt_btn)
        return layout

    def create_axis_radio_group(self, label):
        """Creates a group box with radio buttons for axis selection."""
        group_box = QGroupBox(label)
        layout = QHBoxLayout()
        for axis in ["X", "Y", "Z"]:
            layout.addWidget(QRadioButton(axis))
        group_box.setLayout(layout)
        return group_box

    def create_orient_joints_widget(self):
        """Creates a button to orient joints."""
        layout = QHBoxLayout()
        layout.addWidget(QPushButton("Orient Joints"))
        return layout

    def create_rename_widgets(self):
        """Creates widgets for renaming tools (search/replace & prefix/suffix)."""
        sr_layout = QHBoxLayout()
        sr_layout.addWidget(QLabel("Search"))
        sr_layout.addWidget(QLineEdit())
        sr_layout.addWidget(QLabel("Replace"))
        sr_layout.addWidget(QLineEdit())

        ps_layout = QHBoxLayout()
        ps_layout.addWidget(QLabel("Prefix"))
        ps_layout.addWidget(QLineEdit())
        ps_layout.addWidget(QLabel("Suffix"))
        ps_layout.addWidget(QLineEdit())

        return sr_layout, ps_layout

    def create_slider_widget(self):
        """Creates a slider widget."""
        layout = QVBoxLayout()
        slider = QSlider(Qt.Horizontal)
        slider.valueChanged.connect(lambda: print_widget_name("QSlider"))
        layout.addWidget(slider)
        return layout

    def create_combo_box_widget(self):
        """Creates a combo box widget."""
        layout = QVBoxLayout()
        combo_box = QComboBox()
        combo_box.addItems(["Choice 1", "Choice 2", "Choice 3"])
        combo_box.currentIndexChanged.connect(lambda: print_widget_name("QComboBox"))
        layout.addWidget(combo_box)
        return layout

    def create_spin_box_widget(self):
        """Creates a spin box widget."""
        layout = QVBoxLayout()
        spin_box = QSpinBox()
        spin_box.valueChanged.connect(lambda: print_widget_name("QSpinBox"))
        layout.addWidget(spin_box)
        return layout

    def create_label_widget(self):
        """Creates a label widget."""
        layout = QVBoxLayout()
        layout.addWidget(QLabel("This is a label"))
        return layout

    def compile_rig(self):
        """Creates widget for controlling rig compilation."""
        # Path input
        layout1 = QHBoxLayout()
        rig_path = QLineEdit("")
        rig_path.setPlaceholderText(
            "Path to Rig Directory (leave empty to use default)"
        )
        layout1.addWidget(rig_path)

        # Action buttons
        layout = QHBoxLayout()
        compile_btn = QPushButton("Compile")
        decompile_btn = QPushButton("Decompile")

        # Connect buttons with lambda functions to pass the current text value
        compile_btn.clicked.connect(
            lambda: self.handle_compile(rig_path.text(), "compile")
        )
        decompile_btn.clicked.connect(
            lambda: self.handle_compile(rig_path.text(), "decompile")
        )

        layout.addWidget(compile_btn)
        layout.addWidget(decompile_btn)

        return layout1, layout

    def handle_compile(self, path, operation):
        """Handler for compile/decompile operations with better error handling."""
        try:
            # First make sure the scene is saved
            if not cmds.file(q=True, sn=True):
                cmds.confirmDialog(
                    title="Save Required",
                    message="Please save your Maya scene before compiling or decompiling.",
                    button=["OK"],
                    defaultButton="OK",
                )
                return

            # Call the rig_compiler function with proper parameters
            from modules.rig.Lib import rig_compiler as rc

            rc.run(path, operation)
        except Exception as e:
            import traceback

            error_msg = str(e)
            tb = traceback.format_exc()
            cmds.warning(f"Error during {operation}: {error_msg}")
            logger.error(f"Traceback: {tb}")

            # Show a more user-friendly error dialog
            cmds.confirmDialog(
                title="Operation Failed",
                message=f"The {operation} operation failed: {error_msg}",
                button=["OK"],
                defaultButton="OK",
            )


# ------------------------------
# Dockable Widget Function
# ------------------------------
def show_dockable_widget():
    """Shows the dockable QuickToolsWindow in Maya."""
    global tm_tab_window

    try:
        if tm_tab_window:
            tm_tab_window.close()
            tm_tab_window.deleteLater()
            tm_tab_window = None

    except Exception as e:
        logger.warning(f"Error deleting UI: {e}")

    tm_tab_window = QuickToolsWindow()
    tm_tab_window.show()


def main(*args):
    show_dockable_widget()


if __name__ == "__main__":
    main()
