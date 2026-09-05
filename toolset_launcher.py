"""Launch CJ's Maya Tools.

Run from a shelf button, the Script Editor, or as a file:

    exec(open(r"C:/dev/maya-tools/toolset_launcher.py").read())

Bootstraps sys.path, force-reloads the package so code edits take effect
without restarting Maya, then shows the dockable UI.
"""
import importlib
import os
import sys
import traceback

import maya.cmds as cmds

print("=== TOOLSET LAUNCHER STARTING ===")


def _project_root():
    """Where this file lives.

    __file__ is undefined under exec() from a shelf button, so fall back to
    MAYA_TOOLS_ROOT, then to any sys.path entry that actually contains the
    package. The old hardcoded Dropbox path is gone: it pointed at a
    checkout that no longer exists and made the failure silent.
    """
    try:
        return os.path.dirname(os.path.abspath(__file__))
    except NameError:
        pass
    env = os.environ.get("MAYA_TOOLS_ROOT")
    if env and os.path.isdir(os.path.join(env, "core")):
        return env
    for path in sys.path:
        try:
            if path and os.path.isfile(
                    os.path.join(path, "core", "toolset_master.py")):
                return path
        except (TypeError, OSError):
            continue
    return None


def launch():
    root = _project_root()
    if not root:
        cmds.warning("Toolset: cannot find the project root. Set "
                     "MAYA_TOOLS_ROOT or add the checkout to sys.path.")
        return None
    print("Project root: {}".format(root))
    if root not in sys.path:
        sys.path.insert(0, root)

    # Reload the package so edits land without restarting Maya. Order
    # matters: reloading a parent before its children leaves the parent
    # holding stale child references, so reload deepest-first.
    names = [m for m in list(sys.modules)
             if m == "core" or m.startswith("core.")
             or m == "modules" or m.startswith("modules.")]
    for name in sorted(names, key=lambda n: n.count("."), reverse=True):
        mod = sys.modules.get(name)
        if mod is None:
            continue
        try:
            importlib.reload(mod)
        except Exception as exc:            # a broken edit must not block launch
            print("Reload skipped for {}: {}".format(name, exc))

    try:
        from core import toolset_master
    except Exception:
        traceback.print_exc()
        cmds.warning("Toolset: could not import core.toolset_master (see "
                     "the Script Editor).")
        return None

    try:
        ui = toolset_master.show_ui()
        print("UI displayed successfully")
        return ui
    except Exception:
        traceback.print_exc()
        cmds.warning("Toolset: show_ui failed (see the Script Editor).")
        return None


# Always launch. The old guard was `if __name__ == "__main__"`, but exec()
# inherits the CALLER's __name__ - from a shelf button that is often not
# "__main__", so the launcher would run, print its markers, and silently
# never open the window. That was the intermittent-launch bug.
TM = launch()

print("=== TOOLSET LAUNCHER COMPLETED ===")
