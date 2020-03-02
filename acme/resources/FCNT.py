#
#	FCNT.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: FlexContainer
#

import sys
from Constants import Constants as C
import Utils
from .Resource import *


class FCNT(Resource):

	def __init__(self, jsn=None, pi=None, fcntType=None, create=False):
		super().__init__(fcntType, jsn, pi, C.tFCNT, create=create)
		if self.json is not None:
			self.setAttribute('cs', 0, overwrite=False)

	# Enable check for allowed sub-resources
	def canHaveChild(self, resource):
		return super()._canHaveChild(resource,	
									 [ C.tCNT,
									   C.tFCNT,
									   C.tSUB
									 ])


	# Checking the presentse of cnd and calculating the size
	def validate(self, originator=None):
		if (res := super().validate(originator))[0] == False:
			return res

		# No CND?
		if (cnd := self.cnd) is None or len(cnd) == 0:
			return (False, C.rcContentsUnacceptable)

		# Calculate contentSize
		cs = 0
		for attr in self.json:
			if attr in [ self._rtype, self._srn, self._node, 'cs', 'ri',  'ct', 'lt', 'et', 'ty', 'st', 'pi', 'rn', 'cnd', 'or', 'acpi']:
				continue
			cs += sys.getsizeof(self['attr'])
		self['cs'] = cs
		
		# May have been changed, so store the resource 
		x = CSE.dispatcher.updateResource(self, doUpdateCheck=False) # To avoid recursion, dont do an update check
		
		return (True, C.rcOK)