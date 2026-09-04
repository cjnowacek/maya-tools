# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

A Maya Python toolset — rigging, animation, and modeling utilities for Autodesk Maya. All code runs inside Maya's embedded Python (3.x) and depends on Maya's APIs (`maya.cmds`, `maya.mel`, `maya.OpenMayaUI`) and PySide2/shiboken2 for UI. There is **no way to run, build, or test this outside of Maya** — there is no standalone interpreter entry point, no test suite, no linter config, and no package manifest.

## Running the Toolset

Paste into Maya's Script Editor (Python tab) and run, or drag `toolset_launcher.py` onto a Maya shelf:

```python
exec(open(r"C:\path\to\toolset_launcher.py").read())
```

`toolset_launcher.py` bootstraps `sys.path` (project root + `core/` + `modules/`), force-reloads any already-imported `core`/`modules`/`tools` submodules (so edits take effect without restarting Maya), then imports `core.toolset_master` and calls `show_ui()`.

When running from the Script Editor, `__file__` is undefined, so the launcher falls back to the **`MAYA_TOOLS_ROOT` environment variable** — set it to your checkout location (the launcher raises a clear error if it's unset).

## Architecture

### Entry point → main UI → tool modules

```
toolset_launcher.py        # sys.path bootstrap + reload; calls toolset_master.show_ui()
core/
  toolset_master.py        # Main dockable QDialog; tabs: Workflow | Rig | Anim | Model | Scene | Wip
  Config.py                # Central config: TOOL_PATHS, UI sizes, joint DEFAULTS, scene-path helpers
  path_utils.py            # Scene file-path globals (legacy/standalone helper)
modules/
  rig/                     # Production rigging tools
    Lib/                   # Library modules imported BY rig tools (not run via the UI)
  anim/                    # Animation export/prep tools
  model/                   # Geometry creation/export tools
  scene/                   # Scene-wide utilities
  wip/                     # Experimental tools (shown last in the UI)
```

### The tool contract (three tiers)

**Every tool module must expose a top-level `main(...)` function.** Modules in `Lib/` (e.g. `joint_tools.py`, `scene_meta.py`, `build_locators.py`) are imported as helpers and are not invoked directly by the UI. On top of `main`, a tool opts into richer UI declaratively:

1. **Nothing else declared** — one generic text input, passed as a positional string.
2. **`TOOL_META` dict** — `"description"` fills the always-visible description panel (module docstring is the fallback); `"params"` refines the auto-generated widgets per parameter: `label`, `tooltip`, `min`/`max` (clamp spinboxes), `choices` (dropdown), `choices_fn` (name of a module function returning per-scene options, e.g. namespaces), `editable` (combobox accepts typed text).
3. **`def build_ui(parent)`** — the tool returns its own QWidget, embedded in the main window on selection (no popups). Run calls `main(**ui_kwargs(widget))` if the module defines `ui_kwargs`, else `main()`. Use only for real interaction that fields cannot express (see `anim_master.py`); prefer tier 2.

The workflow composites in `modules/workflow/` record/read scene state through `Lib/scene_meta.py` (a `TOOLSET_META` network node with message links to built nodes), guard against double-builds, and redirect to the correct builder when prerequisites are missing.

`ToolsetMaster.run_script()` dynamically imports (or `importlib.reload`s) the selected module and calls `main`. If `main` returns an object with a `.show()` method (a Qt widget), the UI shows it — this is how tools open their own secondary windows.

### Dynamic parameter UI (signature introspection)

`core/toolset_master.py` is generic and knows nothing about individual tools. When a script is selected, `ToolsetTab._refresh_params()` calls `inspect.signature(mod.main)`:

- If `main` has **named parameters**, the tab renders one labeled `QLineEdit` per parameter (pre-filled with the default). Values are passed as `**kwargs`, with each string cast to `int`/`float` when possible (`get_kwargs()`).
- If `main` only takes `*args`/`**kwargs` (or none), the tab shows a single generic input passed as one positional string.

Practical effect: to give a tool typed input fields in the UI, give its `main()` explicit named parameters (e.g. `def main(sphere_name="default_sphere", *args)`). Otherwise it gets the single free-text box.

### Tool discovery

`list_modules()` scans each `Config.TOOL_PATHS` directory for `*.py` files (skipping `__`-prefixed). The tab keys (`Rig`, `Anim`, …) map to category dirs via `Config.get_tool_path(category.lower())`. **Adding a new category requires updating `Config.TOOL_PATHS`** — it is the authoritative tab-name → directory mapping.

Dropdown labels are derived from filenames by `format_display_name()` (underscores → spaces, title case: `create_sphere.py` → "Create Sphere"), so name tool files in snake_case.

### Rig hierarchy convention

`modules/rig/character_rig_handler.py` (a separate `MayaRigHandler` dialog, launched from the Rig tab) creates and expects this node structure:

```
{name}_rig
  ├── {name}_Controls
  ├── {name}_Meshes
  │     ├── {name}_ExportMeshes   ← meshes exported to FBX
  │     └── {name}_bak            ← backup / WIP meshes
  └── {name}_Skeleton             ← root joint lives here
```

Rigs are detected **by name pattern, not node type or attribute**: `_find_rigs()` matches transforms named `rig`, `RIG`, or ending in `_rig`. Export selection walks this hierarchy with several fallbacks to find the root joint and export meshes.

### Secondary Rig UI

`modules/rig/rig_toolset.py` is a separate dockable window (`QuickToolsWindow`) with tabs for Quick Tools (joint axis/orientation), Renamer, and Rig Compiler. It is launched as a tool module via its `main()` from the Rig tab. It imports helpers from `Lib/` (`joint_tools`, `rig_compiler`).

## Key Conventions & Gotchas

- **Casing is standardized lowercase** for module directories, `Config.TOOL_PATHS`, and intra-package imports (`from modules.rig.Lib import joint_tools`); `Lib/` keeps its capital L. Match on-disk casing exactly in any new imports or `TOOL_PATHS` entries so the code stays portable to case-sensitive filesystems.
- **Lib imports go through the package path** `from modules.rig.Lib import ...` and `from core.Config import Config`, which only resolve because the launcher put the project root on `sys.path`.
- **Hardcoded path needs updating before use:** FBX export output in `character_rig_handler._export_rig()` (`C:/dropbox/your_file.fbx`) is a placeholder. FBX export settings there are hardcoded MEL `FBXExport*` calls.
- **Code style:** black-style formatting; snake_case filenames and functions. Use a module-level `logger = logging.getLogger(__name__)` for diagnostics rather than `print`, and `cmds.warning(...)` for user-facing warnings in Maya.
- **WIP tools** (`modules/wip/`) are active-development and show last in the UI; treat them as unstable.
- No automated tests or CI — verification is manual, inside Maya.
