#
#	GRP.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: Group
#

from Constants import Constants as C
import Utils
from .Resource import *


class GRP(Resource):

	def __init__(self, jsn=None, pi=None, fcntType=None, create=False):
		super().__init__(C.tsGRP, jsn, pi, C.tGRP, create=create)
		if self.json is not None:
			self.setAttribute('mt', C.tMIXED, overwrite=False)
			self.setAttribute('ssi', False, overwrite=True)
			self.setAttribute('cnm', 0, overwrite=False)	# calculated later
			self.setAttribute('mid', [], overwrite=False)			
			self.setAttribute('mtv', False, overwrite=True)
			self.setAttribute('csy', C.csyAbandonMember, overwrite=False)

			# These attributes are not provided by default: mnm (no default), macp (no default)
			# optional set: spty, gn, nar


	# Enable check for allowed sub-resources
	def canHaveChild(self, resource):
		return super()._canHaveChild(resource,	
									 [ C.tSUB, 
									   C.tGRP_FOPT
									 ])

	def activate(self, originator, create=False):
		# super().activate(originator)		
		# if not (result := self.validate(originator))[0]:
		if not (result := super().activate(originator, create))[0]:
			return result

		# add fanOutPoint
		ri = self['ri']
		Logging.logDebug('Registering fanOutPoint resource for: %s' % ri)
		if not (res := CSE.dispatcher.createResource(
				Utils.resourceFromJSON({ 'pi' : ri }, acpi=self['acpi'],tpe=C.tGRP_FOPT),
				self, 
				originator))[0]:
			return res

		return (True, C.rcOK)


	def validate(self, originator, create=False):
		if (res := super().validate(originator, create))[0] == False:
			return res
		if (ret := CSE.group.validateGroup(self, originator))[0]:
			self['mtv'] = True	# validaed
			CSE.dispatcher.updateResource(self, doUpdateCheck=False) # To avoid recursion, dont do an update check
		else:
			self['mtv'] = False	# not validateed
		return ret




