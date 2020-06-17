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
			self.setAttribute('csi', 'cse', overwrite=False)	# This shouldn't happen
			self['ri'] = self.csi.split('/')[-1]				# overwrite ri (only after /'s')
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


	def validate(self, originator, create=False):
		if (res := super().validate(originator), create)[0] == False:
			return res

		self.normalizeURIAttribute('poa')
		return True, C.rcOK
