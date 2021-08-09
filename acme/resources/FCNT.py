#
#	FCNT.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: FlexContainer
#

from __future__ import annotations
import sys
from typing import List, cast
from etc.Types import ResourceTypes as T, Result, ResponseCode as RC, JSON
import etc.Utils as Utils, etc.DateUtils as DateUtils, services.CSE as CSE
import resources.Factory as Factory
from resources.Resource import *
from resources.AnnounceableResource import AnnounceableResource
from services.Logging import Logging as L
from services.Configuration import Configuration
from services.Validator import constructPolicy, addPolicy



# Attribute policies for this resource are constructed during startup of the CSE
attributePolicies = constructPolicy([ 
	'ty', 'ri', 'rn', 'pi', 'acpi', 'ct', 'lt', 'et', 'st', 'lbl', 'at', 'aa', 'cr', 'hld', 'daci', 'loc',
])
fcntPolicies = constructPolicy([
	'cnd', 'or', 'cs', 'nl', 'mni', 'mia', 'mbs', 'cbs', 'cni', 'dgt'
])
attributePolicies = addPolicy(attributePolicies, fcntPolicies)


class FCNT(AnnounceableResource):

	# Specify the allowed child-resource types
	allowedChildResourceTypes = [ T.CNT, T.FCNT, T.SUB, T.TS, T.FCI ]


	_hasFCI	= '__hasFCI__'
	"""	Internal attribute to indicate whether this FCNT has la/ol installed. """

	def __init__(self, dct:JSON=None, pi:str=None, fcntType:str=None, create:bool=False) -> None:
		super().__init__(T.FCNT, dct, pi, tpe=fcntType, create=create, attributePolicies=attributePolicies)
		self.internalAttributes.append(self._hasFCI)	# Add to internal attributes to ignore in validation etc

		self.resourceAttributePolicies = fcntPolicies	# only the resource type's own policies

		self.setAttribute('cs', 0, overwrite=False)

		# "current" attributes are added when necessary in the validate() method

		# Indicates whether this FC has flexContainerInstances. 
		# Might change during the lifetime of a resource. Used for optimization
		self._hasInstances 	= False		# not stored in DB
		self.setAttribute(self._hasFCI, False, False)	# stored in DB

		self.__validating = False
		self.ignoreAttributes = self.internalAttributes + [ 'acpi', 'cbs', 'cni', 'cnd', 'cs', 'cr', 'ct', 'et', 'lt', 'mbs', 'mia', 'mni', 'or', 'pi', 'ri', 'rn', 'st', 'ty', 'at', 'aa' ]


	def activate(self, parentResource:Resource, originator:str) -> Result:
		if not (res := super().activate(parentResource, originator)).status:
			return res

		# Add <latest>/<oldest> child resources only when necessary
		if self.hasInstances:	# Set in validate() before
			# register latest and oldest virtual resources
			if not (res := self._addLaOl()).status:
				return res

		return Result(status=True)


	def update(self, dct:JSON=None, originator:str=None) -> Result:
		if not (res := super().update(dct, originator)).status:
			return res
		
		# Remove <latest>/<oldest> child resources when necessary (mni etc set to null)
		if self._hasInstances and not self[self._hasFCI]:
			if not (res := self._addLaOl()).status:
				return res
		elif not self._hasInstances and self[self._hasFCI]:
			if not (res := self._removeLaOl()).status:
				return res
			if not (res := self._removeFCIs()).status:
				return res
			self.setAttribute('cni', None)
			self.setAttribute('cbs', None)
			

		return Result(status=True)



	# This method is NOT called when adding FCIN!!
	# Because FCInn is added by the FCNT itself.

	def childWillBeAdded(self, childResource:Resource, originator:str) -> Result:
		if not (res := super().childWillBeAdded(childResource, originator)).status:
			return res

		# Check whether the child's rn is "ol" or "la".
		if (rn := childResource['rn']) and rn in ['ol', 'la']:
			return Result(status=False, rsc=RC.operationNotAllowed, dbg='resource types "latest" or "oldest" cannot be added')
		return Result(status=True)


	# Handle the removal of a FCIN. 
	def childRemoved(self, childResource:Resource, originator:str) -> None:
		super().childRemoved(childResource, originator)
		if childResource.ty == T.FCI:	# Validate if child was FCIN
			self._validateChildren(originator, deletingFCI=True)


	# Checking the presence of cnd and calculating the size
	def validate(self, originator:str=None, create:bool=False, dct:JSON=None, parentResource:Resource=None) -> Result:
		if not (res := super().validate(originator, create, dct, parentResource)).status:
			return res
		self._validateChildren(originator)
		return Result(status=True)

		# No CND? -> Validator
		# if (cnd := self.cnd) is None or len(cnd) == 0:
		# 	return Result(status=False, rsc=RC.contentsUnacceptable, dbg='cnd attribute missing or empty')


	def _validateChildren(self, originator:str, deletingFCI:bool=False) -> None:
		""" Internal validation and checks. This called more often then just from
			the validate() method, for example when deleting a FCIN.
		"""
		# Check whether we already are in validation the children (ie prevent unfortunate recursion by the Dispatcher)
		if self.__validating:
			return
		self.__validating = True

		# Calculate contentSize
		cs = 0
		for attr in self.dict:
			if attr in self.ignoreAttributes:
				continue
			cs += Utils.getAttributeSize(self[attr])
		self['cs'] = cs

		#
		#	Handle flexContainerInstances
		#		

		if self.mni is not None or self.mbs is not None or self.mia is not None: # not when this method is called when already deleting a child resource
			self._hasInstances = True	# Change the internal flag whether this FC has flexContainerInstances

			if not deletingFCI:
				self.addFlexContainerInstance(originator)
			
			fci = self.flexContainerInstances()
			fcii = len(fci)	# number of instances

			# check mni
			if self.mni is not None:	# is an int
				mni = self.mni
				i = 0
				l = fcii
				while fcii > mni and i < l:
					# remove oldest
					# Deleting a child must not cause a notification for 'deleteDirectChild'.
					# Don't do a delete check means that FCNT.childRemoved() is not called, where subscriptions for 'deleteDirectChild'  is tested.
					CSE.dispatcher.deleteResource(fci[i], parentResource=self, doDeleteCheck=False)
					fcii -= 1
					i += 1
					changed = True

				# Add "current" atribute, if it is not there
				self.setAttribute('cni', 0, overwrite=False)
				fci = self.flexContainerInstances()	# get FCIs again (bc may be different now)
				fcii = len(fci)

			# Calculate cbs
			cbs = 0
			for f in fci:					
				cbs += f.cs

			# check size
			if self.mbs is not None:
				mbs = self.mbs
				i = 0
				#l = len(fci)
				while cbs > mbs and i < fcii:
					# remove oldest
					cbs -= fci[i].cs			
					# Deleting a child must not cause a notification for 'deleteDirectChild'.
					# Don't do a delete check means that FCNT.childRemoved() is not called, where subscriptions for 'deleteDirectChild'  is tested.
					CSE.dispatcher.deleteResource(fci[i], parentResource=self, doDeleteCheck=False)
					fcii -= 1	# again, decrement fcii when deleting a cni
					i += 1

				# Add "current" atribute, if it is not there
				self.setAttribute('cbs', 0, overwrite=False)
			
			self['cni'] = fcii
			self['cbs'] = cbs
		else:
			self._hasInstances = False	# Indicate that reqs for child resources is not given
		
		# May have been changed, so store the resource
		self.dbUpdate()
	
		# End validating
		self.__validating = False


	def flexContainerInstances(self) -> list[Resource]:
		"""	Get all flexContainerInstances of a resource and return a sorted (by ct) list
		""" 
		return sorted(CSE.dispatcher.directChildResources(self.ri, T.FCI), key=lambda x: x.ct) # type:ignore[no-any-return]


	# Add a new FlexContainerInstance for this flexContainer
	def addFlexContainerInstance(self, originator:str) -> None:

		if L.isDebug: L.logDebug('Adding flexContainerInstance')
		dct:JSON = { 'rn'  : f'{self.rn}_{self.st:d}', }

		# Copy the label as well
		if self.lbl:	# TODO: this is currently (2021/04) not standard conform
			dct['lbl'] = self.lbl

		for attr in self.dict:
			if attr not in self.ignoreAttributes:
				dct[attr] = self[attr]
				continue
			# special for at attribute. It might contain additional id's when it
			# is announced. Those we don't want to copy.
			if attr == 'at':
				dct['at'] = [ x for x in self['at'] if x.count('/') == 1 ]	# Only copy single csi in at

		resource = Factory.resourceFromDict(resDict={ self.tpe : dct }, pi=self.ri, ty=T.FCI).resource
		CSE.dispatcher.createResource(resource, originator=originator)
		resource['cs'] = self.cs

		# Check for mia handling
		if self.mia is not None:	# mia is an int
			# Take either mia or the maxExpirationDelta, whatever is smaller
			maxEt = DateUtils.getResourceDate(self.mia if self.mia <= (med := Configuration.get('cse.maxExpirationDelta')) else med)
			# Only replace the childresource's et if it is greater than the calculated maxEt
			if resource.et > maxEt:
				resource.setAttribute('et', maxEt)

		resource.dbUpdate()	# store


	def _addLaOl(self) -> Result:
		"""	Add <latest> and <oldest> virtual child resources.
		"""
		if L.isDebug: L.logDebug(f'Registering latest and oldest virtual resources for: {self.ri}')

		# add latest
		resource = Factory.resourceFromDict({}, pi=self.ri, ty=T.FCNT_LA).resource	# rn is assigned by resource itself
		if not (res := CSE.dispatcher.createResource(resource)).resource:
			return Result(status=False, rsc=res.rsc, dbg=res.dbg)

		# add oldest
		resource = Factory.resourceFromDict({}, pi=self.ri, ty=T.FCNT_OL).resource	# rn is assigned by resource itself
		if not (res := CSE.dispatcher.createResource(resource)).resource:
			return Result(status=False, rsc=res.rsc, dbg=res.dbg)
		
		self.setAttribute(self._hasFCI, True)
		return Result(status=True)


	def _removeLaOl(self) -> Result:
		"""	Remove <latest> and <oldest> virtual child resources.
		"""
		if L.isDebug: L.logDebug(f'De-registering latest and oldest virtual resources for: {self.ri}')

		# remove latest
		if len(res := CSE.dispatcher.directChildResources(self.ri, T.FCNT_LA)) == 1: # type:ignore[no-any-return]
			CSE.dispatcher.deleteResource(res[0])	# ignore errors
		# remove oldest
		if len(res := CSE.dispatcher.directChildResources(self.ri, T.FCNT_OL)) == 1: # type:ignore[no-any-return]
			CSE.dispatcher.deleteResource(res[0])	# ignore errors
	
		self.setAttribute(self._hasFCI, False)
		return Result(status=True)


	def _removeFCIs(self) -> Result:
		"""	Remove the FCI childResources.
		"""
		if L.isDebug: L.logDebug(f'Removing FCI child resources for: {self.ri}')
		rs = CSE.dispatcher.directChildResources(self.ri, ty=T.FCI)
		for r in rs:
			# self.childRemoved(r, originator) # It should not be necessary to notify self at this point.
			if not (res := CSE.dispatcher.deleteResource(r, parentResource=self)).status:
				return res
		return Result(status=True)
