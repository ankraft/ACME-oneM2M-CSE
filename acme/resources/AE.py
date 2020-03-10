#
#	AE.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: Application Entity
#

from Constants import Constants as C
import Utils
from .Resource import *

class AE(Resource):

	def __init__(self, jsn=None, pi=None, create=False):
		super().__init__(C.tsAE, jsn, pi, C.tAE, create=create)

		if self.json is not None:
			self.setAttribute('aei', Utils.uniqueAEI(), overwrite=False)
			self.setAttribute('rr', False, overwrite=False)


	# Enable check for allowed sub-resources
	def canHaveChild(self, resource):
		return super()._canHaveChild(resource,	
									 [ C.tACP,
									   C.tCNT,
									   C.tFCNT,
									   C.tGRP,
									   C.tSUB
									 ])


	def validate(self, originator, create=False):
		if (res := super().validate(originator), create)[0] == False:
			return res
			
		# Update the hcl attribute in the hosting node
		nl = self['nl']
		_nl_ = self.__node__
		if nl is not None or _nl_ is not None:
			if nl != _nl_:
				ri = self['ri']
				# Remove from old node first
				if _nl_ is not None:
					(n, _) = CSE.dispatcher.retrieveResource(_nl_)
					if n is not None:
						hael = n['hael']
						if hael is not None and isinstance(hael, list) and ri in hael:
							hael.remove(ri)
						CSE.dispatcher.updateResource(n)
				self[self._node] = nl
				# Add to new node
				(n, _) = CSE.dispatcher.retrieveResource(nl)
				if n is not None:
					hael = n['hael']
					if hael is None:
						n['hael'] = [ ri ]
					else:
						if isinstance(hael, list):
							hael.append(ri)
							n['hael'] = hael
					CSE.dispatcher.updateResource(n)
			self[self._node] = nl

		return (True, C.rcOK)
