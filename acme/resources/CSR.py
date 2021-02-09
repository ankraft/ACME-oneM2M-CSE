#
#	CSR.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: RemoteCSE
#

from Constants import Constants as C
from Types import ResourceTypes as T, Result, JSON
from Configuration import Configuration
from Validator import constructPolicy, addPolicy
from .Resource import *
from .AnnounceableResource import AnnounceableResource

# Attribute policies for this resource are constructed during startup of the CSE
attributePolicies = constructPolicy([ 
	'ty', 'ri', 'rn', 'pi', 'acpi', 'ct', 'lt', 'et', 'lbl', 'at', 'aa', 'cr', 'daci', 'loc', 'hld'
])
csrPolicies = constructPolicy([
	'cst', 'poa', 'cb', 'csi', 'mei', 'tri', 'rr', 'nl', 'csz', 'esi', 'trn', 'dcse', 'mtcc', 'egid', 'tren', 'ape', 'srv'
])
attributePolicies = addPolicy(attributePolicies, csrPolicies)

# TODO ^^^ Add Attribute EnableTimeCompensation, also in CSRAnnc


class CSR(AnnounceableResource):

	def __init__(self, dct:JSON=None, pi:str=None, rn:str=None, create:bool=False) -> None:
		super().__init__(T.CSR, dct, pi, rn=rn, create=create, attributePolicies=attributePolicies)

		self.resourceAttributePolicies = csrPolicies	# only the resource type's own policies

		if self.dict is not None:
			self.setAttribute('csi', 'cse', overwrite=False)	# This shouldn't happen
			self['ri'] = self.csi.split('/')[-1]				# overwrite ri (only after /'s')
			self.setAttribute('rr', False, overwrite=False)


	# Enable check for allowed sub-resources
	def canHaveChild(self, resource:Resource) -> bool:
		return super()._canHaveChild(resource,
									 [ T.CNT,
									   T.CNTAnnc,
									   T.CINAnnc,
									   T.FCNT,
									   T.FCNTAnnc,
									   T.FCI,
									   T.FCIAnnc,
									   T.GRP,
									   T.GRPAnnc,
									   T.ACP,
									   T.ACPAnnc,
									   T.SUB,
									   T.CSRAnnc,
									   T.MGMTOBJAnnc,
									   T.NODAnnc,
									   T.AEAnnc
									 ])


	def validate(self, originator:str=None, create:bool=False, dct:JSON=None) -> Result:
		if (res := super().validate(originator, create, dct)).status == False:
			return res
		self.normalizeURIAttribute('poa')
		return Result(status=True)
