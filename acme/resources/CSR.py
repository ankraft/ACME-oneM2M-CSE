#
#	CSR.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: RemoteCSE
#

from ..etc.Types import AttributePolicyDict, ResourceTypes as T, Result, JSON
from ..resources.Resource import *
from ..resources.AnnounceableResource import AnnounceableResource


class CSR(AnnounceableResource):

	# Specify the allowed child-resource types
	_allowedChildResourceTypes = [	T.ACP, T.ACPAnnc, T.ACTR, T.ACTRAnnc, T.AEAnnc, T.CNT, T.CNTAnnc, 
									T.CINAnnc, T.CSRAnnc, T.FCNT, T.FCNTAnnc, T.FCI, T.GRP, T.GRPAnnc, 
									T.MGMTOBJAnnc, T.NODAnnc, T.PCH, T.SUB, T.TS, T.TSAnnc, T.TSB ]


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
	

	def __init__(self, dct:JSON=None, pi:str = None, rn:str = None, create:bool = False) -> None:
		super().__init__(T.CSR, dct, pi, rn = rn, create=create)

		#self.setAttribute('csi', 'cse', overwrite=False)	# This shouldn't happen
		if self.csi:
			# self.setAttribute('ri', self.csi.split('/')[-1])				# overwrite ri (only after /'s')
			self.setAttribute('ri', Utils.getIdFromOriginator(self.csi))	# overwrite ri (only after /'s')
		self.setAttribute('rr', False, overwrite=False)


	def childWillBeAdded(self, childResource:Resource, originator:str) -> Result:
		if not (res := super().childWillBeAdded(childResource, originator)).status:
			return res

		# Perform checks for <PCH>	
		if childResource.ty == T.PCH:
			# Check correct originator. Even the ADMIN is not allowed that		
			if self.csi != originator:
				L.logDebug(dbg := f'Originator must be the parent <CSR>')
				return Result.errorResult(rsc = RC.originatorHasNoPrivilege, dbg = dbg)

			# check that there will only by one PCH as a child
			if CSE.dispatcher.countDirectChildResources(self.ri, ty=T.PCH) > 0:
				L.logDebug(dbg := 'Only one <PCH> per <CSR> is allowed')
				return Result.errorResult(dbg = dbg)

		return Result.successResult()


	def validate(self, originator:str = None, create:bool = False, dct:JSON = None, parentResource:Resource = None) -> Result:
		if (res := super().validate(originator, create, dct, parentResource)).status == False:
			return res
		self._normalizeURIAttribute('poa')
		return Result.successResult()
