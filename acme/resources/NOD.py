#
#	NOD.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: mgmtObj:Node
#

import random, string
from Constants import Constants as C
import Utils, CSE
from Validator import constructPolicy
from .Resource import *

# TODO Support cmdhPolicy
# TODO Support storage

attributePolicies = constructPolicy([ 
	'ty', 'ri', 'rn', 'pi', 'acpi', 'ct', 'lt', 'et', 'lbl', 'at', 'aa', 'daci',
	'ni', 'hcl', 'hael', 'hsl', 'mgca', 'rms', 'nid', 'nty'
])

class NOD(Resource):

	def __init__(self, jsn: dict = None, pi: str = None, create: bool = False) -> None:
		super().__init__(C.tsNOD, jsn, pi, C.tNOD, create=create, attributePolicies=attributePolicies)

		if self.json is not None:
			self.setAttribute('ni', Utils.uniqueID(), overwrite=False)


	# Enable check for allowed sub-resources
	def canHaveChild(self, resource : Resource) -> bool:
		return super()._canHaveChild(resource, 
									[ C.tMGMTOBJ,
									  C.tSUB
									])


	def deactivate(self, originator : str) -> None:
		super().deactivate(originator)

		# Remove self from all hosted AE's (their node links)
		if (hael := self['hael']) is None:
			return
		ri = self['ri']
		for ae in self['hael']:
			self._removeNODfromAE(ae, ri)


	def _removeNODfromAE(self, aeRI: str, ri: str) -> None:
		""" Remove NOD.ri from AE node link. """

		ae, _, _ = CSE.dispatcher.retrieveResource(aeRI)
		if ae is not None:
			nl = ae['nl']
			if nl is not None and isinstance(nl, str) and ri == nl:
				ae.delAttribute('nl')
				ae.dbUpdate()

