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
from Validator import constructPolicy
import Utils
from .Resource import *


# Attribute policies for this resource are constructed during startup of the CSE
attributePolicies = constructPolicy([ 
	'ty', 'ri', 'rn', 'pi', 'acpi', 'ct', 'lt', 'et', 'st', 'lbl', 'at', 'aa', 'cr', 'daci', 'loc',
	'cnd', 'or', 'cs', 'nl', 'mni', 'mia', 'mbs', 'cni'

])

class FCNT(Resource):

	def __init__(self, jsn=None, pi=None, fcntType=None, create=False):
		super().__init__(fcntType, jsn, pi, C.tFCNT, create=create, attributePolicies=attributePolicies)
		if self.json is not None:
			self.setAttribute('cs', 0, overwrite=False)

			# "current" attributes are added when necessary in the validate() method

			# Indicates whether this FC has flexContainerInstances. 
			# Might change during the lifetime of a resource. Used for optimization
			self.hasInstances = False

		self.ignoreAttributes = [ self._rtype, self._srn, self._node, self._originator, 'acpi', 'cbs', 'cni', 'cnd', 'cs', 'cr', 'ct', 'et', 'lt', 'mbs', 'mia', 'mni', 'or', 'pi', 'ri', 'rn', 'st', 'ty' ]


	# Enable check for allowed sub-resources
	def canHaveChild(self, resource):
		return super()._canHaveChild(resource,	
									 [ C.tCNT,
									   C.tFCNT,
									   C.tSUB
									 ])


	def activate(self, parentResource, originator):
		super().activate(parentResource, originator)
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
		return True, C.rcOK


	def childWillBeAdded(self, childResource, originator):
	
		# See also CNT resource
	
		if not (res := super().childWillBeAdded(childResource, originator))[0]:
			return res

		# Check whether the child's rn is "ol" or "la".
		if (rn := childResource['rn']) is not None and rn in ['ol', 'la']:
			return False, C.rcOperationNotAllowed
	
		# Check whether the size of the CIN doesn't exceed the mbs
		if childResource.ty == C.tCIN and self.mbs is not None:
			if childResource.cs is not None and childResource.cs > self.mbs:
				return False, C.rcNotAcceptable
		return True, C.rcOK


	# Checking the presentse of cnd and calculating the size
	def validate(self, originator, create=False):
		if (res := super().validate(originator, create))[0] == False:
			return res

		# No CND?
		if (cnd := self.cnd) is None or len(cnd) == 0:
			return False, C.rcContentsUnacceptable

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
		
		return True, C.rcOK


	# Validate expirations of child resurces
	def validateExpirations(self):
		Logging.logDebug('Validate expirations')
		super().validateExpirations()

		if (mia := self.mia) is None:
			return
		now = Utils.getResourceDate(-mia)
		# print(now)		# fcis = self.flexContainerInstances()
		# TODO
		# for fci in fcis



	# Get all flexContainerInstances of a resource and return a sorted (by ct) list 
	def flexContainerInstances(self):
		return sorted(CSE.dispatcher.directChildResources(self.ri, C.tFCI), key=lambda x: (x.ct))

# TODO:
# If the maxInstanceAge attribute is present in the targeted 
# <flexContainer> resource, then the Hosting CSE shall set the expirationTime attribute in 
# created <flexContainerInstance> child resource such that the time difference between expirationTime 
# and the creationTime of the <flexContainerInstance>. The <flexContainerInstance> child resource shall 
# not exceed the maxInstanceAge of the targeted <flexContainer> resource.

	# Add a new FlexContainerInstance for this flexContainer
	def addFlexContainerInstance(self, originator):
		Logging.logDebug('Adding flexContainerInstance')
		jsn = {	'rn'  : '%s_%d' % (self.rn, self.st),
   				#'cnd' : self.cnd,
   				'lbl' : self.lbl,
			}
		for attr in self.json:
			if attr not in self.ignoreAttributes:
				jsn[attr] = self[attr]


		fci = Utils.resourceFromJSON(jsn = { self.tpe : jsn },
									pi = self.ri, 
									acpi = self.acpi, # or no ACPI?
									tpe = C.tFCI)

		CSE.dispatcher.createResource(fci)
		fci['cs'] = self.cs
		fci.dbUpdate()


