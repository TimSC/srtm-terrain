
import events, time, projfunc
import math
import numpy as np

class PhysicsBody():
	def __init__(self):
		self.pos = np.array((0., 0., 0.))
		self.velocity = np.array((0., 0., 0.))
		self.targetPos = None
		self.accel = 0.01
		self.maxSpeed = 0.003
		self.mass = 1.

class Physics(events.EventCallback):
	def __init__(self, mediator):
		super(Physics, self).__init__(mediator)

		mediator.AddListener("physicscreateperson", self)
		mediator.AddListener("physicssetpos", self)
		mediator.AddListener("physicssettargetpos", self)

		self.proj = None
		self.planetCentre = None
		self.reportedPos = {}

		self.objs = {}
		self.prevSpeed = {}

	def AddPlanet(self):
		self.planetCentre = np.array(self.proj.Proj(0., 0., self.proj.UnscaleDistance(-self.proj.radius)))

	def AddSphere(self, pos, objId):
		body = PhysicsBody()
		body.pos = np.array(pos)
		self.objs[objId] = body

	def Update(self, timeElapsed, timeNow):

		#Add motor forces
		for objId in self.objs:
			body = self.objs[objId]
			if body.targetPos is None: continue
			
			#Direction towards target
			targetVec = body.targetPos - body.pos
			dist = np.linalg.norm(targetVec, ord=2)
			targetVecNorm = targetVec.copy()
			if dist > 0.:
				targetVecNorm /= dist

			#Normalise velocity to get direction
			velVec = body.velocity
			speed = np.linalg.norm(velVec, ord=2)
			velVecNorm = velVec.copy()
			if speed > 0.:
				velVecNorm /= speed

			#Check if approaching target
			veldot = np.dot(velVec, targetVecNorm)
			approaching = (veldot >= 0.)
			speedTowardTarg = np.dot(velVec, targetVecNorm)			

			if approaching:
				#Check if braking is needed
				idealSpeedToward = (2. * dist * body.accel) ** 0.5
				safetyMargin = 0.95

				if speedTowardTarg >= idealSpeedToward * safetyMargin:
					braking = True
				else:
					braking = False
			else:
				braking = False

			if braking:
				print "brake"
				#Braking is required
				idealDecelMag = (speedTowardTarg ** 2.) / (2. * dist)
				idealAccel = -targetVecNorm * idealDecelMag
			else:
				print "accel"
				#Calculate force to reduce missing the target
				offTargetVel = velVec - speedTowardTarg * targetVec
				offTargetVelMag = np.linalg.norm(offTargetVel, ord=2)
				offTargetVelNorm = offTargetVel.copy()
				if offTargetVelMag > 0.:
					offTargetVelNorm /= offTargetVelMag
				offTargetAccelReq = - offTargetVelNorm

				#Mix acceleration towards with anti-drift
				idealAccel = offTargetAccelReq + targetVecNorm
				
			#Limit acceleration
			idealAccelMag = np.linalg.norm(idealAccel, ord=2)
			idealAccelScaled = idealAccel.copy()
			if idealAccelMag > body.accel:
				idealAccelScaled /= idealAccelMag
				idealAccelScaled *= body.accel

			print np.linalg.norm(idealAccelScaled, ord=2)
			body.velocity += idealAccelScaled * timeElapsed
			body.pos += body.velocity * timeElapsed

			#idealSpeed = np.array((idealSpeedx, idealSpeedy, idealSpeedz))
			#idealDiff = idealSpeedz - body.pos
			#idealDiffMag = np.linalg.norm(idealDiff, ord=2)
			#if idealDiffMag > 0.:
			#	idealDiff /= idealDiffMag
			#print idealDiff

			#if idealSpeed > velMag:
			#	print "accel", idealSpeed, velMag, timeElapsed
			#	fo = vec * body.mass * accel
			#else:
			#	print "braking", idealSpeed, velMag, timeElapsed
			#	fo = -vel * body.mass * accel

			#if objId in self.prevSpeed:
			#	print (velMag - self.prevSpeed[objId]) / timeElapsed

			#self.prevSpeed[objId] = velMag



		#FIXME remove unused data in self.prevPosLi?

		# Generate events if object has moved
		#for objId in self.objs:
		#	body = self.objs[objId]
		#	pos = body.getPosition()
		#	if objId not in self.reportedPos:
		#		#Position not previously reported
		#		posUpdateEv = events.Event("physicsposupdate")
		#		posUpdateEv.pos = pos
		#		posUpdateEv.objId = objId
		#		self.mediator.Send(posUpdateEv)

		#		self.reportedPos[objId] = pos
		#	else:
		#		prevPos = self.reportedPos[objId]
		#		moveDist = np.linalg.norm(np.array(prevPos) - pos, ord=2)

		#		if moveDist > 0.00001:
		#Position has changed enough to report it
			posUpdateEv = events.Event("physicsposupdate")
			posUpdateEv.pos = body.pos
			posUpdateEv.objId = objId
			self.mediator.Send(posUpdateEv)

		#			self.reportedPos[objId] = pos

	def ProcessEvent(self, event):
		if event.type == "physicscreateperson":
			self.AddSphere(self.proj.ProjDeg(0.,0.,0.), event.objId)
			return

		if event.type == "physicssetpos":
			#print event.type, event.pos
			obj = self.objs[event.objId]
			obj.pos = np.array(event.pos).copy()
			return

		if event.type == "physicssettargetpos":
			obj = self.objs[event.objId]
			obj.targetPos = np.array(event.pos).copy()
			return

		print event.type

if __name__ == "__main__":
	p = Physics(None)
	p.proj = projfunc.ProjFunc()
	p.AddPlanet()

	while(1):
		p.Update(0.01,0.)
		time.sleep(0.01)


