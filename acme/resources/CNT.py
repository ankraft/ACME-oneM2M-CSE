#
#	CNT.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: Container
#

from typing import Tuple, List
from Logging import Logging
from Configuration import Configuration
from Constants import Constants as C
from Validator import constructPolicy
import Utils, CSE
from .Resource import *

# Attribute policies for this resource are constructed during startup of the CSE
attributePolicies = constructPolicy([ 
	'ty', 'ri', 'rn', 'pi', 'acpi', 'ct', 'lt', 'et', 'st', 'lbl', 'at', 'aa', 'daci', 'loc',
	'cr', 
	'mni', 'mbs', 'mia', 'cni', 'cbs', 'li', 'or', 'disr'
])


class CNT(Resource):


	def __init__(self, jsn: dict = None, pi: str = None, create: bool = False) -> None:
		super().__init__(C.tsCNT, jsn, pi, C.tCNT, create=create, attributePolicies=attributePolicies)

		if self.json is not None:
			self.setAttribute('mni', Configuration.get('cse.cnt.mni'), overwrite=False)
			self.setAttribute('mbs', Configuration.get('cse.cnt.mbs'), overwrite=False)
			self.setAttribute('cni', 0, overwrite=False)
			self.setAttribute('cbs', 0, overwrite=False)


	# Enable check for allowed sub-resources
	def canHaveChild(self, resource: Resource) -> bool:
		return super()._canHaveChild(resource,	
									 [ C.tCNT,
									   C.tCIN,
									   C.tFCNT,
									   C.tSUB
									 ])


	def activate(self, parentResource: Resource, originator: str) -> Tuple[bool, int, str]:
		if not (result := super().activate(parentResource, originator))[0]:
			return result

		# register latest and oldest virtual resources
		Logging.logDebug('Registering latest and oldest virtual resources for: %s' % self.ri)

		# add latest
		r, _ = Utils.resourceFromJSON({}, pi=self.ri, acpi=self.acpi, ty=C.tCNT_LA)
		res = CSE.dispatcher.createResource(r)
		if res[0] is None:
			return False, res[1], res[2]

		# add oldest
		r, _ = Utils.resourceFromJSON({}, pi=self.ri, acpi=self.acpi, ty=C.tCNT_OL)
		res = CSE.dispatcher.createResource(r)
		if res[0] is None:
			return False, res[1], res[2]

		return True, C.rcOK, None


	# Get all content instances of a resource and return a sorted (by ct) list 
	def contentInstances(self) -> List[Resource]:
		return sorted(CSE.dispatcher.directChildResources(self.ri, C.tCIN), key=lambda x: (x.ct))


	def childWillBeAdded(self, childResource: Resource, originator: str) -> Tuple[bool, int, str]:
		if not (res := super().childWillBeAdded(childResource, originator))[0]:
			return res
		
		# Check whether the child's rn is "ol" or "la".
		if (rn := childResource['rn']) is not None and rn in ['ol', 'la']:
			return False, C.rcOperationNotAllowed, 'resource types "latest" or "oldest" cannot be added'
	
		# Check whether the size of the CIN doesn't exceed the mbs
		if childResource.ty == C.tCIN and self.mbs is not None:
			if childResource.cs is not None and childResource.cs > self.mbs:
				return False, C.rcNotAcceptable, 'children content sizes would exceed mbs'
		return True, C.rcOK, None


	# Handle the addition of new CIN. Basically, get rid of old ones.
	def childAdded(self, childResource: Resource, originator: str) -> None:
		super().childAdded(childResource, originator)
		if childResource.ty == C.tCIN:	# Validate if child is CIN
			self.validate(originator)

	# Handle the removal of a CIN. 
	def childRemoved(self, childResource: Resource, originator: str) -> None:
		super().childRemoved(childResource, originator)
		if childResource.ty == C.tCIN:	# Validate if child was CIN
			self.validate(originator)


	# Validating the Container. This means recalculating cni, cbs as well as
	# removing ContentInstances when the limits are met.
	def validate(self, originator: str = None, create: bool = False) -> Tuple[bool, int, str]:
		if (res := super().validate(originator, create))[0] == False:
			return res

		# retrieve all children
		cs = self.contentInstances()

		# Check number of instances
		mni = self.mni
		cni = len(cs)
		i = 0
		l = cni
		while cni > mni and i < l:
			# remove oldest
			CSE.dispatcher.deleteResource(cs[i])
			cni -= 1
			i += 1
		self['cni'] = cni

		# check size
		cs = self.contentInstances()	# get CINs again
		mbs = self.mbs
		cbs = 0
		for c in cs:					# Calculate cbs
			cbs += c['cs']
		i = 0
		l = len(cs)
		while cbs > mbs and i < l:
			# remove oldest
			cbs -= cs[i]['cs']
			CSE.dispatcher.deleteResource(cs[i])
			i += 1
		self['cbs'] = cbs

		# TODO: support maxInstanceAge

		# Some CNT resource may have been updated, so store the resource 
		CSE.dispatcher.updateResource(self, doUpdateCheck=False) # To avoid recursion, dont do an update check

		return True, C.rcOK, None

