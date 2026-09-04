"""Parameterised stretchy IK leg builder.

Builds a reverse-foot stretchy IK leg from six guide locators, with a rig
(driver) chain and a bind chain, optional twist/roll joints, and display layers.

Everything is derived from the guide positions: the leg plane, the joint
orientation and the foot frame. No world axis is assumed.

    from modules.rig.Lib import leg_rig_builder as lrb

    guides = {g: cmds.xform(g, q=True, ws=True, t=True)
              for g in lrb.NEEDED}          # Thigh Knee Ankle Ball Toe Heel
    lrb.build_leg('leg_', guides, roll_joints=3)

Library module: imported by rig tools, not run from the toolset UI (no main()).
"""
import math

import maya.cmds as cmds
import maya.api.OpenMaya as om

ORDER = ['Thigh', 'Knee', 'Ankle', 'Ball', 'Toe']
NEEDED = ORDER + ['Heel']


# --------------------------------------------------------------------- vectors
def sub(a, b): return [a[i] - b[i] for i in range(3)]
def add(a, b): return [a[i] + b[i] for i in range(3)]
def mul(a, s): return [v * s for v in a]
def dot(a, b): return sum(a[i] * b[i] for i in range(3))
def cross(a, b): return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]
def mag(a): return math.sqrt(dot(a, a))


def norm(a):
    m = mag(a)
    return [v / m for v in a] if m > 1e-9 else [1.0, 0.0, 0.0]


def inverse_matrix(m):
    return list(om.MMatrix(m).inverse())


# --------------------------------------------------------------------- helpers
def add_attr(node, name, dv=0.0, mn=None, mx=None):
    kw = dict(longName=name, attributeType='double', defaultValue=dv, keyable=True)
    if mn is not None:
        kw['minValue'] = mn
    if mx is not None:
        kw['maxValue'] = mx
    cmds.addAttr(node, **kw)
    return node + '.' + name


def divider(node, name):
    cmds.addAttr(node, longName=name, attributeType='enum', enumName='---', keyable=True)
    cmds.setAttr(node + '.' + name, lock=True)


def negate(name, src):
    n = cmds.createNode('multDoubleLinear', name=name)
    cmds.setAttr(n + '.input2', -1.0)
    cmds.connectAttr(src, n + '.input1')
    return n + '.output'


def colour(node, index):
    cmds.setAttr(node + '.overrideEnabled', 1)
    cmds.setAttr(node + '.overrideColor', index)


def twist_reader(name, joint, ref=None):
    """Angle (deg) that `joint` has twisted about its own X since the rest pose.

    With `ref`, the twist is measured in `ref`'s frame instead (used for the
    shin, whose twist must be read about the knee's bone axis, not the ankle's).
    Returns the plug carrying the angle.
    """
    mm = cmds.createNode('multMatrix', name=name + '_mmx')
    if ref is None:
        rest = inverse_matrix(cmds.getAttr(joint + '.matrix'))
        cmds.connectAttr(joint + '.matrix', mm + '.matrixIn[0]')
        cmds.setAttr(mm + '.matrixIn[1]', rest, type='matrix')
    else:
        cur = om.MMatrix(cmds.getAttr(joint + '.worldMatrix[0]')) * \
              om.MMatrix(cmds.getAttr(ref + '.worldInverseMatrix[0]'))
        # Order matters: restInverse * current, so the delta comes out in
        # `ref`'s frame, whose X runs down the parent bone. current *
        # restInverse expresses it in the joint's own frame instead, whose X
        # points along the NEXT bone, and the extracted twist reads far too
        # small (45% of the true value on this leg).
        cmds.setAttr(mm + '.matrixIn[0]', list(cur.inverse()), type='matrix')
        cmds.connectAttr(joint + '.worldMatrix[0]', mm + '.matrixIn[1]')
        cmds.connectAttr(ref + '.worldInverseMatrix[0]', mm + '.matrixIn[2]')

    dm = cmds.createNode('decomposeMatrix', name=name + '_dcm')
    cmds.connectAttr(mm + '.matrixSum', dm + '.inputMatrix')
    qn = cmds.createNode('quatNormalize', name=name + '_qnorm')
    cmds.connectAttr(dm + '.outputQuatX', qn + '.inputQuatX')
    cmds.connectAttr(dm + '.outputQuatW', qn + '.inputQuatW')
    qe = cmds.createNode('quatToEuler', name=name + '_q2e')
    cmds.connectAttr(qn + '.outputQuat', qe + '.inputQuat')
    return qe + '.outputRotateX'


# ----------------------------------------------------------------------- build
def build_leg(prefix, P, roll_joints=0, ctrl_scale=None):
    for g in NEEDED:
        if g not in P:
            raise RuntimeError('missing guide: ' + g)

    n_plane = norm(cross(sub(P['Knee'], P['Thigh']), sub(P['Ankle'], P['Knee'])))
    axis = norm(sub(P['Ankle'], P['Thigh']))
    v = sub(P['Knee'], P['Thigh'])
    front = norm(sub(v, mul(axis, dot(v, axis))))
    x0 = norm(sub(P['Knee'], P['Thigh']))
    if dot(cross(n_plane, x0), front) < 0:
        n_plane = mul(n_plane, -1)

    leg_len = mag(sub(P['Ankle'], P['Thigh']))
    cs = ctrl_scale if ctrl_scale else leg_len * 0.09

    # ---------------------------------------------------------- joint chains
    def build_chain(suffix, radius):
        cmds.select(clear=True)
        js = [cmds.joint(name='%s%s_%s_jnt' % (prefix, g.lower(), suffix), position=P[g])
              for g in ORDER]
        for i, j in enumerate(js[:-1]):
            aim = norm(sub(P[ORDER[i + 1]], P[ORDER[i]]))
            y = norm(cross(n_plane, aim))
            z = cross(aim, y)
            cmds.xform(j, ws=True, matrix=aim + [0] + y + [0] + z + [0] + P[ORDER[i]] + [1])
            cmds.makeIdentity(j, apply=True, rotate=True, translate=False, scale=False)
        cmds.xform(js[-1], ws=True, t=P[ORDER[-1]])   # end joint drifts on reorient
        cmds.setAttr(js[-1] + '.jointOrient', 0, 0, 0)
        for j in js:
            cmds.setAttr(j + '.radius', radius)
        return js

    bind = build_chain('bind', cs * 0.9)
    rig = build_chain('rig', cs * 0.6)

    # deterministic knee bend direction (guides can be nearly straight)
    jo_z = cmds.getAttr(rig[1] + '.jointOrientZ')
    pa = (-1.0 if jo_z < 0 else 1.0) * max(20.0, abs(jo_z))
    for ch in (rig, bind):
        cmds.setAttr(ch[1] + '.preferredAngleZ', pa)

    # ------------------------------------------------------------ hierarchy
    top = cmds.group(empty=True, name=prefix + 'rig_grp')
    c_global = cmds.curve(name=prefix + 'global_ctrl', degree=1,
                          point=[(-6*cs, 0, -6*cs), (6*cs, 0, -6*cs), (6*cs, 0, 6*cs),
                                 (-6*cs, 0, 6*cs), (-6*cs, 0, -6*cs)])
    cmds.xform(c_global, ws=True, t=[P['Ankle'][0], 0, P['Ankle'][2]])
    cmds.makeIdentity(c_global, apply=True, t=True)
    colour(c_global, 17)
    g_rig = cmds.group(empty=True, name=prefix + 'rig_jnt_grp')
    g_bind = cmds.group(empty=True, name=prefix + 'bind_jnt_grp')
    cmds.parent(c_global, top)
    cmds.parent(g_rig, c_global)
    cmds.parent(g_bind, top)              # bind stays OUT of the world ctrl
    cmds.parent(rig[0], g_rig)
    # Single root joint so the bind skeleton exports as a game skeleton. It is
    # deliberately static: every bind joint is constrained in world space, so
    # animating the root as well would apply the motion twice.
    root = cmds.createNode('joint', name=prefix + 'root_jnt', parent=g_bind)
    cmds.setAttr(root + '.translate', P['Ankle'][0], 0.0, P['Ankle'][2])
    cmds.setAttr(root + '.radius', cs * 1.2)
    cmds.parent(bind[0], root)

    # ------------------------------------------------------------ ik handles
    ikh_leg = cmds.ikHandle(name=prefix + 'ik_hdl', startJoint=rig[0],
                            endEffector=rig[2], solver='ikRPsolver')[0]
    ikh_ball = cmds.ikHandle(name=prefix + 'ball_ik_hdl', startJoint=rig[2],
                             endEffector=rig[3], solver='ikSCsolver')[0]
    ikh_toe = cmds.ikHandle(name=prefix + 'toe_ik_hdl', startJoint=rig[3],
                            endEffector=rig[4], solver='ikSCsolver')[0]
    for h in (ikh_leg, ikh_ball, ikh_toe):
        cmds.setAttr(h + '.visibility', 0)
        cmds.setAttr(h + '.snapEnable', 0)

    # -------------------------------------------------------------- controls
    hx, tx = P['Heel'][0] - cs * 1.5, P['Toe'][0] + cs * 1.5
    gy = min(P['Heel'][1], P['Ball'][1], P['Toe'][1]) - cs * 0.3
    wz = cs * 3.0
    corners = [(hx, gy, P['Ankle'][2] - wz), (tx, gy, P['Ankle'][2] - wz),
               (tx, gy, P['Ankle'][2] + wz), (hx, gy, P['Ankle'][2] + wz),
               (hx, gy, P['Ankle'][2] - wz)]
    c_foot = cmds.curve(name=prefix + 'foot_ik_ctrl', degree=1,
                        point=[tuple(sub(c, P['Ankle'])) for c in corners])
    g_foot = cmds.group(empty=True, name=prefix + 'foot_ik_ctrl_offset_grp')
    cmds.xform(g_foot, ws=True, t=P['Ankle'])
    cmds.parent(c_foot, g_foot, relative=True)      # keeps the ctrl zeroed
    cmds.parent(g_foot, c_global)
    colour(c_foot, 6)

    pv_pos = add(P['Knee'], mul(front, leg_len * 0.55))
    c_pv = cmds.circle(name=prefix + 'pv_ctrl', normal=n_plane, radius=cs * 1.7,
                       constructionHistory=False)[0]
    g_pv = cmds.group(c_pv, name=prefix + 'pv_ctrl_offset_grp')
    cmds.xform(g_pv, ws=True, t=pv_pos)
    cmds.parent(g_pv, c_global)
    colour(c_pv, 6)

    # ----------------------------------------------------------- reverse foot
    fwd = norm(sub(P['Toe'], P['Heel']))
    up = norm(cross(n_plane, fwd))
    FM = fwd + [0] + up + [0] + n_plane + [0]

    def in_frame(d):
        return [dot(d, fwd), dot(d, up), dot(d, n_plane)]

    # ONE static group carries the foot-frame orientation. The pivot groups
    # inside it stay identity-rotated on purpose: their rotateZ / rotateY get
    # driven by the roll attributes further down, and a connection writes the
    # source value straight over whatever orientation was sitting on that
    # channel. Storing the frame on the driven groups loses it the moment the
    # first roll connection is made, which silently rotates the whole foot.
    frame_euler = [math.degrees(a) for a in
                   om.MTransformationMatrix(om.MMatrix(FM + [0, 0, 0, 1])).rotation()]
    g_frame = cmds.group(empty=True, name=prefix + 'footFrame_grp', parent=c_foot)
    cmds.setAttr(g_frame + '.translate', *sub(P['Heel'], P['Ankle']))
    cmds.setAttr(g_frame + '.rotate', *frame_euler)

    def pivot(name, local, parent):
        g = cmds.group(empty=True, name=prefix + name, parent=parent)
        cmds.setAttr(g + '.translate', *local)
        return g

    g_heel = pivot('heelPivot_grp', [0.0, 0.0, 0.0], g_frame)
    g_toe = pivot('toePivot_grp', in_frame(sub(P['Toe'], P['Heel'])), g_heel)
    g_ball = pivot('ballRoll_grp', in_frame(sub(P['Ball'], P['Toe'])), g_toe)
    g_wig = pivot('toeWiggle_grp', in_frame(sub(P['Ball'], P['Toe'])), g_toe)
    for h, par in ((ikh_leg, g_ball), (ikh_ball, g_ball), (ikh_toe, g_wig)):
        cmds.parent(h, par)
    cmds.poleVectorConstraint(c_pv, ikh_leg)

    # ikHandle() drops the handle on the *solved* effector, which is not the
    # guide when the chain is near-straight, so pin each handle to its guide.
    # Set the LOCAL translate against the known foot frame rather than using a
    # world-space xform: inside one script block the parent matrices are stale,
    # so a world-space set reads back correct and is then undone by the next
    # real evaluation.
    def foot_local(target, origin=P['Ball']):
        return in_frame(sub(target, origin))

    for h, g in ((ikh_leg, 'Ankle'), (ikh_ball, 'Ball'), (ikh_toe, 'Toe')):
        cmds.setAttr(h + '.translate', *foot_local(P[g]))

    # ------------------------------------------------------------ foot attrs
    divider(c_foot, 'FOOT')
    a_roll = add_attr(c_foot, 'roll')
    a_break = add_attr(c_foot, 'rollBreak', 35.0, 0.0, 90.0)
    a_wiggle = add_attr(c_foot, 'toeWiggle')
    a_hpiv = add_attr(c_foot, 'heelPivot')
    a_tpiv = add_attr(c_foot, 'toePivot')
    a_bpiv = add_attr(c_foot, 'ballPivot')
    a_twist = add_attr(c_foot, 'kneeTwist')

    cl_heel = cmds.createNode('clamp', name=prefix + 'heelRoll_clamp')
    cmds.setAttr(cl_heel + '.minR', -360)
    cmds.setAttr(cl_heel + '.maxR', 0)
    cmds.connectAttr(a_roll, cl_heel + '.inputR')
    cl_ball = cmds.createNode('clamp', name=prefix + 'ballRoll_clamp')
    cmds.setAttr(cl_ball + '.minR', 0)
    cmds.connectAttr(a_break, cl_ball + '.maxR')
    cmds.connectAttr(a_roll, cl_ball + '.inputR')
    sub_toe = cmds.createNode('plusMinusAverage', name=prefix + 'toeRoll_sub')
    cmds.setAttr(sub_toe + '.operation', 2)
    cmds.connectAttr(a_roll, sub_toe + '.input1D[0]')
    cmds.connectAttr(a_break, sub_toe + '.input1D[1]')
    cl_toe = cmds.createNode('clamp', name=prefix + 'toeRoll_clamp')
    cmds.setAttr(cl_toe + '.minR', 0)
    cmds.setAttr(cl_toe + '.maxR', 360)
    cmds.connectAttr(sub_toe + '.output1D', cl_toe + '.inputR')

    cmds.connectAttr(negate(prefix + 'heelRoll_neg', cl_heel + '.outputR'), g_heel + '.rotateZ')
    cmds.connectAttr(negate(prefix + 'ballRoll_neg', cl_ball + '.outputR'), g_ball + '.rotateZ')
    cmds.connectAttr(negate(prefix + 'toeRoll_neg', cl_toe + '.outputR'), g_toe + '.rotateZ')
    cmds.connectAttr(a_wiggle, g_wig + '.rotateZ')
    cmds.connectAttr(a_hpiv, g_heel + '.rotateY')
    cmds.connectAttr(a_tpiv, g_toe + '.rotateY')
    cmds.connectAttr(a_bpiv, g_ball + '.rotateY')
    cmds.connectAttr(a_twist, ikh_leg + '.twist')

    # ---------------------------------------------------------------- stretch
    rest_thigh = cmds.getAttr(rig[1] + '.translateX')
    rest_shin = cmds.getAttr(rig[2] + '.translateX')
    rest_len = rest_thigh + rest_shin
    divider(c_foot, 'STRETCH')
    a_stretch = add_attr(c_foot, 'stretch', 1.0, 0.0, 1.0)

    loc_s = cmds.spaceLocator(name=prefix + 'stretch_start_loc')[0]
    cmds.xform(loc_s, ws=True, t=P['Thigh'])
    cmds.parent(loc_s, g_rig)
    loc_e = cmds.spaceLocator(name=prefix + 'stretch_end_loc')[0]
    cmds.parent(loc_e, g_ball, relative=True)
    cmds.setAttr(loc_e + '.translate', *foot_local(P['Ankle']))
    for l in (loc_s, loc_e):
        cmds.setAttr(l + '.visibility', 0)

    dist = cmds.createNode('distanceBetween', name=prefix + 'stretch_dist')
    cmds.connectAttr(loc_s + '.worldMatrix[0]', dist + '.inMatrix1')
    cmds.connectAttr(loc_e + '.worldMatrix[0]', dist + '.inMatrix2')
    gnorm = cmds.createNode('multiplyDivide', name=prefix + 'stretch_globalNorm')
    cmds.setAttr(gnorm + '.operation', 2)
    cmds.connectAttr(dist + '.distance', gnorm + '.input1X')
    cmds.connectAttr(c_global + '.scaleY', gnorm + '.input2X')
    factor = cmds.createNode('multiplyDivide', name=prefix + 'stretch_factor')
    cmds.setAttr(factor + '.operation', 2)
    cmds.connectAttr(gnorm + '.outputX', factor + '.input1X')
    cmds.setAttr(factor + '.input2X', rest_len)
    cond = cmds.createNode('condition', name=prefix + 'stretch_cond')
    cmds.setAttr(cond + '.operation', 2)
    cmds.connectAttr(gnorm + '.outputX', cond + '.firstTerm')
    cmds.setAttr(cond + '.secondTerm', rest_len)
    cmds.connectAttr(factor + '.outputX', cond + '.colorIfTrueR')
    cmds.setAttr(cond + '.colorIfFalseR', 1.0)
    blend = cmds.createNode('blendTwoAttr', name=prefix + 'stretch_blend')
    cmds.setAttr(blend + '.input[0]', 1.0)
    cmds.connectAttr(cond + '.outColorR', blend + '.input[1]')
    cmds.connectAttr(a_stretch, blend + '.attributesBlender')
    seg = cmds.createNode('multiplyDivide', name=prefix + 'stretch_segments')
    cmds.setAttr(seg + '.input1X', rest_thigh)
    cmds.setAttr(seg + '.input1Y', rest_shin)
    cmds.connectAttr(blend + '.output', seg + '.input2X')
    cmds.connectAttr(blend + '.output', seg + '.input2Y')
    cmds.connectAttr(seg + '.outputX', rig[1] + '.translateX')
    cmds.connectAttr(seg + '.outputY', rig[2] + '.translateX')

    # ------------------------------------------------------- rig drives bind
    for r, b in zip(rig, bind):
        cmds.parentConstraint(r, b, maintainOffset=False)
        cmds.scaleConstraint(r, b, maintainOffset=False)

    # ----------------------------------------------------------- roll joints
    rolls = []
    if roll_joints:
        n = int(roll_joints)
        # thigh: counter-rotate the femur twist so the hip end stays put
        tw_thigh = twist_reader(prefix + 'thighTwist', bind[0])
        for i in range(n):
            t = i / float(n)                       # 0 .. (n-1)/n
            j = cmds.createNode('joint', name='%sthighRoll%02d_bind_jnt' % (prefix, i + 1),
                                parent=bind[0])
            cmds.setAttr(j + '.radius', cs * 0.7)
            md = cmds.createNode('multDoubleLinear', name='%sthighRoll%02d_pos' % (prefix, i + 1))
            cmds.setAttr(md + '.input2', t)
            cmds.connectAttr(seg + '.outputX', md + '.input1')
            cmds.connectAttr(md + '.output', j + '.translateX')
            mw = cmds.createNode('multDoubleLinear', name='%sthighRoll%02d_tw' % (prefix, i + 1))
            cmds.setAttr(mw + '.input2', -(1.0 - t))
            cmds.connectAttr(tw_thigh, mw + '.input1')
            cmds.connectAttr(mw + '.output', j + '.rotateX')
            rolls.append(j)
        # shin: follow the ankle twist, measured about the knee's bone axis
        tw_shin = twist_reader(prefix + 'shinTwist', bind[2], ref=bind[1])
        for i in range(n):
            t = (i + 1) / float(n)                 # 1/n .. 1
            j = cmds.createNode('joint', name='%sshinRoll%02d_bind_jnt' % (prefix, i + 1),
                                parent=bind[1])
            cmds.setAttr(j + '.radius', cs * 0.7)
            md = cmds.createNode('multDoubleLinear', name='%sshinRoll%02d_pos' % (prefix, i + 1))
            cmds.setAttr(md + '.input2', t)
            cmds.connectAttr(seg + '.outputY', md + '.input1')
            cmds.connectAttr(md + '.output', j + '.translateX')
            mw = cmds.createNode('multDoubleLinear', name='%sshinRoll%02d_tw' % (prefix, i + 1))
            cmds.setAttr(mw + '.input2', t)
            cmds.connectAttr(tw_shin, mw + '.input1')
            cmds.connectAttr(mw + '.output', j + '.rotateX')
            rolls.append(j)

    # --------------------------------------------------------------- layers
    l_bind = cmds.createDisplayLayer(name=prefix + 'bind_lyr', empty=True)
    l_rig = cmds.createDisplayLayer(name=prefix + 'rig_lyr', empty=True)
    cmds.editDisplayLayerMembers(l_bind, [root] + bind + rolls, noRecurse=True)
    cmds.editDisplayLayerMembers(l_rig, rig + [ikh_leg, ikh_ball, ikh_toe], noRecurse=True)
    cmds.setAttr(l_bind + '.color', 6)
    cmds.setAttr(l_rig + '.color', 17)
    cmds.setAttr(l_rig + '.visibility', 0)

    for c in (c_foot, c_pv):
        for a in ('scaleX', 'scaleY', 'scaleZ', 'visibility'):
            cmds.setAttr(c + '.' + a, lock=True, keyable=False, channelBox=False)
    for a in ('rotateX', 'rotateY', 'rotateZ'):
        cmds.setAttr(c_pv + '.' + a, lock=True, keyable=False, channelBox=False)

    return dict(top=top, glob=c_global, foot=c_foot, pv=c_pv, rig=rig, bind=bind,
                bind_grp=g_bind, rig_grp=g_rig, root=root,
                rolls=rolls, ik=(ikh_leg, ikh_ball, ikh_toe), stretch_nodes=dict(
                    dist=dist, cond=cond, blend=blend, seg=seg),
                rest_len=rest_len, plane=n_plane, front=front,
                layers=(l_bind, l_rig))
