#
#	CNT.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: Container
#

from typing import List
from Logging import Logging
from Configuration import Configuration
from Constants import Constants as C
from Types import ResourceTypes as T, Result, ResponseCode as RC, JSON
from Validator import constructPolicy, addPolicy
import Utils, CSE
from .Resource import *
from .AnnounceableResource import AnnounceableResource
import resources.Factory as Factory




# Attribute policies for this resource are constructed during startup of the CSE
attributePolicies = constructPolicy([ 
	'ty', 'ri', 'rn', 'pi', 'acpi', 'ct', 'lt', 'et', 'st', 'lbl', 'at', 'aa', 'daci', 'loc', 'hld', 'cr',
])
cntPolicies = constructPolicy([
	'mni', 'mbs', 'mia', 'cni', 'cbs', 'li', 'or', 'disr'
])
attributePolicies =  addPolicy(attributePolicies, cntPolicies)


class CNT(AnnounceableResource):


	def __init__(self, dct:JSON=None, pi:str=None, create:bool=False) -> None:
		super().__init__(T.CNT, dct, pi, create=create, attributePolicies=attributePolicies)

		self.resourceAttributePolicies = cntPolicies	# only the resource type's own policies

		if self.dict is not None:
			self.setAttribute('mni', Configuration.get('cse.cnt.mni'), overwrite=False)
			self.setAttribute('mbs', Configuration.get('cse.cnt.mbs'), overwrite=False)
			self.setAttribute('cni', 0, overwrite=False)
			self.setAttribute('cbs', 0, overwrite=False)

		self.__validating = False	# semaphore for validating


	# Enable check for allowed sub-resources
	def canHaveChild(self, resource: Resource) -> bool:
		return super()._canHaveChild(resource,	
									 [ T.CNT,
									   T.CIN,
									   T.FCNT,
									   T.SUB
									 ])


	def activate(self, parentResource:Resource, originator:str) -> Result:
		if not (res := super().activate(parentResource, originator)).status:
			return res
		

		# register latest and oldest virtual resources
		Logging.logDebug(f'Registering latest and oldest virtual resources for: {self.ri}')

		# add latest
		latestResource = Factory.resourceFromDict({}, pi=self.ri, ty=T.CNT_LA).resource		# rn is assigned by resource itself
		if (res := CSE.dispatcher.createResource(latestResource)).resource is None:
			return Result(status=False, rsc=res.rsc, dbg=res.dbg)

		# add oldest
		oldestResource = Factory.resourceFromDict({}, pi=self.ri, ty=T.CNT_OL).resource		# rn is assigned by resource itself
		if (res := CSE.dispatcher.createResource(oldestResource)).resource is None:
			return Result(status=False, rsc=res.rsc, dbg=res.dbg)

		return Result(status=True)


	# Get all content instances of a resource and return a sorted (by ct) list 
	def contentInstances(self) -> List[Resource]:
		return sorted(CSE.dispatcher.directChildResources(self.ri, T.CIN), key=lambda x: (x.ct))	# type: ignore[no-any-return]


	def childWillBeAdded(self, childResource:Resource, originator:str) -> Result:
		if not (res := super().childWillBeAdded(childResource, originator)).status:
			return res
		
		# Check whether the child's rn is "ol" or "la".
		if (rn := childResource['rn']) is not None and rn in ['ol', 'la']:
			return Result(status=False, rsc=RC.operationNotAllowed, dbg='resource types "latest" or "oldest" cannot be added')
	
		# Check whether the size of the CIN doesn't exceed the mbs
		if childResource.ty == T.CIN and self.mbs is not None:
			if childResource.cs is not None and childResource.cs > self.mbs:
				return Result(status=False, rsc=RC.notAcceptable, dbg='children content sizes would exceed mbs')
		return Result(status=True)


	# Handle the addition of new CIN. Basically, get rid of old ones.
	def childAdded(self, childResource:Resource, originator:str) -> None:
		Logging.logDebug(f'Child resource added: {childResource.ri}')
		super().childAdded(childResource, originator)
		if childResource.ty == T.CIN:	# Validate if child is CIN

			# Check for mia handling
			if self.mia is not None:
				# Take either mia or the maxExpirationDelta, whatever is smaller
				maxEt = Utils.getResourceDate(self.mia if self.mia <= (med := Configuration.get('cse.maxExpirationDelta')) else med)
				# Only replace the childresource's et if it is greater than the calculated maxEt
				if childResource.et > maxEt:
					childResource.setAttribute('et', maxEt)
					childResource.dbUpdate()

			self.validate(originator)

	# Handle the removal of a CIN. 
	def childRemoved(self, childResource:Resource, originator:str) -> None:
		Logging.logDebug(f'Child resource removed: {childResource.ri}')
		super().childRemoved(childResource, originator)
		if childResource.ty == T.CIN:	# Validate if child was CIN
			self._validateChildren()


	# Validating the Container. This means recalculating cni, cbs as well as
	# removing ContentInstances when the limits are met.
	def validate(self, originator:str=None, create:bool=False, dct:JSON=None) -> Result:
		if (res := super().validate(originator, create, dct)).status == False:
			return res
		self._validateChildren()
		return Result(status=True)


	# TODO Align this and FCNT implementations
	
	def _validateChildren(self) -> None:
		""" Internal validation and checks. This called more often then just from
			the validate() method.
		"""
		# Check whether we already are in validation the children (ie prevent unfortunate recursion by the Dispatcher)
		if self.__validating:
			return
		self.__validating = True

		# retrieve all children
		cs = self.contentInstances()

		# Check number of instances
		mni = self.mni
		cni = len(cs)
		i = 0
		l = cni
		while cni > mni and i < l:
			Logging.logDebug(f'cni > mni: Removing <cin>: {cs[i].ri}')
			# remove oldest
			CSE.dispatcher.deleteResource(cs[i], parentResource=self)
			cni -= 1	# decrement cni
			i += 1

		# check size
		cs = self.contentInstances()	# get CINs again
		mbs = self.mbs
		cbs = 0
		for c in cs:					# Calculate cbs
			cbs += c['cs']
		i = 0
		l = len(cs)
		while cbs > mbs and i < l:
			Logging.logDebug(f'cbs > mbs: Removing <cin>: {cs[i].ri}')

			# remove oldest
			cbs -= cs[i]['cs']
			CSE.dispatcher.deleteResource(cs[i], parentResource=self)
			cni -= 1	# again, decrement cni when deleting a cni
			i += 1

		# Some CNT resource may have been updated, so store the resource 
		self['cni'] = cni
		self['cbs'] = cbs
		self.dbUpdate()
	
		# End validating
		self.__validating = False

