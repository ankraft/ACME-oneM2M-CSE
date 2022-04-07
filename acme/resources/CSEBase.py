#
#	CSEBase.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: CSEBase
#

from __future__ import annotations
from urllib import request
from ..etc.Types import AttributePolicyDict, CSERequest, ResourceTypes as T, ContentSerializationType as CST, Result, JSON
from ..etc import Utils
from ..resources.Resource import Resource
from ..resources.AnnounceableResource import AnnounceableResource
from ..services import CSE
from ..services.Logging import Logging as L

# TODO notificationCongestionPolicy

class CSEBase(AnnounceableResource):

	# Specify the allowed child-resource types
	_allowedChildResourceTypes = [ T.ACP, T.ACTR, T.AE, T.CSR, T.CNT, T.FCNT, T.GRP, T.NOD, T.REQ, T.SUB, T.TS, T.TSB, T.CSEBaseAnnc ]

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


	def __init__(self, dct:JSON, create:bool = False) -> None:
		super().__init__(T.CSEBase, dct, '', create = create)

		self.setAttribute('ri', 'cseid', overwrite = False)
		self.setAttribute('rn', 'cse', overwrite = False)
		self.setAttribute('csi', '/cse', overwrite = False)

		self.setAttribute('rr', False, overwrite = False)
		self.setAttribute('srt', T.supportedResourceTypes(), overwrite = False)			#  type: ignore
		self.setAttribute('csz', CST.supportedContentSerializations(), overwrite = False)	# Will be replaced when retrieved
		self.setAttribute('srv', CSE.supportedReleaseVersions, overwrite = False)			# This must be a list
		self.setAttribute('poa', [ CSE.httpServer.serverAddress ], overwrite = False)		# TODO add more address schemes when available
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


	def validate(self, originator:str = None, create:bool = False, dct:JSON = None, parentResource:Resource = None) -> Result:
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
						CSE.dispatcher.updateResource(nresource)
				self[Resource._node] = nl
				if nresource := CSE.dispatcher.retrieveResource(nl).resource:
					nresource['hcl'] = self['ri']
					CSE.dispatcher.updateResource(nresource)
			self[Resource._node] = nl

		return Result.successResult()


	def willBeRetrieved(self, originator:str, request:CSERequest, subCheck:bool = True) -> Result:
		if not (res := super().willBeRetrieved(originator, request, subCheck = subCheck)).status:
			return res

		# add the current time to this resource instance
		self['ctm'] = CSE.time.getCSETimestamp()

		# add the supported release versions
		self['srv'] = CSE.supportedReleaseVersions

		return Result.successResult()


		
