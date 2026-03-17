# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a Maya Python toolset — a collection of rigging, animation, and modeling utilities for Autodesk Maya. All code runs inside Maya's Python environment (Python 3.x) and relies on Maya's APIs (`maya.cmds`, `maya.mel`, `maya.OpenMayaUI`) and PySide2 for UI.

## Running the Toolset

There is no standalone build or test runner. Everything executes inside Maya's Script Editor or shelf button:

```python
# Paste into Maya's Script Editor (Python tab) and run:
exec(open(r"C:\path\to\toolset_launcher.py").read())
```

Or drag `toolset_launcher.py` onto a Maya shelf. When running from the Script Editor (where `__file__` is undefined), update the hardcoded fallback path at `toolset_launcher.py:15`.

The launcher adds the project root, `core/`, and `modules/` to `sys.path`, then calls `toolset_master.show_ui()`.

## Architecture

### Entry Point → Main UI → Tool Modules

```
toolset_launcher.py          # Bootstraps sys.path, imports and calls toolset_master.show_ui()
core/toolset_master.py       # Main dockable QDialog; tabs: WIP | Model | Rig | Anim
core/Config.py               # Central config — TOOL_PATHS, UI sizes, joint defaults
modules/
  Rig/                       # Production rigging tools
    Lib/                     # Library modules imported by rig tools (not run directly)
  Anim/                      # Animation export/prep tools
  Model/                     # Geometry creation/export tools
  Scene/                     # Scene-wide utilities
  Wip/                       # Experimental tools (shown last in UI)
  ThirdParty/                # Third-party helper libraries
```

### Tool Discovery and Execution

`toolset_master.py:list_modules()` scans each category directory for `*.py` files (excluding `__init__.py`) and populates the tab dropdowns. When a script is run, `ToolsetMaster.run_script()` dynamically imports (or reloads) the module and calls its `main(user_input)` function. **Every tool module must expose a `main(*args)` function** — it's the required entry point.

### Rig Hierarchy Convention

`character_rig_handler.py` creates and expects this node structure in Maya:

```
{name}_rig
  ├── {name}_Controls
  ├── {name}_Meshes
  │     ├── {name}_ExportMeshes   ← meshes exported to FBX
  │     └── {name}_bak
  └── {name}_Skeleton             ← root joint lives here
```

`MayaRigHandler._find_rigs()` identifies rigs by finding transforms named `rig`, `RIG`, or ending with `_rig`.

### Secondary Rig UI

`modules/Rig/rig_toolset.py` is a separate dockable window (`QuickToolsWindow`) with three tabs: Quick Tools (joint axis/orientation), Renamer, and Rig Compiler. It is invoked as a tool module (via `main()`) from the Rig tab, not from `toolset_master` directly.

## Key Conventions

- **Tool modules** live in `modules/<Category>/` (PascalCase) and must have a `main(*args)` function.
- **WIP tools** in `modules/Wip/` are for active development; they show last in the UI.
- `Config.TOOL_PATHS` is the authoritative mapping from tab name to directory — update it when adding new categories.
- Rigs are detected by name pattern (`_rig` suffix), not by node type or attribute.
- FBX export settings are hardcoded in `character_rig_handler._export_rig()` — the output path (`C:/dropbox/your_file.fbx`) is a placeholder that needs updating.
