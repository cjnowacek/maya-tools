# CJ's Maya Tools

A dockable rigging, animation, and modeling toolset for Autodesk Maya, built in Python/PySide2. One launcher opens a tabbed UI that discovers every tool in the repo automatically: drop a script in the right folder, give it a `main()`, and it shows up in the UI with typed input fields generated from its function signature.

Built and maintained by [CJ Nowacek](https://cjnowacek.com), technical artist and pipeline developer (SMITE 2, MediaLab 3D Solutions).

<!-- TODO: screenshot of the docked UI goes here
![Toolset Master docked in Maya](docs/toolset_ui.png)
-->

## Features

- **Dockable tabbed UI** (`core/toolset_master.py`) that integrates with Maya's workspace
- **Zero-registration tool discovery**: each tab lists the `*.py` files in its category folder; selecting a tool introspects `main()`'s signature and renders one input field per named parameter
- **Rigging tools**: joint creation and orientation, batch renaming, rig compilation, Unreal-oriented auto-rig helpers, and a character rig handler that builds and exports a standard rig hierarchy to FBX
- **Animation tools**: animation export and scene prep utilities
- **Hot reload**: rerunning the launcher reloads changed modules without restarting Maya

## Requirements

- Autodesk Maya 2020–2024 (PySide2/shiboken2; Maya 2025+ ships PySide6 and is not yet supported)
- No dependencies outside Maya's bundled Python

## Installation

1. Clone the repo:
   ```
   git clone https://github.com/cjnowacek/maya-tools.git
   ```
2. In Maya's Script Editor (Python tab), run:
   ```python
   exec(open(r"C:/path/to/maya-tools/toolset_launcher.py").read())
   ```
   or middle-drag that snippet to a shelf button.

If you paste the launcher's *contents* into the Script Editor instead of `exec`-ing the file, set a `MAYA_TOOLS_ROOT` environment variable pointing at the repo first (with no `__file__`, the launcher can't locate itself).

## Adding a tool

1. Save a snake_case `.py` file into `modules/rig/`, `modules/anim/`, `modules/model/`, `modules/scene/`, or `modules/wip/`
2. Expose a top-level `main()` function; named parameters with defaults become labeled input fields in the UI
3. Relaunch: the tool appears in its category tab, titled from its filename

Shared helpers imported by tools (not shown in the UI) live in `modules/rig/Lib/`.

## Repo layout

```
toolset_launcher.py   # run this inside Maya
core/                 # UI framework + config
modules/
  rig/                # production rigging tools (Lib/ = shared helpers)
  anim/               # animation export/prep
  model/              # geometry utilities
  scene/              # scene-wide utilities
  wip/                # experimental tools, shown last in the UI
```

## Recommended companion scripts

Not bundled (their licenses don't permit redistribution), but they pair well with this toolset:

- [cometJointOrient](http://www.comet-cartoons.com/melscript.html) by Michael Comet: joint orientation utility
- [zTools](https://github.com/zethwillie/zTools) by Zeth Willie: control shapes and rigging helpers

## License

[GPL-3.0](LICENSE)
