#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2011, Florent Lamiraux, Thomas Moulard, JRL, CNRS/AIST
#
# This file is part of dynamic-graph.
# dynamic-graph is free software: you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public License
# as published by the Free Software Foundation, either version 3 of
# the License, or (at your option) any later version.
#
# dynamic-graph is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Lesser Public License for more details.  You should have
# received a copy of the GNU Lesser General Public License along with
# dynamic-graph. If not, see <http://www.gnu.org/licenses/>.

print("Run legs_follower_graph.py  v2.0.")
import time

from dynamic_graph import plug

print "import from sot.core"
from dynamic_graph.sot.core import FeatureGeneric, FeaturePosture, Task, MatrixConstant, RobotSimu

print "import from sot.motion_planner"
from dynamic_graph.sot.motion_planner import LegsFollower, PostureError, LegsError, WaistError

print "import TracerRealTime"
from dynamic_graph.tracer_real_time import TracerRealTime


#./sot-dynamic/_build-Release/src/dynamic_graph/sot/dynamics/hrp2.py: have been modified

halfSitting = (0.0, 0.0, 0.648702, 0.0, 0.0, 0.0,
 0.0, 0.0, -0.45378600000000002, 0.87266500000000002, -0.418879, 0.0,
 0.0, 0.0, -0.45378600000000002, 0.87266500000000002, -0.418879, 0.0,
 0.0, 0.0,
 0.0, 0.0,
 0.60039, -0.17453, 0.0, -1.75057, 0.0, 0.0, 0.09948,
 0.60039, 0.17453, 0.0, -1.75057, 0.0, 0.0, 0.09948)
#0.261799, -0.17452999999999999, 0.0, -0.52359900000000004, 0.0, 0.0, 0.10000000000000001,
#0.261799, 0.17452999999999999, 0.0, -0.52359900000000004, 0.0, 0.0, 0.10000000000000001)


def oneVector(i,statelength):
    r = [0.,] * statelength
    r[i] = 1.
    return tuple(r)

def zeroVector(statelength):
    r = [0.,] * statelength
    return tuple(r)

class LegsFollowerGraph(object):

    legsFollower = None

    postureTask = None
    postureFeature = None
    postureFeatureDes = None
    postureError = None

    legsTask = None
    legsFeature = None
    legsFeatureDes = None
    legsError = None

    waistTask = None
    waistFeature = None
    waistFeatureDes = None
    waistError = None

    trace = None

    def __init__(self, robot, solver, trace = None, postureTaskDofs = None):
        print("Constructor of LegsFollower Graph")
        self.robot = robot
        self.solver = solver
	self.legsFollower = LegsFollower('legs-follower')
        self.statelength = len(robot.device.state.value)

 	# Initialize the posture task.
	print("Posture Task")
        self.postureTaskDofs = postureTaskDofs
        if not self.postureTaskDofs:
            self.postureTaskDofs = []
            for i in xrange(len(robot.halfSitting) - 6):
                # Disable legs dofs.
                if i < 12: #FIXME: not generic enough
                    self.postureTaskDofs.append((i + 6, False))
                else:
                    self.postureTaskDofs.append((i + 6, True))
        
        # This part is taken from feet_follower_graph
        self.postureTask = Task(self.robot.name + '_posture')
        
        self.postureFeature = FeaturePosture(self.robot.name + '_postureFeature')
        plug(self.robot.device.state, self.postureFeature.state)

        posture = list(self.robot.halfSitting)
        self.postureFeature.setPosture(tuple(posture))
        for (dof, isEnabled) in self.postureTaskDofs:
            self.postureFeature.selectDof(dof, isEnabled)
        self.postureTask.add(self.postureFeature.name)
        self.postureTask.controlGain.value = 2.

	# Initialize the waist follower task.
	print("Waist Task")
        self.robot.features['waist'].selec.value = '111111'
        plug(self.legsFollower.waist, self.robot.features['waist'].reference)
        self.robot.tasks['waist'].controlGain.value = 1.

	# Initialize the legs follower task.
	print("Legs Task")
        self.legsTask = Task(self.robot.name + '_legs')
        self.legsFeature = FeatureGeneric(self.robot.name + '_legsFeature')
        legsFeatureDesName = self.robot.name + '_legsFeatureDes'
        self.legsFeatureDes = FeatureGeneric(legsFeatureDesName)
        self.legsError = LegsError('LegsError')
        plug(self.robot.device.state, self.legsError.state)

        # self.legsFeatureDes.errorIN.value = self.legsFollower.ldof.value        
        plug(self.legsFollower.ldof,self.legsFeatureDes.errorIN)
        self.legsFeature.jacobianIN.value = self.legsJacobian()

        self.legsFeature.setReference(legsFeatureDesName)
        plug(self.legsError.error, self.legsFeature.errorIN)            

        self.legsTask.add(self.legsFeature.name)
        self.legsTask.controlGain.value = 5.

	#CoM task
        print("Com Task")
        print (0., 0., self.robot.dynamic.com.value[2])
	self.robot.comTask.controlGain.value = 50.
        self.robot.featureComDes.errorIN.value =  (0., 0., self.robot.dynamic.com.value[2])
        self.robot.featureCom.selec.value = '111'
	plug(self.legsFollower.com, self.robot.featureComDes.errorIN)

        # Plug the legs follower zmp output signals.
        plug(self.legsFollower.zmp, self.robot.device.zmp)


	solver.sot.remove(self.robot.comTask.name)

	print("Push in solver.")
        solver.sot.push(self.legsTask.name)
        solver.sot.push(self.postureTask.name)
	solver.sot.push(self.robot.tasks['waist'].name)
        solver.sot.push(self.robot.comTask.name)
        
        solver.sot.remove(self.robot.tasks['left-ankle'].name)
	solver.sot.remove(self.robot.tasks['right-ankle'].name)


	print solver.sot.display()

        print("Tasks added in solver.\n")
	print("Command are : \n - f.plug()\n - f.plugViewer()\n - f.plugPlanner()\n"
              " - f.plugPlannerWithoutMocap()\n - f.start()\n - f.stop()\n - f.readMocap()\n")


    def legsJacobian(self):
        j = []
        for i in xrange(12):
            j.append(oneVector(6+i,self.statelength)) 
        return tuple(j)

    def waistJacobian(self):
        j = []
        for i in xrange(6):
            j.append(oneVector(i,self.statelength)) 
        return tuple(j)

    def postureJacobian(self):
        j = []
        for i in xrange(self.statelength):
            if i >= 6 + 2 * 6:
                j.append(oneVector(i))
            if i == 3 or i == 4:
                j.append(zeroVector())
        return tuple(j)

    def computeDesiredValue(self):
        e = self.robot.halfSitting
        #e = halfSitting
        e_ = [e[3], e[4]]
        offset = 6 + 2 * 6
        for i in xrange(len(e) - offset):
            e_.append(e[offset + i])
        return tuple(e_)
    
    def canStart(self):
        securityThreshold = 1e-3
        return (self.postureTask.error.value <=
                (securityThreshold,) * len(self.postureTask.error.value))

    def setupTrace(self):
	self.trace = TracerRealTime('trace')
	self.trace.setBufferSize(2**20)
	self.trace.open('/tmp/','legs_follower_','.dat')
	
	self.trace.add('legs-follower.com', 'com')
	self.trace.add('legs-follower.zmp', 'zmp')
	self.trace.add('legs-follower.ldof', 'ldof')
	self.trace.add('legs-follower.waist', 'waist')
	self.trace.add(self.robot.device.name + '.state', 'state')
	self.trace.add(self.legsTask.name + '.error', 'errorLegs')
        self.trace.add(self.robot.comTask.name + '.error', 'errorCom')

        #self.trace.add('legs-follower.outputStart','start')
        #self.trace.add('legs-follower.outputYaw','yaw')
        self.trace.add('corba.planner_steps','steps')
        self.trace.add('corba.planner_outputGoal','goal')
        self.trace.add('corba.waist','waistMocap')
	self.trace.add('corba.left-foot','footMocap')
        self.trace.add('corba.table','tableMocap')
        self.trace.add('corba.bar','barMocap')
        self.trace.add('corba.chair','chairMocap')
	self.trace.add('corba.helmet','helmetMocap')
	self.trace.add('corba.planner_outputObs','obstacles')

        self.trace.add(self.robot.dynamic.name + '.left-ankle',
                       self.robot.dynamic.name + '-left-ankle')
        self.trace.add(self.robot.dynamic.name + '.right-ankle',
                       self.robot.dynamic.name + '-right-ankle')


	# Recompute trace.triger at each iteration to enable tracing.
	self.robot.device.after.addSignal('legs-follower.zmp')
	self.robot.device.after.addSignal('legs-follower.outputStart')
	self.robot.device.after.addSignal('legs-follower.outputYaw')
        self.robot.device.after.addSignal(self.robot.dynamic.name + '.left-ankle')
	self.robot.device.after.addSignal(self.robot.dynamic.name + '.right-ankle')
	self.robot.device.after.addSignal('trace.triger')
	return

    def plugPlanner(self):
        print("Plug planner.")
	plug(corba.planner_radQ, self.legsFollower.inputRef)
	plug(self.legsFollower.outputStart, corba.planner_inputStart)
	return

    def plugPlannerWithoutMocap(self):
        print("Plug planner without mocap.")
	#plug(corba.planner_radQ, self.legsFollower.inputRef)
	plug(self.legsFollower.outputStart, corba.planner_inputStart)
	return

    def plugViewer(self):
        print("Plug viewer.")
	return

    def plug(self):
	self.plugPlanner()
	self.plugViewer()
	return

    def readMocap(self):
	return;

    def start(self):
        if not self.canStart():
            print("Robot has not yet converged to the initial position,"
                  " please wait and try again.")
            return

        print("Start.")
	self.postureTask.controlGain.value = 180.
        #self.waistTask.controlGain.value = 90.
	self.legsTask.controlGain.value = 180.
	self.robot.comTask.controlGain.value = 180.
	self.robot.tasks['waist'].controlGain.value = 45.

	self.setupTrace()
	self.trace.start()
        self.legsFollower.start()
	return

    def stop(self):
	self.legsFollower.stop()
	self.trace.dump()
	return
