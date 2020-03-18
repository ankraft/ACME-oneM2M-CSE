#
#	FCNT_OL.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: oldest (virtual resource) for flexContainer
#

from Constants import Constants as C
import CSE, Utils
from .Resource import *
from Logging import Logging


class FCNT_OL(Resource):

	def __init__(self, jsn=None, pi=None, create=False):
		super().__init__(C.tsFCNT_OL, jsn, pi, C.tFCNT_OL, create=create, inheritACP=True, readOnly=True, rn='ol')


	# Enable check for allowed sub-resources
	def canHaveChild(self, resource):
		return super()._canHaveChild(resource, [])


	def asJSON(self, embedded=True, update=False, noACP=False):
		pi = self['pi']
		Logging.logDebug('Oldest FCI from FCNT: %s' % pi)
		(pr, _) = CSE.dispatcher.retrieveResource(pi)	# get parent
		rs = pr.flexContainerInstances()				# ask parent for all FCIs
		if len(rs) == 0:								# In case of none
			return None
		return rs[0].asJSON(embedded=embedded, update=update, noACP=noACP)		# result is sorted, so take, and return first


