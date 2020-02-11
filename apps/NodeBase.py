#
#	NodeBase.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	This base class should be used to create nodes for applications. It provides
#	many utility methods like registering with the CSE etc.
#

from AppBase import AppBase
from Configuration import Configuration
from Constants import Constants as C
import CSE, Utils
from resources import BAT

# TODO support further specializations


class NodeBase(AppBase):
				
	def __init__(self, rn,  nodeID, originator):
		super().__init__(rn, originator)
		self.batRn		= self.srn + '/battery'
		self.memRn		= self.srn + '/memory'
		self.dviRn 		= self.srn + '/deviceinfo'
		self.node 		= None
		self.battery 	= None
		self.memory 	= None
		self.deviceInfo = None

		# First check whether node exists and create it if necessary
		self.node = self.retrieveCreate(srn=self.srn,
										jsn={ C.tsNOD : {
											'rn' : self.rn,
											'ni' : nodeID
											}
										},
										ty=C.tNOD)


	def shutdown(self):
		super().shutdown()


	#########################################################################
	#
	#	MgmtObj: Battery
	#

	def createBattery(self):
		self.battery = self.retrieveCreate( srn=self.batRn,
											jsn={ 'm2m:bat' : {
												'mgd' : C.mgdBAT,
												'dc' : 'battery',
												'rn' : 'battery',
												'btl': 0,
												'bts': BAT.btsUNKNOWN
												}
											}
										  )


	def updateBattery(self):
		if self.battery is not None:
			(n, rc) = self.updateResource(ri=self.battery.ri, jsn=self.battery.asJSON(update=True, noACP=True))


	#########################################################################
	#
	#	MgmtObj: Memory
	#

	def createMemory(self):
		self.memory = self.retrieveCreate(	srn=self.memRn,
											jsn={ 'm2m:mem' : {
												'mgd' : C.mgdMEM,
												'dc' : 'memory',
												'rn' : 'memory',
												'mma': 0,
												'mmt': 0
												}
											}
										  )


	def updateMemory(self):
		if self.memory is not None:
			(n, rc) = self.updateResource(ri=self.memory.ri, jsn=self.memory.asJSON(update=True, noACP=True))


	#########################################################################
	#
	#	MgmtObj: DeviceInfo
	#

	def createDeviceInfo(self):
		self.deviceInfo = self.retrieveCreate(	srn=self.dviRn, 
												jsn={ 'm2m:dvi' : {
													'mgd' : C.mgdDVI,
													'dc' : 'deviceInfo',
													'rn' : 'deviceinfo',
													'dlb': [],
													'dvnm': '',
													'osv': '',
													'syst': Utils.getResourceDate()
													}
												}
											 )

	def updateDeviceInfo(self):
		if self.memory is not None:
			(n, rc) = self.updateResource(ri=self.deviceInfo.ri, jsn=self.deviceInfo.asJSON(update=True, noACP=True))


