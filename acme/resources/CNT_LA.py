#
#	CNT_LA.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: latest (virtual resource)
#

from Constants import Constants as C
import CSE, Utils
from .Resource import *
from Logging import Logging


class CNT_LA(Resource):

	def __init__(self, jsn=None, pi=None, create=False):
		super().__init__(C.tsCNT_LA, jsn, pi, C.tCNT_LA, create=create, inheritACP=True, readOnly=True, rn='la')



	# Enable check for allowed sub-resources
	def canHaveChild(self, resource):
		return super()._canHaveChild(resource, [])


	def asJSON(self, embedded=True, update=False, noACP=False):
		pi = self['pi']
		Logging.logDebug('Latest CIN from CNT: %s' % pi)
		(pr, _) = CSE.dispatcher.retrieveResource(pi)	# get parent
		rs = pr.contentInstances()						# ask parent for all CIN
		if len(rs) == 0:								# In case of none
			return None
		return rs[-1].asJSON(embedded=embedded, update=update, noACP=noACP)		# result is sorted, so take, and return last

