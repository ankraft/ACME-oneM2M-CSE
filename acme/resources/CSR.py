#
#	CSR.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: RemoteCSE
#

from Constants import Constants as C
from Configuration import Configuration
from .Resource import *

class CSR(Resource):

	def __init__(self, jsn=None, pi=None, rn=None, create=False):
		super().__init__(C.tsCSR, jsn, pi, C.tCSR, rn=rn, create=create)

		if self.json is not None:
			self.setAttribute('csi', 'cse', overwrite=False)
			self.setAttribute('rr', False, overwrite=False)

	# Enable check for allowed sub-resources
	def canHaveChild(self, resource):
		return super()._canHaveChild(resource,
									 [ C.tCNT,
									   C.tFCNT,
									   C.tGRP,
									   C.tACP,
									   C.tSUB
									 ])
