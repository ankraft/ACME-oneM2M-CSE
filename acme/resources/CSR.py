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

	def __init__(self, jsn=None, pi=None, create=False):
		super().__init__(C.tsCSR, jsn, pi, C.tCSR, create=create)

		if self.json is not None:
			self.setAttribute('csi', 'cse', overwrite=False)
			self.setAttribute('rr', False, overwrite=False)

