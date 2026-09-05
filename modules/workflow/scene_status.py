"""Show what the workflow has built in this scene, and what comes next."""
import logging

import maya.cmds as mc

from modules.rig.Lib import scene_meta

logger = logging.getLogger(__name__)

TOOL_META = {
    "order": 99,
    "description": (
        "Report the scene's workflow state from the TOOLSET_META node.\n\n"
        "Lists every workflow step: done (with timestamp and the nodes it "
        "built, tracked by rename-proof message links) or not, plus the "
        "suggested next step. Steps run before the meta node existed will "
        "show as not done; they can be re-recorded by re-running their "
        "workflow tool."
    ),
}


def main(*args):
    report = scene_meta.summary()
    logger.info("Scene status:\n%s", report)
    print(report)
    mc.confirmDialog(title="Scene Workflow Status", message=report,
                     button=["OK"], defaultButton="OK")
    return report
