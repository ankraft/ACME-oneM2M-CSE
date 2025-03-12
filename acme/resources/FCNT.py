#
#	FCNT.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""  FlexContainer (FCNT) resource type."""

from __future__ import annotations
from typing import Optional

from ..etc.Types import AttributePolicyDict, ResourceTypes, JSON
from ..etc.Constants import Constants
from ..etc.ResponseStatusCodes import OPERATION_NOT_ALLOWED, BAD_REQUEST
from ..etc.ACMEUtils import getAttributeSize
from ..etc.DateUtils import getResourceDate
from ..runtime import CSE
from ..runtime.Logging import Logging as L
from ..runtime.Configuration import Configuration
from ..resources import Factory				# attn: circular import
from ..resources.Resource import Resource, internalAttributes, addToInternalAttributes
from ..resources.ContainerResource import ContainerResource
from ..helpers.ResourceSemaphore import criticalResourceSection, inCriticalSection


# Add to internal attributes
addToInternalAttributes(Constants.attrHasFCI)	# Add to internal attributes to ignore in validation etc

class FCNT(ContainerResource):
	""" FlexContainer (FCNT) resource type. """

	resourceType = ResourceTypes.FCNT
	""" The resource type """

	typeShortname = resourceType.typeShortname()
	"""	The resource's domain and type name. """

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
	""" The allowed child-resource types. """

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
		'cni': None,
		'fcied': None,	# EXPERIMENTAL fcinEnabled
	}
	"""	Attributes and `AttributePolicy` for this resource type. """



	def __init__(self, dct:Optional[JSON] = None, typeShortname:Optional[str] = None, create:Optional[bool] = False) -> None:
		self.typeShortname = typeShortname

		# TODO this could be optimized? copy to an internal attribute?
		self.nonCustomAttributes = internalAttributes + [ a for a in self._attributes.keys() ]
		"""	List of attributes that are not custom attributes. """

		super().__init__(dct, create = create)


	def initialize(self, pi:str, originator:str) -> None:
		self.setAttribute('cs', 0, overwrite = False)
		self.setAttribute('st', 0, overwrite = False)

		self.setAttribute(Constants.attrHasFCI, False, False)	# stored in DB

		super().initialize(pi, originator)


	def activate(self, parentResource:Resource, originator:str) -> None:
		super().activate(parentResource, originator)
		
		self.setAttribute('st', 0)

		# Validate containerDefinition
		if (t := CSE.validator.getFlexContainerSpecialization(self.typeShortname)):
			if t[0] != self.cnd:
				raise BAD_REQUEST(L.logDebug(f'Wrong cnd: {self.cnd} for specialization: {self.typeShortname}. Must be: {t[0]}'))

		# Calculate contentSize. Only the custom attribute
		self.setAttribute('cs', sum([getAttributeSize(self[attr]) for attr in self.dict if attr not in self.nonCustomAttributes]))

		# returen if fcinEnabled is not present at all
		if (fcied := self.fcied) is None:
			if any(attr is not None for attr in [self.mni, self.mbs, self.mia]):
				raise BAD_REQUEST('mni, mbs, or mia must not be present when fcied is not present')
			return	# No FCINs necessary

		# fcinEnabled present

		# Check whether any of the mni, mbs, or mia is set to a 0 value
		if any(attr == 0 for attr in [self.mni, self.mbs, self.mia]):
			raise BAD_REQUEST('mni, mbs, or mia must not be set to 0')

		# Set mni, mbn and mia to the default values if not present
		if Configuration.resource_fcnt_enableLimits:
			self.setAttribute('mni', Configuration.resource_fcnt_mni, overwrite = False)
			self.setAttribute('mbs', Configuration.resource_fcnt_mbs, overwrite = False)
			self.setAttribute('mia', Configuration.resource_fcnt_mia, overwrite = False)

		# Check any of mni, mbs, or mia is present in the request with a value of 0
		if any(attr == 0 for attr in [self.mni, self.mbs, self.mia]):
			raise BAD_REQUEST('mni, mbs, or mia must not be set to 0 when fcied is set')

		# Check whether self.mbs < self.cs
		if self.mbs is not None and self.mbs < self.cs:
			raise BAD_REQUEST('mbs must be greater or equal to the sum of the sizes of all custom attributes')

		# Add <latest> and <oldest> virtual child resources
		self.prepareForInstances()

		# Create FCIN
		self.addFlexContainerInstance(originator)


		# Set the cbs and cni attributes
		self.setAttribute('cni', 1)
		self.setAttribute('cbs', self.cs)



	@criticalResourceSection('FCNT', 'update')	# Set an indicator that this resource is in update
	def update(self, dct:Optional[JSON] = None, 
					 originator:Optional[str] = None, 
					 doValidateAttributes:Optional[bool] = True) -> None:

		# Increment stateTag
		self.setAttribute('st', self.st + 1)

		# Calculate contentSize. Only the custom attributes, but all of them and the finalized version
		self.setAttribute('cs', sum([getAttributeSize(self.getFinalResourceAttribute(attr, dct)) 
							   		 for attr in self.dict 
									 if attr not in self.nonCustomAttributes]))

		# Check whether the fcied attribute is present in the update request
		_dct = dct[self.typeShortname]
		fcied = None
		if 'fcied' in _dct:
			fcied = _dct['fcied']

			if fcied is None:
				L.isDebug and L.logDebug('Removing fcied and related attributes')
				# Check whether fcied is removed but mbs, mni, or mia is present in the request
				if any(attr is not None for attr in [_dct.get('mni'), _dct.get('mbs'), _dct.get('mia')]):
					raise BAD_REQUEST('mni, mbs, or mia must not be present with values when fcied is removed')

				# Remove cni, cbs, mbs, mni, mia
				self.delAttribute('cni')
				self.delAttribute('cbs')
				self.delAttribute('mbs')
				self.delAttribute('mni')
				self.delAttribute('mia')

				# Remove the virtual resources and FCINs
				self.cleanUpInstances()

				super().update(dct, originator, doValidateAttributes)
				return
		
		# fcied present in the final resource?
		finFcied = self.getFinalResourceAttribute('fcied', dct)
		
		# fcied IS NOT present in the final resource
		if finFcied is None: 
			# Check whether any of the mni, mbs, or mia is set to a value in the request
			if any(attr is not None for attr in [_dct.get('mni'), _dct.get('mbs'), _dct.get('mia')]):
				raise BAD_REQUEST('mni, mbs, or mia must not be present with values when fcied is not present')
			
			# We are done here
			super().update(dct, originator, doValidateAttributes)
			return
		
		# else: fcied IS present in the final resource

		# Check any of mni, mbs, or mia is present in the request with a value of 0
		if any(attr == 0 for attr in [_dct.get('mni'), _dct.get('mbs'), _dct.get('mia')]):
			raise BAD_REQUEST('mni, mbs, or mia must not be set to 0 when fcied is set')

		# Handle <fcinEnabled> set to false
		if finFcied == False:
			if self.fcied == finFcied:	# No change
				L.isDebug and L.logDebug('fcied set to false, was: false')
				super().update(dct, originator, doValidateAttributes)
				return
			if self.fcied is None:	# Previously not set at all, no fcin expected
				L.isDebug and L.logDebug('fcied set to false, was: None')
				self.addFlexContainerInstance(originator)	# Add a new FCIN
			# delete all except the latest FCIN
			L.isDebug and L.logDebug('Removing all FCINs except the latest')
			self.cleanUpInstances(onlyInstances = True, keepLatest = True)
			self.setAttribute('cni', 1)
			self.setAttribute('cbs', self.cs)
			super().update(dct, originator, doValidateAttributes)
			return
		
		# From here on the final <fcinEnabled> is assumed true

		# <fcinEnabled> set to true and was false before? (newly enabled)
		if self.fcied == False or self.fcied is None:
			# Add cbs and cni
			self.setAttribute('cbs', 0)
			self.setAttribute('cni', 0)

			# Add <latest> and <oldest> virtual child resources
			self.prepareForInstances()

		finMni = self.getFinalResourceAttribute('mni', dct)
		finMbs = self.getFinalResourceAttribute('mbs', dct)

		# Set mni, mbs and mia to the default values if not present
		if self.getFinalResourceAttribute('mni', dct) is None and \
			self.getFinalResourceAttribute('mbs', dct) is None and \
			self.getFinalResourceAttribute('mia', dct) is None and \
			Configuration.resource_fcnt_enableLimits:	# Only when limits are enabled
				self.setAttribute('mni', Configuration.resource_fcnt_mni, overwrite = False)
				self.setAttribute('mbs', Configuration.resource_fcnt_mbs, overwrite = False)
				self.setAttribute('mia', Configuration.resource_fcnt_mia, overwrite = False)

		# Update cbs and cni if any of the custom attributes or lbl is present in the request
		needsFcin = False
		if any([each not in self.nonCustomAttributes or each in [ 'lbl' ] for each in _dct.keys()]):
			needsFcin = True
			self.setAttribute('cbs', self.cbs + self.cs)
			self.setAttribute('cni', self.cni + 1)

		# OR Check whether fcied if present in the request AND is no present with True in the resource
		elif fcied == True and self.fcied != True:
			needsFcin = True
			self.setAttribute('cbs', self.cbs + self.cs)
			self.setAttribute('cni', self.cni + 1)
		
		# Else fall-through
		else:
			pass


		fcis = self.flexContainerInstances()	# already sorted by st
		cni = self.cni	# number of instances # TODO sanity check here?
		cbs = self.cbs
		fci:Resource = None

		# Handle the mbs invariant
		if finMbs is not None:
			# Is the request's content size greater than the mbs?
			if finMbs < self.cs:
				raise BAD_REQUEST(f'mbs:{finMbs} must be greater or equal to the sum:{self.cs} of the sizes of all custom attributes in the request')
			
			# check size
			while cbs > finMbs and cbs > 0:
				# remove oldest
				fci = fcis[0]
				L.isDebug and L.logDebug(f'cbs:{cbs} > mbs:{finMbs} - Removing <fci>:{fci.ri}')
				# Deleting a child must not cause a notification for 'deleteDirectChild'.
				# Don't do a delete check means that FCNT.childRemoved() is not called, where subscriptions for 'deleteDirectChild'  is tested.
				CSE.dispatcher.deleteLocalResource(fci, parentResource = self, doDeleteCheck = False)
				del fcis[0]
				cbs -= fci.cs			
				cni -= 1	# decrement cni when deleting a cni

		# Handle the mni invariant
		if finMni is not None:
			# check mni
			while cni > finMni and cni > 0:
				fci = fcis[0]
				L.isDebug and L.logDebug(f'cni:{cni} > mni:{finMni} - Removing <fci>: {fci.ri}')
				# remove oldest
				# Deleting a child must not cause a notification for 'deleteDirectChild'.
				# Don't do a delete check means that FCNT.childRemoved() is not called, where subscriptions for 'deleteDirectChild'  is tested.
				CSE.dispatcher.deleteLocalResource(fci, parentResource = self, doDeleteCheck = False)
				del fcis[0]
				cni -= 1	# decrement cni when deleting a cni
				cbs -= fci.cs

		# Set the resulting cni and cbs
		self.setAttribute('cni', cni)
		self.setAttribute('cbs', cbs)

		# Update self first
		super().update(dct, originator, doValidateAttributes)

		# Add a new FCIN if necessary (if any of the custom attributes or lbl is present in the request)	
		if needsFcin:
			L.isDebug and L.logDebug('Adding flexContainerInstance')
			self.addFlexContainerInstance(originator)
		else:
			L.isDebug and L.logDebug('No new FCIN necessary')


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


	# Handle the removal of a FCI. 
	def childRemoved(self, childResource:Resource, originator:str) -> None:
		if inCriticalSection('FCNT', 'update'):	# Ignore when in update
			return
		
		L.isDebug and L.logDebug(f'Child resource removed: {childResource.ri}')
		super().childRemoved(childResource, originator)
		if childResource.ty == ResourceTypes.FCI:	# Validate if child was CIN
			self.instanceRemoved(childResource)		# Update cni and cbs
			self.dbUpdate(True)



	def hasAttributeDefined(self, name:str) -> bool:
		if super().hasAttributeDefined(name):
			return True
		# Check whether the attribute is defined in the containerDefinition
		return name in CSE.validator.getFlexContainerAttributesFor(self.typeShortname).keys()
		

	def flexContainerInstances(self) -> list[Resource]:
		"""	Get all flexContainerInstances of a resource and return a sorted (by st) list
		""" 
		return sorted(CSE.dispatcher.retrieveDirectChildResources(self.ri, ResourceTypes.FCI), key = lambda x: x.st) # type:ignore[no-any-return]


	# Add a new FlexContainerInstance for this flexContainer
	def addFlexContainerInstance(self, originator:str) -> None:
		"""	Add a new FlexContainerInstance for this flexContainer.

			Args:
				originator: The originator of the request.
		"""

		L.isDebug and L.logDebug('Adding flexContainerInstance')

		dct:JSON = { 'rn'  : f'{self.rn}_{self.st:d}', }

		# Copy the label as well
		if self.lbl:
			dct['lbl'] = self.lbl
		
		for attr in self.dict:
			if attr not in self.nonCustomAttributes:
				dct[attr] = self[attr]
				continue
			# special for at attribute. It might contain additional id's when it
			# is announced. Those we don't want to copy.
			if attr == 'at':
				dct['at'] = [ x for x in self['at'] if x.count('/') == 1 ]	# Only copy single csi in at

		# Check for mia handling
		if (_mia := self.mia) is not None:	# mia is an int
			# Take either mia or the maxExpirationDelta, whatever is smaller
			maxEt = getResourceDate(_mia 
									if _mia <= Configuration.cse_maxExpirationDelta 
									else Configuration.cse_maxExpirationDelta)
			L.isDebug and L.logDebug(f'Adding FCI with maxEt: {maxEt} for mia: {_mia}')
			dct['et'] = maxEt

		dct['org'] = originator
		dct['st'] = self.st
		dct['cs'] = self.cs
		fciRes = Factory.resourceFromDict(resDict = { self.typeShortname : dct }, 
										  pi = self.ri, 
										  ty = ResourceTypes.FCI,
										  create = True,
										  originator = originator)
		fciRes.setAttribute(Constants.attrIsManuallyInstantiated, True)	# Mark as instantiated to avoid validation



		CSE.dispatcher.createLocalResource(fciRes, self, originator = originator)


	def prepareForInstances(self) -> None:
		"""	Add <latest> and <oldest> virtual child resources.
		"""
		if self.fcied is None:
			return
		
		if self[Constants.attrHasFCI]:	# Not necessary
			return
		
		L.isDebug and L.logDebug(f'Registering latest and oldest virtual resources for: {self.ri}')

		# add latest
		resource = Factory.resourceFromDict({ 'et': self.et }, 
											pi = self.ri, 
											ty = ResourceTypes.FCNT_LA,
											create = True,
											originator = self.getOriginator())	# rn is assigned by resource itself
		resource = CSE.dispatcher.createLocalResource(resource, self)
		self.setLatestRI(resource.ri)


		# add oldest
		resource = Factory.resourceFromDict({ 'et': self.et }, 
											pi = self.ri, 
											ty = ResourceTypes.FCNT_OL,
											create = True,
											originator = self.getOriginator())	# rn is assigned by resource itself
		resource = CSE.dispatcher.createLocalResource(resource, self)
		self.setOldestRI(resource.ri)
		
		# Set the hasFCI attribute to indicate that the virtual resources are present
		self.setAttribute(Constants.attrHasFCI, True)
	
		# need to update the resource here
		self.dbUpdate()	


	def cleanUpInstances(self, onlyInstances:bool = True, keepLatest:bool = False) -> None:
		"""	Remove <latest> and <oldest> virtual child resources.

			Args:
				onlyInstances: Only remove the FCINs, not the virtual resources.
				keepLatest: Keep the latest resource. Only remove the oldest resource.
		"""
		if not self[Constants.attrHasFCI]:	# Not necessary
			return

		self._removeFCIs(keepLatest)
		if onlyInstances:
			return
		self._removeLaOl()
		self.setAttribute(Constants.attrHasFCI, False)
		# No dbUpdate necessary, because the resource is not changed


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


	def _removeFCIs(self, keepLatest:bool = False) -> None:
		"""	Remove the FCI childResources.

			Args:
				keepLatest: Keep the latest resource. Only remove the oldest resource.
		"""
		L.isDebug and L.logDebug(f'Removing FCI child resources for: {self.ri}')
		chs = CSE.dispatcher.retrieveDirectChildResources(self.ri, ty = ResourceTypes.FCI)
		
		# keepLatest is set, then remove all but the latest
		if keepLatest:
			chs = sorted(chs, key = lambda x: x.ct)
			chs = chs[:-1]	# Remove all but the latest

		for ch in chs:
			CSE.dispatcher.deleteLocalResource(ch, parentResource = self)
