#
#	AEBase.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	This base class should be used to create applications. It provides
#	many utility methods like registering with the CSE etc.
#

from typing import Any
from AppBase import AppBase
from NodeBase import NodeBase
from Configuration import Configuration
from Constants import Constants as C
import CSE, Utils
import json


class AEBase(AppBase):
				
	def __init__(self, rn: str, api: str, originator: str = None, nodeRN: str = None, nodeID: str = None, nodeOriginator: str = None) -> None:
		super().__init__(rn, originator)
		self.rn 			= rn
		self.originator 	= originator
		self.ae 			= None
		self.aeNodeBase 	= None
		self.appData: dict	= None

		# Get or create the hosting node
		if nodeRN is not None and nodeID is not None:
			self.aeNode = NodeBase(nodeRN, nodeID, nodeOriginator)

		# Try to get the application data and the origionator
		self.originator = self.getAppData('_originator', originator)

		# Get or create the AE resource
		self.ae = self.retrieveCreate(	srn=self.srn,
										jsn={ C.tsAE : {
											'rn' : self.rn,
											'api' : api,
											'nl' : self.aeNode.node.ri if self.aeNode.node is not None else None,
											'poa' : [ Configuration.get('http.address') ],
											'rr' : True,
											'srv' : [ "3", "4" ]
											}
										},
										ty=C.tAE)


		# assign as originator the assigned aei attribute

		self.originator = Utils.findXPath(self.ae, "aei") if self.ae is not None else None

		# Store updated application data
		self.setAppData('_originator', self.originator)

		# assign as acpi to use the first assigned acpi
		self.acpi = Utils.findXPath(self.ae, "acpi")[0] if self.ae is not None else None


	def shutdown(self) -> None:
		super().shutdown()


	def clean(self) -> None:
		self.shutdown()
		self.removeAppData()

	#########################################################################
	#
	#	Persistent Application Data
	#


	# retrieve application data. If not found, initialize and store a record
	def retrieveAppData(self) -> dict:
		if (result := CSE.storage.getAppData(self.rn)) is None:
			self.appData = 	{ 'id': self.rn,
							  '_originator': self.originator
							}
			self.storeAppData()
		else:
			self.appData = result
		return self.appData


	def storeAppData(self) -> bool:
		return CSE.storage.updateAppData(self.appData)


	def removeAppData(self) -> bool:
		result = CSE.storage.removeAppData(self.appData)
		self.AppData = None
		return result

	def setAppData(self, key: str, value: Any) -> bool:
		self.appData[key] = value
		return self.storeAppData()


	def getAppData(self, key: str, default: Any = None) -> Any:
		if self.appData is None:
			self.retrieveAppData()
		return self.appData[key] if key in self.appData else default




