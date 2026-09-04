"""NURBS ribbon segments for the leg rig (iteration 3).

A ribbon replaces discrete roll joints. Each limb segment gets a NURBS surface
skinned to three drivers (top / mid / bottom); the bind joints are pinned to
that surface with a single `uvPin` node per segment.

Why a surface rather than a curve: a curve only gives a tangent, so twist has
to be supplied and interpolated by hand (spline IK's advanced twist controls,
up-vector objects, and the flipping that comes with them). A surface carries a
width direction at every point, so tangent + width + their cross product is a
complete, continuous frame. Twist interpolation is free.

The payoff on this rig: drive the thigh ribbon's top from a NON-twisting hip
node and its bottom from the knee, and the surface interpolates from a stable
pelvis to a twisting femur on its own. That removes the whole quaternion
twist-extraction network the roll-joint version needed.

Surface conventions established by measurement (Maya 2027):
  * nurbsPlane U runs across the WIDTH, V along the LENGTH
  * V runs from local +Z (v=0) to local -Z (v=1)
  * rebuildSurface to degreeU=1 / degreeV=3 gives 2 x (spans+3) CVs
  * uvPin with normalAxis=1, tangentAxis=2 yields X along V (down the bone),
    Y on the surface normal, Z across the width

    from modules.rig.Lib import leg_ribbon
    leg_ribbon.add_ribbons(prefix, rig, guides, joints_per_segment=5)
"""
import math

import maya.cmds as cmds
import maya.api.OpenMaya as om

from modules.rig.Lib import leg_rig_builder as lrb


def _euler_from_rows(rows):
    """XYZ euler (degrees) from three orthonormal basis rows."""
    m = om.MMatrix(rows[0] + [0] + rows[1] + [0] + rows[2] + [0] + [0, 0, 0, 1])
    return [math.degrees(a) for a in om.MTransformationMatrix(m).rotation()]


def _frame(aim, side):
    """Rows for a segment frame: X down the bone, Z across (side), Y the rest.

    Returned in surface-local order (width, normal, length) because the plane
    is built with width on X, normal on Y and length on Z.
    """
    row0 = side                      # local X -> width, across the limb
    row2 = lrb.mul(aim, -1.0)        # local Z -> V runs +Z to -Z, so -aim
    row1 = lrb.cross(row2, row0)     # local Y -> surface normal
    return [row0, row1, row2]


def _make_surface(name, start, end, side, width, spans, parent):
    """A ribbon surface spanning start -> end, already placed and parented.

    `parent` must be an identity transform, so local placement is world
    placement. Values are set on the channels directly rather than through a
    world-space xform: inside one script block the parent matrices are stale
    and a world-space set silently fails to survive the next evaluation.
    """
    length = lrb.mag(lrb.sub(end, start))
    srf = cmds.nurbsPlane(name=name, pivot=(0, 0, 0), axis=(0, 1, 0), width=width,
                          lengthRatio=length / width, degree=3, patchesU=1,
                          patchesV=spans, constructionHistory=False)[0]
    cmds.rebuildSurface(srf, constructionHistory=False, replaceOriginal=True, direction=2,
                        degreeU=1, degreeV=3, spansU=1, spansV=spans,
                        keepRange=0, rebuildType=0)
    srf = cmds.parent(srf, parent, relative=True)[0]
    aim = lrb.norm(lrb.sub(end, start))
    cmds.setAttr(srf + '.rotate', *_euler_from_rows(_frame(aim, side)))
    cmds.setAttr(srf + '.translate', *lrb.mul(lrb.add(start, end), 0.5))
    for a in ('translateX', 'translateY', 'translateZ', 'rotateX', 'rotateY', 'rotateZ',
              'scaleX', 'scaleY', 'scaleZ', 'visibility'):
        cmds.setAttr(srf + '.' + a, lock=True)
    return srf


def _driver(name, pos, aim, side, parent, radius):
    j = cmds.createNode('joint', name=name, parent=parent)
    cmds.setAttr(j + '.radius', radius)
    rows = _frame(aim, side)
    # driver joints use the joint convention: X down bone, Z across
    cmds.setAttr(j + '.jointOrient', *_euler_from_rows(
        [lrb.mul(rows[2], -1.0), rows[1], rows[0]]))
    cmds.setAttr(j + '.translate', *pos)
    return j


def _skin_ribbon(srf, drivers, start, end):
    """Skin the surface to top/mid/bottom with a deterministic linear tent.

    A default bind is not used here on purpose: it weights by distance to the
    bone (joint to child) and these drivers are childless, which is the same
    trap that left the roll joints almost unweighted in iteration 2.
    """
    sc = cmds.skinCluster(drivers, srf, toSelectedBones=True, bindMethod=0,
                          skinMethod=0, normalizeWeights=1,
                          name=srf.split('|')[-1] + '_skin')[0]
    shape = cmds.listRelatives(srf, shapes=True, fullPath=True)[0]
    axis = lrb.sub(end, start)
    L2 = lrb.dot(axis, axis)
    nu = cmds.getAttr(shape + '.spansUV')[0][0] + cmds.getAttr(shape + '.degreeU')
    nv = cmds.getAttr(shape + '.spansUV')[0][1] + cmds.getAttr(shape + '.degreeV')
    for iu in range(int(nu)):
        for iv in range(int(nv)):
            cv = '%s.cv[%d][%d]' % (srf, iu, iv)
            p = cmds.pointPosition(cv, world=True)
            t = max(0.0, min(1.0, lrb.dot(lrb.sub(p, start), axis) / L2))
            if t <= 0.5:
                w = [(drivers[0], 1.0 - 2.0 * t), (drivers[1], 2.0 * t), (drivers[2], 0.0)]
            else:
                w = [(drivers[0], 0.0), (drivers[1], 2.0 - 2.0 * t), (drivers[2], 2.0 * t - 1.0)]
            cmds.skinPercent(sc, cv, transformValue=w)
    return sc


def _pin_joints(prefix, tag, srf, count, parent, radius):
    """Pin `count` bind joints evenly along the surface with one uvPin node.

    The pin matrix is taken into the parent joint's space and decomposed onto
    translate / rotate / scale rather than connected to offsetParentMatrix.
    That matters for export: FBX writes TRS and knows nothing about
    offsetParentMatrix, and baking cannot rescue it either, because the TRS
    channels evaluate to zero however the joint is actually moving. Driving TRS
    keeps the joints under a real skeleton hierarchy and bakes correctly.
    """
    shape = cmds.listRelatives(srf, shapes=True, fullPath=True)[0]
    pin = cmds.createNode('uvPin', name='%s%s_pin' % (prefix, tag))
    cmds.connectAttr(shape + '.worldSpace[0]', pin + '.deformedGeometry')
    cmds.setAttr(pin + '.normalAxis', 1)     # Y = surface normal
    cmds.setAttr(pin + '.tangentAxis', 2)    # Z = width  -> X ends up along V
    joints = []
    for i in range(count):
        v = i / float(count - 1) if count > 1 else 0.5
        cmds.setAttr('%s.coordinate[%d].coordinateU' % (pin, i), 0.5)
        cmds.setAttr('%s.coordinate[%d].coordinateV' % (pin, i), v)
        j = cmds.createNode('joint', name='%s%s%02d_bind_jnt' % (prefix, tag, i + 1),
                            parent=parent)
        cmds.setAttr(j + '.radius', radius)
        cmds.setAttr(j + '.jointOrient', 0, 0, 0)
        mm = cmds.createNode('multMatrix', name='%s%s%02d_toParent' % (prefix, tag, i + 1))
        cmds.connectAttr('%s.outputMatrix[%d]' % (pin, i), mm + '.matrixIn[0]')
        cmds.connectAttr(parent + '.worldInverseMatrix[0]', mm + '.matrixIn[1]')
        dm = cmds.createNode('decomposeMatrix', name='%s%s%02d_dcm' % (prefix, tag, i + 1))
        cmds.connectAttr(mm + '.matrixSum', dm + '.inputMatrix')
        cmds.connectAttr(dm + '.outputTranslate', j + '.translate')
        cmds.connectAttr(dm + '.outputRotate', j + '.rotate')
        cmds.connectAttr(dm + '.outputScale', j + '.scale')
        joints.append(j)
    return pin, joints


def add_ribbons(prefix, rig, P, joints_per_segment=5, mid_ctrl=True, width=None):
    """Add a ribbon to the thigh and shin of an already-built leg rig.

    `rig` is the dict returned by leg_rig_builder.build_leg (built with
    roll_joints=0; the ribbon replaces them).
    """
    bind = rig['bind']
    n_plane = rig['plane']
    leg_len = lrb.mag(lrb.sub(P['Ankle'], P['Thigh']))
    w = width if width else leg_len * 0.06
    radius = leg_len * 0.05

    # Ribbon rigging lives OUTSIDE the world control, exactly like the bind
    # skeleton: the drivers are constrained in world space, so inheriting the
    # world control as well would apply it twice.
    grp = cmds.group(empty=True, name=prefix + 'ribbon_grp', parent=rig['top'])

    out = {'surfaces': [], 'pins': [], 'joints': [], 'drivers': [], 'mid_ctrls': []}

    segments = [('thighRibbon', 'Thigh', 'Knee', bind[0], bind[1]),
                ('shinRibbon', 'Knee', 'Ankle', bind[1], bind[2])]

    for tag, g0, g1, j0, j1 in segments:
        start, end = P[g0], P[g1]
        aim = lrb.norm(lrb.sub(end, start))
        srf = _make_surface(prefix + tag + '_srf', start, end, n_plane, w,
                            joints_per_segment, grp)

        top = _driver('%s%s_top_drv' % (prefix, tag), start, aim, n_plane, grp, radius)
        mid = _driver('%s%s_mid_drv' % (prefix, tag), lrb.mul(lrb.add(start, end), 0.5),
                      aim, n_plane, grp, radius)
        bot = _driver('%s%s_bot_drv' % (prefix, tag), end, aim, n_plane, grp, radius)

        if tag == 'thighRibbon':
            # The top of the femur must NOT twist with the femur, so the top
            # driver only follows the swing: point to the hip, aim at the knee,
            # up-vector taken from the (non-twisting) hip group.
            cmds.pointConstraint(j0, top, maintainOffset=False)
            cmds.aimConstraint(j1, top, aimVector=(1, 0, 0), upVector=(0, 0, 1),
                               worldUpType='objectrotation', worldUpObject=rig['glob'],
                               worldUpVector=(0, 0, 1), maintainOffset=False)
        else:
            cmds.parentConstraint(j0, top, maintainOffset=False)
        # The bottom driver has to keep THIS segment's frame. A joint's X runs
        # down the NEXT bone, so constraining straight to j1 pointed the shin's
        # bottom driver at the toes (X.aim 0.337, about 70 degrees off) and
        # dragged the mid control half way there with it. Aim back at the top
        # driver so +X stays on this bone, and take the up vector from j1 so
        # the end joint's twist still propagates while its pitch does not bend
        # the segment.
        cmds.pointConstraint(j1, bot, maintainOffset=False)
        cmds.aimConstraint(top, bot, aimVector=(-1, 0, 0), upVector=(0, 0, 1),
                           worldUpType='objectrotation', worldUpObject=j1,
                           worldUpVector=(0, 0, 1), maintainOffset=False)

        mid_grp = cmds.group(empty=True, name='%s%s_mid_grp' % (prefix, tag), parent=grp)
        cmds.pointConstraint(top, bot, mid_grp, maintainOffset=False)
        cmds.orientConstraint(top, bot, mid_grp, maintainOffset=False)
        if mid_ctrl:
            c = cmds.circle(name='%s%s_mid_ctrl' % (prefix, tag), normal=(1, 0, 0),
                            radius=w * 1.6, constructionHistory=False)[0]
            c = cmds.parent(c, mid_grp, relative=True)[0]
            lrb.colour(c, 14)
            cmds.parent(mid, c)
            cmds.setAttr(mid + '.translate', 0, 0, 0)
            cmds.setAttr(mid + '.jointOrient', 0, 0, 0)
            out['mid_ctrls'].append(c)
        else:
            cmds.parent(mid, mid_grp)
            cmds.setAttr(mid + '.translate', 0, 0, 0)
            cmds.setAttr(mid + '.jointOrient', 0, 0, 0)

        _skin_ribbon(srf, [top, mid, bot], start, end)
        # Parent under the segment's own bind joint, so the exported skeleton
        # is a real hierarchy rather than a flat row of pinned joints.
        pin, joints = _pin_joints(prefix, tag, srf, joints_per_segment,
                                  j0, radius * 0.9)

        cmds.setAttr(srf + '.visibility', lock=False)
        cmds.setAttr(srf + '.visibility', 0)
        cmds.setAttr(srf + '.visibility', lock=True)
        for d in (top, mid, bot):
            cmds.setAttr(d + '.visibility', 0)

        out['surfaces'].append(srf)
        out['pins'].append(pin)
        out['joints'] += joints
        out['drivers'] += [top, mid, bot]

    if out['joints']:
        cmds.editDisplayLayerMembers(rig['layers'][0], out['joints'], noRecurse=True)
    out['grp'] = grp
    return out
