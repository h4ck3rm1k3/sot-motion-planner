#!/usr/bin/env python
#
# This script computes the error drift, i.e. the planned robot position w.r.t
# to the real one.
#
# Practically speaking, this uses three transformations:
# (1) /plan -> /base_link - planning
# (2) /map -> /base_link - map
# (3) /world -> /base_link - control
#
# (1) is the initial movement computed during the planning phase.
# We want to follow this plan as precisely as possible.
#
# (2) is the perceived movement computed by the localization node.
# It takes into account the feedback on the movement execution
# and the drift / errors in the execution.
#
# (3) is the robot position in the control framework, it takes into
# account the correction but not the drift.
# If no correction is applied, it is equal to the planning frame.
#
# We use tf to retrieve these information and realize the following
# computation:
#
# \hat{bl} M bl = \hat{bl} M w . w M bl
#
# \hat{bl} M w is (2)^{-1} and w M bl is (1)
#
# From \hat{bl} M bl, the X, Y and raw components are extracted and
# streamed.


from __future__ import print_function

from math import atan2
import numpy as np
import roslib; roslib.load_manifest('dynamic_graph_bridge')
import rospy

import tf
from geometry_msgs.msg import Vector3Stamped

from tf.transformations import quaternion_from_matrix, \
    translation_from_matrix, quaternion_from_matrix

rospy.init_node('error_estimator')


# Frame ids.
baseLinkMapFrameId = rospy.get_param(
    '~base_link_map_frame_id', '/mocap_world/left_foot/origin') #FIXME:
baseLinkPlanFrameId = rospy.get_param(
    '~base_link_plan_frame_id', '/plan_left_ankle') #FIXME:
mapFrameId = rospy.get_param('~map_frame_id', '/world')
planFrameId = rospy.get_param('~plan_frame_id', '/world')

tr = tf.TransformerROS()
tl = tf.TransformListener()

pub = rospy.Publisher('error', Vector3Stamped)
error = Vector3Stamped()
error.header.seq = 0
error.header.frame_id = baseLinkPlanFrameId


ok = False
rospy.loginfo("Waiting for frames...")
rate = rospy.Rate(10.0)
t = rospy.Time(0)
while not ok and not rospy.is_shutdown():
    try:
        tl.waitForTransform(
            planFrameId, baseLinkPlanFrameId,
            t, rospy.Duration(0.1))
        tl.waitForTransform(
            mapFrameId, baseLinkMapFrameId,
            t, rospy.Duration(0.1))
        ok = True
    except tf.Exception as e:
        rospy.logdebug("error while waiting for frames: {0}".format(e))
        ok = False
        rate.sleep()
if rospy.is_shutdown():
    sys.exit(0)

rospy.loginfo("start streaming execution error")

while not rospy.is_shutdown():
    rospy.sleep(0.01)
    t = rospy.Time()
    try:
        (wMhbl_q, wMhbl_t) = tl.lookupTransform(mapFrameId,
                                                baseLinkMapFrameId,
                                                t)
    except:
        rospy.logwarn("failed to retrieve {0} position w.r.t. the {1} frame".format(
                baseLinkMapFrameId, mapFrameId))
        continue
    try:
        (wMbl_q, wMbl_t) = tl.lookupTransform(planFrameId,
                                              baseLinkPlanFrameId,
                                              t)
    except:
        rospy.logwarn("failed to retrieve {0} position w.r.t. the {1} frame".format(
                baseLinkPlanFrameId, planFrameId))
        continue

    wMhbl = np.matrix(tr.fromTranslationRotation(wMhbl_q, wMhbl_t))

    wMbl = np.matrix(tr.fromTranslationRotation(wMbl_q, wMbl_t))

    hblMbl = np.linalg.inv(wMhbl) * wMbl

    error.header.seq += 1
    error.header.stamp = rospy.Time.now()
    error.vector.x = hblMbl[0, 3]
    error.vector.y = hblMbl[1, 3]
    error.vector.z = atan2(hblMbl[1, 0], hblMbl[0, 0]) #FIXME: double check this

    pub.publish(error)
