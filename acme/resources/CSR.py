#
#	CSR.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: RemoteCSE
#

from __future__ import annotations
from typing import Optional

from ..etc.Types import AttributePolicyDict, ResourceTypes, ResponseStatusCode, Result, JSON
from ..etc import Utils
from ..resources.Resource import Resource
from ..resources.AnnounceableResource import AnnounceableResource
from ..services.Logging import Logging as L
from ..services import CSE


class CSR(AnnounceableResource):

	# Specify the allowed child-resource types
	_allowedChildResourceTypes = [	ResourceTypes.ACP, 
									ResourceTypes.ACPAnnc, 
									ResourceTypes.ACTR, 
									ResourceTypes.ACTRAnnc, 
									ResourceTypes.AEAnnc, 
									ResourceTypes.CINAnnc,
									ResourceTypes.CNT,
									ResourceTypes.CNTAnnc, 
									ResourceTypes.CRS,
									ResourceTypes.CSRAnnc,
									ResourceTypes.FCNT,
									ResourceTypes.FCNTAnnc,
									ResourceTypes.FCI,
									ResourceTypes.GRP, 
									ResourceTypes.GRPAnnc, 
									ResourceTypes.MGMTOBJAnnc,
									ResourceTypes.NODAnnc,
									ResourceTypes.PCH,
									ResourceTypes.SMDAnnc,
									ResourceTypes.SUB,
									ResourceTypes.TS,
									ResourceTypes.TSAnnc,
									ResourceTypes.TSB ]


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
			'et': None,
			'lbl': None,
			'cstn': None,
			'acpi':None,
			'daci': None,
			'at': None,
			'aa': None,
			'ast': None,
			'cr': None,
			'loc': None,

			# Resource attributes
			'cst': None,
			'poa': None,
			'cb': None,
			'csi': None,
			'mei': None,
			'tri': None,
			'rr': None,
			'nl': None,
			'csz': None,
			'esi': None,
			'trn': None,
			'dcse': None,
			'mtcc': None,
			'egid': None,
			'tren': None,
			'ape': None,
			'srv': None
	}

	# TODO ^^^ Add Attribute EnableTimeCompensation, also in CSRAnnc
	

	def __init__(self, dct:Optional[JSON] = None, 
					   pi:Optional[str] = None, 
					   rn:Optional[str] = None, 
					   create:Optional[bool] = False) -> None:
		super().__init__(ResourceTypes.CSR, dct, pi, rn = rn, create=create)

		#self.setAttribute('csi', 'cse', overwrite=False)	# This shouldn't happen
		if self.csi:
			# self.setAttribute('ri', self.csi.split('/')[-1])				# overwrite ri (only after /'s')
			self.setAttribute('ri', Utils.getIdFromOriginator(self.csi))	# overwrite ri (only after /'s')
		self.setAttribute('rr', False, overwrite=False)


	def childWillBeAdded(self, childResource:Resource, originator:str) -> Result:
		if not (res := super().childWillBeAdded(childResource, originator)).status:
			return res

		# Perform checks for <PCH>	
		if childResource.ty == ResourceTypes.PCH:
			# Check correct originator. Even the ADMIN is not allowed that		
			if self.csi != originator:
				return Result.errorResult(rsc = ResponseStatusCode.originatorHasNoPrivilege, dbg = L.logDebug(f'Originator must be the parent <CSR>'))

			# check that there will only by one PCH as a child
			if CSE.dispatcher.countDirectChildResources(self.ri, ty=ResourceTypes.PCH) > 0:
				return Result.errorResult(dbg = L.logDebug('Only one <PCH> per <CSR> is allowed'))

		return Result.successResult()


	def validate(self, originator:Optional[str] = None, 
					   create:Optional[bool] = False, 
					   dct:Optional[JSON] = None, 
					   parentResource:Optional[Resource] = None) -> Result:
		if (res := super().validate(originator, create, dct, parentResource)).status == False:
			return res
		self._normalizeURIAttribute('poa')
		return Result.successResult()
