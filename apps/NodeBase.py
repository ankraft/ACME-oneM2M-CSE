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
from resources.Resource import Resource


# TODO support further specializations


class NodeBase(AppBase):
				
	def __init__(self, rn: str,  nodeID: str, originator: str) -> None:
		super().__init__(rn, originator)
		self.batRn					= self.srn + '/battery'
		self.memRn					= self.srn + '/memory'
		self.dviRn 					= self.srn + '/deviceinfo'
		self.node:Resource 			= None
		self.battery:Resource 		= None
		self.memory:Resource 		= None
		self.deviceInfo:Resource	= None

		# First check whether node exists and create it if necessary
		self.node = self.retrieveCreate(srn=self.srn,
										jsn={ C.tsNOD : {
											'rn' : self.rn,
											'ni' : nodeID
											}
										},
										ty=C.tNOD)


	def shutdown(self) -> None:
		super().shutdown()


	#########################################################################
	#
	#	MgmtObj: Battery
	#

	def createBattery(self) -> None:
		self.battery = self.retrieveCreate( srn=self.batRn,
											jsn={ 'm2m:bat' : {
												'mgd' : C.mgdBAT,
												'dc'  : 'battery',
												'rn'  : 'battery',
												'btl' : 0,
												'bts' : BAT.btsUNKNOWN
												}
											}
										  )


	def updateBattery(self) -> None:
		if self.battery is not None:
			self.updateResource(ri=self.battery.ri, jsn=self.battery.asJSON(update=True, noACP=True))


	#########################################################################
	#
	#	MgmtObj: Memory
	#

	def createMemory(self) -> None:
		self.memory = self.retrieveCreate(	srn=self.memRn,
											jsn={ 'm2m:mem' : {
												'mgd' : C.mgdMEM,
												'dc'  : 'memory',
												'rn'  : 'memory',
												'mma' : 0,
												'mmt' : 0
												}
											}
										  )


	def updateMemory(self) -> None:
		if self.memory is not None:
			self.updateResource(ri=self.memory.ri, jsn=self.memory.asJSON(update=True, noACP=True))


	#########################################################################
	#
	#	MgmtObj: DeviceInfo
	#

	def createDeviceInfo(self) -> None:
		self.deviceInfo = self.retrieveCreate(	srn=self.dviRn, 
												jsn={ 'm2m:dvi' : {
													'mgd' : C.mgdDVI,
													'dc'  : 'deviceInfo',
													'rn'  : 'deviceinfo',
													'dlb' : '',
													'dty' : '',
													'dvnm': '',
													'man' : '',
													'mod' : '',
													'osv' : '',
													'syst': Utils.getResourceDate()
													}
												}
											 )

	def updateDeviceInfo(self) -> None:
		if self.memory is not None:
			self.updateResource(ri=self.deviceInfo.ri, jsn=self.deviceInfo.asJSON(update=True, noACP=True))


