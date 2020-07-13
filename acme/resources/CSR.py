#
#	CSR.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: RemoteCSE
#

from typing import Tuple
from Constants import Constants as C
from Types import ResourceTypes as T
from Configuration import Configuration
from Validator import constructPolicy, addPolicy
from .Resource import *
from .AnnounceableResource import AnnounceableResource

# Attribute policies for this resource are constructed during startup of the CSE
attributePolicies = constructPolicy([ 
	'ty', 'ri', 'rn', 'pi', 'acpi', 'ct', 'lt', 'et', 'lbl', 'at', 'aa', 'cr', 'daci', 'loc',
])
csrPolicies = constructPolicy([
	'cst', 'poa', 'cb', 'csi', 'mei', 'tri', 'rr', 'nl', 'csz', 'esi', 'trn', 'dcse', 'mtcc', 'egid', 'tren', 'ape', 'srv'
])
attributePolicies = addPolicy(attributePolicies, csrPolicies)

# TODO ^^^ Add Attribute EnableTimeCompensation


class CSR(AnnounceableResource):

	def __init__(self, jsn: dict = None, pi: str = None, rn: str = None, create: bool = False) -> None:
		super().__init__(T.CSR, jsn, pi, rn=rn, create=create)

		self.resourceAttributePolicies = csrPolicies	# only the resource type's own policies

		if self.json is not None:
			self.setAttribute('csi', 'cse', overwrite=False)	# This shouldn't happen
			self['ri'] = self.csi.split('/')[-1]				# overwrite ri (only after /'s')
			self.setAttribute('rr', False, overwrite=False)


	# Enable check for allowed sub-resources
	def canHaveChild(self, resource : Resource) -> bool:
		return super()._canHaveChild(resource,
									 [ T.CNT,
									   T.FCNT,
									   T.GRP,
									   T.ACP,
									   T.SUB
									 ])


	def validate(self, originator: str = None, create: bool = False) -> Tuple[bool, int, str]:
		if (res := super().validate(originator), create)[0] == False:
			return res
		self.normalizeURIAttribute('poa')
		return True, C.rcOK, None
