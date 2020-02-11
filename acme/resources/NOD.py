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
from .Resource import *

# TODO Support cmdhPolicy
# TODO Support storage

class NOD(Resource):

	def __init__(self, jsn=None, pi=None, create=False):
		super().__init__(C.tsNOD, jsn, pi, C.tNOD, create=create)

		if self.json is not None:
			self.setAttribute('ni', Utils.uniqueID(), overwrite=False)


	# Enable check for allowed sub-resources
	def canHaveChild(self, resource):
		return super()._canHaveChild(resource, 
									[ C.tMGMTOBJ,
									  C.tSUB
									])