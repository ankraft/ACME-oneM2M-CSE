#
#	FCI.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: FlexContainerInstance
#

from Constants import Constants as C
from .Resource import *
import Utils


class FCI(Resource):

	def __init__(self, jsn=None, pi=None, fcntType=None, create=False):
		super().__init__(fcntType, jsn, pi, C.tFCI, create=create, inheritACP=True, readOnly=True)


	# Enable check for allowed sub-resources. No Child for CIN
	def canHaveChild(self, resource):
		return super()._canHaveChild(resource, [])