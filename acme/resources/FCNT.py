#
#	FCNT.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: FlexContainer
#

from __future__ import annotations
from typing import Optional

from ..etc.Types import AttributePolicyDict, ResourceTypes, JSON
from ..etc.Constants import Constants
from ..etc.ResponseStatusCodes import OPERATION_NOT_ALLOWED, BAD_REQUEST
from ..etc.ACMEUtils import getAttributeSize
from ..etc.DateUtils import getResourceDate
from ..runtime import CSE
from ..runtime.Logging import Logging as L
from ..resources import Factory				# attn: circular import
from ..resources.Resource import Resource, internalAttributes, addToInternalAttributes
from ..resources.ContainerResource import ContainerResource


# Add to internal attributes
addToInternalAttributes(Constants.attrHasFCI)	# Add to internal attributes to ignore in validation etc

class FCNT(ContainerResource):

	# Specify the allowed child-resource types
	_allowedChildResourceTypes = [ ResourceTypes.ACTR, 
								   ResourceTypes.CNT, 
								   ResourceTypes.FCNT, 
								   ResourceTypes.SMD, 
								   ResourceTypes.SUB, 
								   ResourceTypes.TS, 
								   ResourceTypes.FCI,
								   ResourceTypes.FCNT_LA,
								   ResourceTypes.FCNT_OL ]

	# Attributes and Attribute policies for this Resource Class
	# Assigned during startup in the Importer
	_attributes:AttributePolicyDict = {		
		# Common and universal attributes
		'rn': None,
		'ty': None,
		'ri': None,
		'pi': None,
		'ct': None,
		'lt': None,
		'et': None,
		'lbl': None,
		'cstn': None,
		'acpi':None,
		'at': None,
		'aa': None,
		'ast': None,
		'daci': None,
		'st': None,
		'cr': None,
		'loc': None,

		# Resource attributes
		'cnd': None,
		'or': None,
		'cs': None,
		'nl': None,
		'mni': None,
		'mia': None,
		'mbs': None,
		'cbs': None,
		'cni': None
	}



	def __init__(self, dct:Optional[JSON] = None, 
					   pi:Optional[str] = None, 
					   fcntType:Optional[str] = None, 
					   create:Optional[bool] = False) -> None:
		super().__init__(ResourceTypes.FCNT, dct, pi, typeShortname = fcntType, create = create)

		self.setAttribute('cs', 0, overwrite = False)
		self.setAttribute('st', 0, overwrite = False)

		# Indicates whether this FC has flexContainerInstances. 
		# Might change during the lifetime of a resource. Used for optimization
		self._hasInstances 	= False		# not stored in DB
		self.setAttribute(Constants.attrHasFCI, False, False)	# stored in DB

		self.__validating = False
		self.ignoreAttributes = internalAttributes + [ a for a in self._attributes.keys() ]


	def activate(self, parentResource:Resource, originator:str) -> None:
		super().activate(parentResource, originator)

		# Add <latest>/<oldest> child resources only when necessary
		# if self._hasInstances:	# Set in validate() before
		# 	# register latest and oldest virtual resources
		# 	self._addLaOl()


	def update(self, dct:Optional[JSON] = None, 
					 originator:Optional[str] = None, 
					 doValidateAttributes:Optional[bool] = True) -> None:
		
		# Increment stateTag before all because it is needed later to name
		# a FCI, but only when any custom attributes is updated
		for attr in dct:
			if attr not in self.ignoreAttributes:
				self.setAttribute('st', self.st + 1)
				break

		super().update(dct, originator, doValidateAttributes)
		
		# Remove <latest>/<oldest> child resources when necessary (mni etc set to null)
		hasFCI = self[Constants.attrHasFCI]
		if self._hasInstances and not hasFCI:
			self._prepareForInstances()
		elif not self._hasInstances and hasFCI:
			self._removeLaOl()
			self._removeFCIs()
			self.setAttribute('cni', None)
			self.setAttribute('cbs', None)
		

	# This method is NOT called when adding FCIN!!
	# Because FCInn is added by the FCNT itself.

	def childWillBeAdded(self, childResource:Resource, originator:str) -> None:
		super().childWillBeAdded(childResource, originator)

		# Check whether the child's rn is "ol" or "la".
		if (rn := childResource['rn']) and rn in ['ol', 'la']:
			raise OPERATION_NOT_ALLOWED('resource types "latest" or "oldest" cannot be added')


	def childAdded(self, childResource:Resource, originator:str) -> None:
		L.isDebug and L.logDebug(f'Child resource added: {childResource.ri}')
		super().childAdded(childResource, originator)
		if childResource.ty == ResourceTypes.FCI:	# Validate if child was FCIN
			L.isDebug and L.logDebug(f'FCI added: {childResource.ri}')
			self.instanceAdded(childResource)
			self.updateLaOlLatestTimestamp()	# EXPERIMENTAL TODO Also do in FCNT and TS

		# Send update event on behalf of the latest resources.
		# The oldest resource might not be changed. That is handled in the validate() method.
		CSE.event.changeResource(childResource, self.getLatestRI())	 # type: ignore [attr-defined]



	# Handle the removal of a FCIN. 
	def childRemoved(self, childResource:Resource, originator:str) -> None:
		super().childRemoved(childResource, originator)
		if childResource.ty == ResourceTypes.FCI:	# Validate if child was FCIN
			self._validateChildren(originator, deletingFCI=True)


	# Checking the presence of cnd and calculating the size
	def validate(self, originator:Optional[str] = None, 
					   dct:Optional[JSON] = None, 
					   parentResource:Optional[Resource] = None) -> None:
		super().validate(originator, dct, parentResource)
		
		# Validate containerDefinition
		if dct is None:	# create
			if (t := CSE.validator.getFlexContainerSpecialization(self.typeShortname)):
				if t[0] != self.cnd:
					raise BAD_REQUEST(L.logDebug(f'Wrong cnd: {self.cnd} for specialization: {self.typeShortname}. Must be: {t[0]}'))

		# Validate the child resources
		self._validateChildren(originator, dct = dct)


	def _validateChildren(self, originator:str, 
								deletingFCI:Optional[bool] = False, 
								dct:Optional[JSON] = None) -> None:
		""" Internal validation and checks. This called more often then just from
			the validate() method, for example when deleting a FCIN.
		"""
		# Check whether we already are in validation the children (ie prevent unfortunate recursion by the Dispatcher)
		if self.__validating:
			return
		self.__validating = True

		# Calculate contentSize. Only the custom attribute
		self.setAttribute('cs', sum([getAttributeSize(self[attr]) for attr in self.dict if attr not in self.ignoreAttributes]))

		#
		#	Handle flexContainerInstances
		#		

		if self.mni is not None or self.mbs is not None or self.mia is not None: # not when this method is called when already deleting a child resource
			self._hasInstances = True	# Change the internal flag whether this FC has flexContainerInstances

			# Add FCI only 
			# - if mni etc is set, and
			# - if this is NOT a deleteFCI validation, and any of the following is true:
			#   - the Constants.attrHasFCI attriubte is NOT set (which means we are in progress to add FCI), or
			#   - the update dct is empty, or
			#   - there is any of the custom attributes OR lbl attribute present
			_updateCustomAttributes = dct is not None and any([each not in self.ignoreAttributes or each in [ 'lbl' ] for each in dct[self.typeShortname].keys()])
			if not deletingFCI and (_updateCustomAttributes or dct is None or not self[Constants.attrHasFCI]):
				self.addFlexContainerInstance(originator)
			
			fcis = self.flexContainerInstances()
			cni = len(fcis)	# number of instances
			fci:Resource = None

			# check mni
			if (mni := self.mni) is not None:	# is an int
				mni = self.mni
				while cni > mni and cni > 0:
					fci = fcis[0]
					L.isDebug and L.logDebug(f'cni > mni: Removing <fci>: {fci.ri}')
					# remove oldest
					# Deleting a child must not cause a notification for 'deleteDirectChild'.
					# Don't do a delete check means that FCNT.childRemoved() is not called, where subscriptions for 'deleteDirectChild'  is tested.
					CSE.dispatcher.deleteLocalResource(fci, parentResource = self, doDeleteCheck = False)
					del fcis[0]	# Remove from list
					cni -= 1	# decrement cni when deleting a <fci>

			# Calculate cbs
			cbs = sum([ each.cs for each in fcis])

			# check size
			if (mbs := self.mbs) is not None:
				while cbs > mbs and cbs > 0:
					fci = fcis[0]
					L.isDebug and L.logDebug(f'cbs > mbs: Removing <fci>: {fci.ri}')
					# remove oldest
					cbs -= fci.cs			
					# Deleting a child must not cause a notification for 'deleteDirectChild'.
					# Don't do a delete check means that FCNT.childRemoved() is not called, where subscriptions for 'deleteDirectChild'  is tested.
					CSE.dispatcher.deleteLocalResource(fci, parentResource = self, doDeleteCheck = False)
					cni -= 1	# again, decrement cbi when deleting a cni

				# Add "current" atribute, if it is not there
				self.setAttribute('cbs', 0, overwrite = False)
			
			self.setAttribute('cni', cni)
			self.setAttribute('cbs', cbs)

			# If fci is not None anymore then we have a new "oldest" resource.
			# fci is NOT the oldest resource, but the one that was deleted last. The new
			# oldest resource is the first in the list of fcis.
			# This means that we need to send an "update" event for the oldest resource.
			if fci is not None and len(fcis):
				CSE.event.changeResource(fcis[0], self.getOldestRI())	# type: ignore [attr-defined]

		else:
			self._hasInstances = False	# Indicate that reqs for child resources is not given
		
		# May have been changed, so store the resource
		self.dbUpdate(True)
	
		# End validating
		self.__validating = False


	def flexContainerInstances(self) -> list[Resource]:
		"""	Get all flexContainerInstances of a resource and return a sorted (by ct) list
		""" 
		return sorted(CSE.dispatcher.retrieveDirectChildResources(self.ri, ResourceTypes.FCI), key = lambda x: x.ct) # type:ignore[no-any-return]


	# Add a new FlexContainerInstance for this flexContainer
	def addFlexContainerInstance(self, originator:str) -> None:

		L.isDebug and L.logDebug('Adding flexContainerInstance')

		# Add <latest> and <oldest> virtual child resources if not already there
		self._prepareForInstances()	

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

		fciRes = Factory.resourceFromDict(resDict = { self.typeShortname : dct }, pi = self.ri, ty = ResourceTypes.FCI)
		CSE.dispatcher.createLocalResource(fciRes, self, originator = originator)
		fciRes.setAttribute('cs', self.cs)
		fciRes.setAttribute('org', originator)

		# Check for mia handling
		if self.mia is not None:	# mia is an int
			# Take either mia or the maxExpirationDelta, whatever is smaller
			maxEt = getResourceDate(self.mia 
									if self.mia <= CSE.request.maxExpirationDelta 
									else CSE.request.maxExpirationDelta)
			# Only replace the childresource's et if it is greater than the calculated maxEt
			if fciRes.et > maxEt:
				fciRes.setAttribute('et', maxEt)

		fciRes.dbUpdate(True)	# store


	def _prepareForInstances(self) -> None:
		"""	Add <latest> and <oldest> virtual child resources.
		"""
		if self[Constants.attrHasFCI]:	# Not necessary
			return
		
		L.isDebug and L.logDebug(f'Registering latest and oldest virtual resources for: {self.ri}')

		# add latest
		resource = Factory.resourceFromDict({ 'et': self.et }, 
											pi = self.ri, 
											ty = ResourceTypes.FCNT_LA)	# rn is assigned by resource itself
		resource = CSE.dispatcher.createLocalResource(resource, self)
		self.setLatestRI(resource.ri)


		# add oldest
		resource = Factory.resourceFromDict({ 'et': self.et }, 
											pi = self.ri, 
											ty = ResourceTypes.FCNT_OL)	# rn is assigned by resource itself
		resource = CSE.dispatcher.createLocalResource(resource, self)
		self.setOldestRI(resource.ri)
		
		self.setAttribute(Constants.attrHasFCI, True)
	
		# Also adding cni and cbs attribute to the FCNT
		self.setAttribute('cni', 0)
		self.setAttribute('cbs', 0)

		self.dbUpdate()



	def _removeLaOl(self) -> None:
		"""	Remove <latest> and <oldest> virtual child resources.
		"""
		L.isDebug and L.logDebug(f'De-registering latest and oldest virtual resources for: {self.ri}')

		# remove latest
		if len(chs := CSE.dispatcher.retrieveDirectChildResources(self.ri, ResourceTypes.FCNT_LA)) == 1: # type:ignore[no-any-return]
			CSE.dispatcher.deleteLocalResource(chs[0])	# ignore errors
		# remove oldest
		if len(chs := CSE.dispatcher.retrieveDirectChildResources(self.ri, ResourceTypes.FCNT_OL)) == 1: # type:ignore[no-any-return]
			CSE.dispatcher.deleteLocalResource(chs[0])	# ignore errors
	
		self.setAttribute(Constants.attrHasFCI, False)


	def _removeFCIs(self) -> None:
		"""	Remove the FCI childResources.
		"""
		L.isDebug and L.logDebug(f'Removing FCI child resources for: {self.ri}')
		chs = CSE.dispatcher.retrieveDirectChildResources(self.ri, ty = ResourceTypes.FCI)
		for ch in chs:
			# self.childRemoved(r, originator) # It should not be necessary to notify self at this point.
			CSE.dispatcher.deleteLocalResource(ch, parentResource = self)
