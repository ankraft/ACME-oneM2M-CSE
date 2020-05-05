#
#	FCNT.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: FlexContainer
#

import sys
from Constants import Constants as C
import Utils
from .Resource import *


class FCNT(Resource):

	def __init__(self, jsn=None, pi=None, fcntType=None, create=False):
		super().__init__(fcntType, jsn, pi, C.tFCNT, create=create)
		if self.json is not None:
			self.setAttribute('cs', 0, overwrite=False)

			# "current" attributes are added when necessary in the validate() method

			# Indicates whether this FC has flexContainerInstances. 
			# Might change during the lifetime of a resource. Used for optimization
			self.hasInstances = False

		self.ignoreAttributes = [ self._rtype, self._srn, self._node, 'acpi', 'cbs', 'cni', 'cnd', 'cs', 'cr', 'ct', 'et', 'lt', 'mbs', 'mia', 'mni', 'or', 'pi', 'ri', 'rn', 'st', 'ty' ]


	# Enable check for allowed sub-resources
	def canHaveChild(self, resource):
		return super()._canHaveChild(resource,	
									 [ C.tCNT,
									   C.tFCNT,
									   C.tSUB
									 ])


	def activate(self, originator):
		super().activate(originator)
		# TODO Error checking above

		# register latest and oldest virtual resources
		Logging.logDebug('Registering latest and oldest virtual resources for: %s' % self.ri)

		if self.hasInstances:
			# add latest
			r = Utils.resourceFromJSON({}, pi=self.ri, acpi=self.acpi, tpe=C.tFCNT_LA)
			CSE.dispatcher.createResource(r)

			# add oldest
			r = Utils.resourceFromJSON({}, pi=self.ri, acpi=self.acpi, tpe=C.tFCNT_OL)
			CSE.dispatcher.createResource(r)


		return (True, C.rcOK)


	# Checking the presentse of cnd and calculating the size
	def validate(self, originator, create=False):
		if (res := super().validate(originator, create))[0] == False:
			return res

		# No CND?
		if (cnd := self.cnd) is None or len(cnd) == 0:
			return (False, C.rcContentsUnacceptable)

		# Calculate contentSize
		# This is not at all realistic since this is the in-memory representation
		# TODO better implementation needed 
		cs = 0
		for attr in self.json:
			if attr in self.ignoreAttributes:
				continue
			cs += sys.getsizeof(self[attr])
		self['cs'] = cs

		#
		#	Handle flexContainerInstances
		#

		# TODO When cni and cbs is set to 0, then delete mni, mbs, la, ol, and all children
		

		if self.mni is not None or self.mbs is not None:
			self.hasInstances = True	# Change the internal flag whether this FC has flexContainerInstances

			self.addFlexContainerInstance(originator)
			fci = self.flexContainerInstances()

			# check mni
			if self.mni is not None:
				mni = self.mni
				fcii = len(fci)
				i = 0
				l = fcii
				while fcii > mni and i < l:
					# remove oldest
					CSE.dispatcher.deleteResource(fci[i])
					fcii -= 1
					i += 1
					changed = True
				self['cni'] = fcii

				# Add "current" atribute, if it is not there
				self.setAttribute('cni', 0, overwrite=False)

			# check size
			if self.mbs is not None:
				fci = self.flexContainerInstances()	# get FCIs again (bc may be different now)
				mbs = self.mbs
				cbs = 0
				for f in fci:					# Calculate cbs
					cbs += f.cs
				i = 0
				l = len(fci)
				print(fci)
				while cbs > mbs and i < l:
					# remove oldest
					cbs -= fci[i].cs
					CSE.dispatcher.deleteResource(fci[i])
					i += 1
				self['cbs'] = cbs

				# Add "current" atribute, if it is not there
				self.setAttribute('cbs', 0, overwrite=False)

		# TODO Remove la, ol, existing FCI when mni etc are not present anymore.


		# TODO support maxInstanceAge
		
		# May have been changed, so store the resource 
		x = CSE.dispatcher.updateResource(self, doUpdateCheck=False) # To avoid recursion, dont do an update check
		
		return (True, C.rcOK)


	# Get all flexContainerInstances of a resource and return a sorted (by ct) list 
	def flexContainerInstances(self):
		return sorted(CSE.dispatcher.subResources(self.ri, C.tFCI), key=lambda x: (x.ct))


	# Add a new FlexContainerInstance for this flexContainer
	def addFlexContainerInstance(self, originator):
		Logging.logDebug('Adding flexContainerInstance')
		jsn = {	'rn'  : '%s_%d' % (self.rn, self.st),
   				#'cnd' : self.cnd,
   				'lbl' : self.lbl,
   				'ct'  : self.lt,
   				'et'  : self.et,
   				'cs'  : self.cs,
   				'or'  : originator
			}
		for attr in self.json:
			if attr not in self.ignoreAttributes:
				jsn[attr] = self[attr]


		fci = Utils.resourceFromJSON(jsn = { self.tpe : jsn },
									pi = self.ri, 
									tpe = C.tFCI) # no ACPI

		CSE.dispatcher.createResource(fci)

