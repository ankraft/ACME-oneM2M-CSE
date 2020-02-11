#
#	AEBase.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	This base class should be used to create applications. It provides
#	many utility methods like registering with the CSE etc.
#

from AppBase import AppBase
from NodeBase import NodeBase
from Configuration import Configuration
from Constants import Constants as C
import CSE, Utils
import json


class AEBase(AppBase):
				
	def __init__(self, rn, api, aei, acpri=None, originator=None, nodeRN=None, nodeID=None):
		super().__init__(rn, originator)
		self.ae 			= None
		self.aeNodeBase 	= None

		# Get or create the hosting node
		if nodeRN is not None and nodeID is not None:
			self.aeNode = NodeBase(nodeRN, nodeID, originator)

		# Get or create the AE resource
		self.ae = self.retrieveCreate(	srn=self.srn,
										jsn={ C.tsAE : {
											'rn' : self.rn,
											'api' : api,
											'aei' : aei,
											'nl' : self.aeNode.node.ri if self.aeNode.node is not None else None,
											'acpi' : [ 
												acpri if acpri is not None else Configuration.get('cse.defaultACPRI')
											],
											'poa' : Configuration.get('http.address')
											}
										},
										ty=C.tAE)


	def shutdown(self):
		super().shutdown()
