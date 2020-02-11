#
#	CIN.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: ContentInstance
#

from Constants import Constants as C
from .Resource import *
import Utils


class CIN(Resource):

	def __init__(self, jsn=None, pi=None, create=False):
		super().__init__(C.tsCIN, jsn, pi, C.tCIN, create=create, inheritACP=True, readOnly = True)

		if self.json is not None:
			self.setAttribute('con', '', overwrite=False)
			self.setAttribute('cs', len(self['con']))


	# Enable check for allowed sub-resources. No Child for CIN
	def canHaveChild(self, resource):
		return super()._canHaveChild(resource, [])