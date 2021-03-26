#
#	CSENode.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	This application creates and updates the CSE Node.
#


from NodeBase import *
from Logging import Logging
from Configuration import Configuration
from resources import BAT
import CSE, Utils
# import psutil 	# type: ignore
import socket, platform, re, uuid, traceback
from Types import ResponseCode as RC, JSON



class CSENode(NodeBase):

	def __init__(self) -> None:
		super().__init__(rn=Configuration.get('app.csenode.nodeRN'),
						 nodeID=Configuration.get('app.csenode.nodeID'),
						 originator=Configuration.get('app.csenode.originator'))
		
		if self.node is None:
			Logging.logErr('CSENode: no node')
			return

		self.lastBTL = -1
		self.lastMMA = -1
		self.batteryLowLevel	= 20
		self.batteryChargedLevel = 100

		self.updateCSEBase()
		self.createBattery()
		self.createMemory()
		self.createDeviceInfo()

		# Add a thread to read and update the content from time to time
		self.startWorker(Configuration.get('app.csenode.interval'), self.nodeWorker, 'nodeWorker')	
		Logging.log('CSENode registered')



	def shutdown(self) -> None:
		super().shutdown()
		Logging.log('CSENode shut down')


	# Set this node as the hosting node for the CSE Base
	def updateCSEBase(self) -> None:
		if (result := self.retrieveResource(ri=CSE.cseCsi)).rsc != RC.OK:
			Logging.logErr('CSENode: cannot retrieve CSEBase')
			return
		dct:JSON = { 'm2m:cb' : {
						'nl' : self.node.ri
					}
				}
		self.updateResource(ri=CSE.cseCsi, data=dct) # ignore result



	#########################################################################
	#
	#	Node capabilities monitoring handling
	#

	def nodeWorker(self) -> bool:
		Logging.logDebug('Updating node data')
		try:
			self._checkBattery()
			self._checkMemory()
			self._checkDeviceInfo()
		except Exception as e:
			Logging.logErr(f'Exception: {traceback.format_exc()}')
			return False
		return True


	#########################################################################
	#
	#	Update Management Objects of the node
	#

	def _checkBattery(self) -> None:
		import psutil 	# type: ignore
		if self.battery is not None:
			if (sensorBat := psutil.sensors_battery()) is not None:
				(percent, _, plugged) = sensorBat
				if percent == self.lastBTL:
					return
				self.lastBTL = percent
				self.battery['btl'] = percent
				self.battery['bts'] = BAT.btsNORMAL
				if percent <= self.batteryLowLevel:
					self.battery['bts'] = BAT.btsLOW_BATTERY
				if plugged is not None and plugged:
					self.battery['bts'] = BAT.btsCHARGING_COMPLETE if percent >= self.batteryChargedLevel else BAT.btsCHARGING
			else:
				self.battery['bts'] = BAT.btsNOT_INSTALLED
			self.updateBattery()


	def _checkMemory(self) -> None:
		import psutil
		if self.memory is not None:
			mmt = psutil.virtual_memory().total
			mma = psutil.virtual_memory().available
			if mma != self.lastMMA:
				self.lastMMA = mma
				self.memory['mmt'] = mmt
				self.memory['mma'] = mma
				self.updateMemory()


	def _checkDeviceInfo(self) -> None:
		if self.deviceInfo is not None:
			try:
				self.deviceInfo['dvnm'] = socket.gethostname()
				self.deviceInfo['osv'] = f'{platform.system()} {platform.release()} {platform.machine()}'
				self.deviceInfo['syst'] = Utils.getResourceDate()
				self.deviceInfo['dlb'] = f'| IP:{socket.gethostbyname(socket.gethostname())} MAC:{":".join(re.findall("..", "%012x" % uuid.getnode()))}'
				self.updateDeviceInfo()
			except Exception as e:
				Logging.logDebug(str(e))
