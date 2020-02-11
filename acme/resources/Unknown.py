#
#	Unknown.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: Unknown
#
#	This is the default-capture class for all unknown resources. 
#	This is only for storing the resource, no further processing is done.
#

from .Resource import Resource

class Unknown(Resource):

	def __init__(self, jsn, ty, root, pi=None, create=False):
		super().__init__(root, jsn, pi, ty, create=create)

	# Enable check for allowed sub-resources (ie. all)
	def canHaveChild(self, resource):
		return True