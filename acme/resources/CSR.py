#
#	CSR.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: RemoteCSE
#

from Types import ResourceTypes as T, Result, JSON
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

	# Specify the allowed child-resource types
	allowedChildResourceTypes = [ T.CNT, T.CNTAnnc, T.CINAnnc, T.FCNT, T.FCNTAnnc, T.FCI, T.FCIAnnc, T.GRP, T.GRPAnnc,
								T.ACP, T.ACPAnnc, T.SUB, T.TS, T.TSAnnc, T.CSRAnnc, T.MGMTOBJAnnc, T.NODAnnc, T.AEAnnc ]


	def __init__(self, dct:JSON=None, pi:str=None, rn:str=None, create:bool=False, isRemote:bool=False) -> None:
		super().__init__(T.CSR, dct, pi, rn=rn, create=create, attributePolicies=attributePolicies, isRemote=isRemote)

		self.resourceAttributePolicies = csrPolicies	# only the resource type's own policies

		if self.dict is not None:
			#self.setAttribute('csi', 'cse', overwrite=False)	# This shouldn't happen
			if self.csi is not None:
				self.setAttribute('ri', self.csi.split('/')[-1])				# overwrite ri (only after /'s')
			self.setAttribute('rr', False, overwrite=False)


	def validate(self, originator:str=None, create:bool=False, dct:JSON=None, parentResource:Resource=None) -> Result:
		if (res := super().validate(originator, create, dct, parentResource)).status == False:
			return res
		self.normalizeURIAttribute('poa')
		return Result(status=True)
