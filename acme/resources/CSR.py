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

from ..etc.Types import AttributePolicyDict, ResourceTypes, JSON
from ..etc.ResponseStatusCodes import ORIGINATOR_HAS_NO_PRIVILEGE, BAD_REQUEST
from ..etc.IDUtils import getIdFromOriginator
from ..resources.Resource import Resource
from ..resources.AnnounceableResource import AnnounceableResource
from ..runtime.Logging import Logging as L
from ..runtime import CSE


class CSR(AnnounceableResource):

	resourceType = ResourceTypes.CSR
	""" The resource type """

	typeShortname = resourceType.typeShortname()
	"""	The resource's domain and type name. """

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
									ResourceTypes.LCPAnnc,
									ResourceTypes.MGMTOBJAnnc,
									ResourceTypes.NODAnnc,
									ResourceTypes.PCH,
								    ResourceTypes.PRMR,
								    ResourceTypes.PRMRAnnc,
									ResourceTypes.PRP,
									# ResourceTypes.PRPAnnc,	# TODO
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
	

	def initialize(self, pi:str, originator:str) -> None:
		#self.setAttribute('csi', 'cse', overwrite=False)	# This shouldn't happen
		if self.csi:
			# self.setAttribute('ri', self.csi.split('/')[-1])				# overwrite ri (only after /'s')
			self.setAttribute('ri', getIdFromOriginator(self.csi))	# overwrite ri (only after /'s')
		self.setAttribute('rr', False, overwrite = False)
		super().initialize(pi, originator)


	def childWillBeAdded(self, childResource:Resource, originator:str) -> None:
		super().childWillBeAdded(childResource, originator)

		# Perform checks for <PCH>	
		if childResource.ty == ResourceTypes.PCH:
			# Check correct originator. Even the ADMIN is not allowed that		
			if self.csi != originator:
				raise ORIGINATOR_HAS_NO_PRIVILEGE(L.logDebug(f'Originator must be the parent <CSR>'))

			# check that there will only by one PCH as a child
			if CSE.dispatcher.countDirectChildResources(self.ri, ty=ResourceTypes.PCH) > 0:
				raise BAD_REQUEST(L.logDebug('Only one <PCH> per <CSR> is allowed'))


	def validate(self, originator:Optional[str] = None, 
					   dct:Optional[JSON] = None, 
					   parentResource:Optional[Resource] = None) -> None:
		super().validate(originator, dct, parentResource)
		self._normalizeURIAttribute('poa')
