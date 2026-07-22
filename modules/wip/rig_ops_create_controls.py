"""Build an FK circle-control chain over the selected joints.

Select the joints in chain order (root first). Each joint named with the
token (default "JNT") gets a CON circle and a zeroed GRP; each GRP is
parented under the previous control to form the FK chain.
"""

import logging

import maya.cmds as mc

logger = logging.getLogger(__name__)


def main(name_token="JNT", *args):
    create_fk_controls(name_token or "JNT")


def create_fk_controls(name_token="JNT"):
    sel = mc.ls(sl=True, type="joint")
    if not sel:
        mc.warning("Select the joint chain (root first) to build FK controls on.")
        return None

    chain = []
    controls = []
    for jnt in sel:
        if name_token not in jnt:
            mc.warning(
                "'{}' does not contain the token '{}'; names may clash.".format(
                    jnt, name_token
                )
            )
        con = mc.circle(n=jnt.replace(name_token, "CON"), nr=[1, 0, 0], sw=360)
        grp = mc.group(n=jnt.replace(name_token, "GRP"))
        const = mc.parentConstraint(jnt, grp, mo=False)
        mc.delete(const)
        mc.parentConstraint(con[0], jnt, mo=True)

        chain.append(grp)
        chain.append(con[0])
        controls.append(con[0])

    # [grp0, con0, grp1, con1, ...] -> parent each grp under the previous con
    chain.pop(0)
    for i in range(len(chain) // 2):
        mc.parent(chain[i * 2 + 1], chain[i * 2])

    mc.select(controls)
    logger.debug("Built FK controls: %s", controls)
    return controls
