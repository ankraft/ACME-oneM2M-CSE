#
#	CSEBase.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: CSEBase
#

from __future__ import annotations
from typing import Optional

from ..etc.Types import AttributePolicyDict, CSERequest, ResourceTypes, ContentSerializationType, Result, JSON
from ..etc import Utils
from ..resources.Resource import Resource
from ..resources.AnnounceableResource import AnnounceableResource
from ..services import CSE
from ..services.Logging import Logging as L

# TODO notificationCongestionPolicy

class CSEBase(AnnounceableResource):

	# Specify the allowed child-resource types
	_allowedChildResourceTypes = [ ResourceTypes.ACP,
								   ResourceTypes.ACTR, 
								   ResourceTypes.AE, 
								   ResourceTypes.CRS, 
								   ResourceTypes.CSR, 
								   ResourceTypes.CNT, 
								   ResourceTypes.FCNT, 
								   ResourceTypes.GRP, 
								   ResourceTypes.NOD, 
								   ResourceTypes.REQ, 
								   ResourceTypes.SUB, 
								   ResourceTypes.TS, 
								   ResourceTypes.TSB, 
								   ResourceTypes.CSEBaseAnnc ]

	# Attributes and Attribute policies for this Resource Class
	# Assigned during startup in the Importer
	_attributes:AttributePolicyDict = {		
			# Common and universal attributes
			'rn': None,
		 	'ty': None,
			'ri': None,
			'pi': None,
			'ct': None,
			'lt': None,
			'lbl': None,
			'loc': None,	
			'cstn': None,
			'acpi': None,

			# Resource attributes
			'poa': None,
			'nl': None,
			'daci': None,
			'esi': None,
			'srv': None,
			'cst': None,
			'csi': None,
			'csz': None
	}


	def __init__(self, dct:JSON, create:Optional[bool] = False) -> None:
		super().__init__(ResourceTypes.CSEBase, dct, '', create = create)

		self.setAttribute('ri', 'cseid', overwrite = False)
		self.setAttribute('rn', 'cse', overwrite = False)
		self.setAttribute('csi', '/cse', overwrite = False)

		self.setAttribute('rr', False, overwrite = False)
		self.setAttribute('srt', ResourceTypes.supportedResourceTypes(), overwrite = False)			#  type: ignore
		self.setAttribute('csz', ContentSerializationType.supportedContentSerializations(), overwrite = False)	# Will be replaced when retrieved
		self.setAttribute('srv', CSE.supportedReleaseVersions, overwrite = False)			# This must be a list
		self.setAttribute('poa', CSE.csePOA, overwrite = False)	
		self.setAttribute('cst', CSE.cseType, overwrite = False)

		# remove the et attribute that was set by the parent. The CSEBase doesn't have one	
		self.delAttribute('et', setNone = False)	


	def activate(self, parentResource:Resource, originator:str) -> Result:
		if not (res := super().activate(parentResource, originator)).status:
			return res
		
		if not Utils.isValidCSI(self.csi):
			L.logWarn(dbg := f'Wrong format for CSEBase.csi: {self.csi}')
			return Result.errorResult(dbg = dbg)

		return Result.successResult()


	def validate(self, originator:Optional[str] = None, 
					   create:Optional[bool] = False, 
					   dct:Optional[JSON] = None, 
					   parentResource:Optional[Resource] = None) -> Result:
		if not (res := super().validate(originator, create, dct, parentResource)).status:
			return res
		
		self._normalizeURIAttribute('poa')

		# Update the hcl attribute in the hosting node (similar to AE)
		nl = self['nl']
		_nl_ = self.__node__

		if nl or _nl_:
			if nl != _nl_:
				if _nl_:
					if nresource := CSE.dispatcher.retrieveResource(_nl_).resource:
						nresource['hcl'] = None # remove old link
						CSE.dispatcher.updateLocalResource(nresource)
				self[Resource._node] = nl
				if nresource := CSE.dispatcher.retrieveResource(nl).resource:
					nresource['hcl'] = self['ri']
					CSE.dispatcher.updateLocalResource(nresource)
			self[Resource._node] = nl

		return Result.successResult()


	def willBeRetrieved(self, originator:str, 
							  request:Optional[CSERequest] = None, 
							  subCheck:Optional[bool] = True) -> Result:
		if not (res := super().willBeRetrieved(originator, request, subCheck = subCheck)).status:
			return res

		# add the current time to this resource instance
		self.setAttribute('ctm', CSE.time.getCSETimestamp())

		# add the supported release versions
		self.setAttribute('srv', CSE.supportedReleaseVersions)

		return Result.successResult()


		
