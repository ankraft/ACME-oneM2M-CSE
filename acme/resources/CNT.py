#
#	CNT.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: Container
#
""" Container (CNT) resource type.
"""

from __future__ import annotations
from typing import Optional, cast

from ..etc.Types import AttributePolicyDict, ResourceTypes, JSON, JSONLIST
from ..etc.ResponseStatusCodes import NOT_ACCEPTABLE
from ..etc.DateUtils import getResourceDate
from ..helpers.TextTools import findXPath
from ..runtime import CSE
from ..runtime.Logging import Logging as L
from ..runtime.Configuration import Configuration
from ..resources.Resource import Resource
from ..resources.ContainerResource import ContainerResource
from ..resources import Factory	# attn: circular import


class CNT(ContainerResource):
	""" Container resource type. """

	resourceType = ResourceTypes.CNT
	""" The resource type """

	typeShortname = resourceType.typeShortname()
	"""	The resource's domain and type name. """


	_allowedChildResourceTypes =  [ ResourceTypes.ACTR,
									ResourceTypes.CNT, 
									ResourceTypes.CIN,
									ResourceTypes.FCNT,
									ResourceTypes.SMD,
									ResourceTypes.SUB,
									ResourceTypes.TS,
									ResourceTypes.CNT_LA,
									ResourceTypes.CNT_OL ]
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
		'mni': None,
		'mbs': None,
		'mia': None,
		'cni': None,
		'cbs': None,
		'li': None,
		'or': None,
		'disr': None,

		# EXPERIMENTAL
		'subi': None,
	}		
	"""	Attributes and `AttributePolicy` for this resource type. """


	def __init__(self, dct:Optional[JSON] = None, create:Optional[bool] = False) -> None:
		super().__init__(dct, create = create)
		self.__validating = False	# semaphore for validating


	def initialize(self, pi:str, originator:str) -> None:
		self.setAttribute('cni', 0, overwrite = False)
		self.setAttribute('cbs', 0, overwrite = False)
		self.setAttribute('st', 0, overwrite = False)
		super().initialize(pi, originator)

	def activate(self, parentResource:Resource, originator:str) -> None:
		super().activate(parentResource, originator)

		# Set the limits for this container if enabled
		# TODO optimize this
		if Configuration.resource_cnt_enableLimits:	# Only when limits are enabled
			self.setAttribute('mni', Configuration.resource_cnt_mni, overwrite = False)
			self.setAttribute('mbs', Configuration.resource_cnt_mbs, overwrite = False)
			self.setAttribute('mia', Configuration.resource_cnt_mia, overwrite = False)

		# register latest and oldest virtual resources
		L.isDebug and L.logDebug(f'Registering latest and oldest virtual resources for: {self.ri}')

		# add latest
		latestResource = Factory.resourceFromDict({ 'et': self.et }, 
													pi = self.ri, 
													ty = ResourceTypes.CNT_LA,
													create = True,
													originator = originator)		# rn is assigned by resource itself
		resource = CSE.dispatcher.createLocalResource(latestResource, self)
		self.setLatestRI(resource.ri)

		# add oldest
		oldestResource = Factory.resourceFromDict({ 'et': self.et }, 
													pi = self.ri, 
													ty = ResourceTypes.CNT_OL,
													create = True,
													originator = originator)		# rn is assigned by resource itself
		resource = CSE.dispatcher.createLocalResource(oldestResource, self)
		self.setOldestRI(resource.ri)


	def update(self, dct:JSON = None, 
					 originator:Optional[str] = None, 
					 doValidateAttributes:Optional[bool] = True) -> None:

		# remember disr update first, handle later after the update
		disrOrg = self.disr
		disrNew = findXPath(dct, 'm2m:cnt/disr')	# TODO or pureResource?

		# Generic update
		super().update(dct, originator, doValidateAttributes)
		
		# handle disr: delete all <cin> when disr was set to TRUE and is now FALSE.
		if disrOrg and disrNew == False:
			CSE.dispatcher.deleteChildResources(self, originator, ty = ResourceTypes.CIN)

		# add default values for cni, cbs and mia if not present
		if self.getFinalResourceAttribute('mni', dct) is None and \
			self.getFinalResourceAttribute('mbs', dct) is None and \
			self.getFinalResourceAttribute('mia', dct) is None and \
			Configuration.resource_cnt_enableLimits:	# Only when limits are enabled
				self.setAttribute('mni', Configuration.resource_cnt_mni, overwrite = False)
				self.setAttribute('mbs', Configuration.resource_cnt_mbs, overwrite = False)
				self.setAttribute('mia', Configuration.resource_cnt_mia, overwrite = False)

		# Update stateTag when modified
		self.setAttribute('st', self.st + 1)


	def childWillBeAdded(self, childResource:Resource, originator:str) -> None:
		super().childWillBeAdded(childResource, originator)
		
		# Check whether the child's rn is "ol" or "la".
		# TODO check necessary?
		# if (rn := childResource.rn) is not None and rn in ['ol', 'la']:
		# 	return Result.errorResult(rsc = ResponseStatusCode.operationNotAllowed, dbg = 'resource types "latest" or "oldest" cannot be added')
	
		# Check whether the size of the CIN doesn't exceed the mbs
		if childResource.ty == ResourceTypes.CIN and self.mbs is not None:
			if childResource.cs is not None and childResource.cs > self.mbs:
				raise NOT_ACCEPTABLE('child content sizes would exceed mbs')


	# Handle the addition of new CIN. Basically, get rid of old ones.
	def childAdded(self, childResource:Resource, originator:str) -> None:
		L.isDebug and L.logDebug(f'Child resource added: {childResource.ri}')
		super().childAdded(childResource, originator)
		if childResource.ty == ResourceTypes.CIN:	# Validate if child is CIN

			# Check for mia handling. This sets the et attribute in the CIN
			if (mia := self.mia) is not None:
				# Take either mia or the maxExpirationDelta, whatever is smaller. 
				# Don't change if maxExpirationDelta is 0.
				maxEt = getResourceDate(mia 
									    if mia <= CSE.request.maxExpirationDelta 
									    else CSE.request.maxExpirationDelta)
				# Only replace the childresource's et if it is greater than the calculated maxEt
				if childResource.et > maxEt:
					childResource.setAttribute('et', maxEt)
					childResource.dbUpdate()

			self.instanceAdded(childResource)
			self.validate(originator)
			self.updateLaOlLatestTimestamp()	# EXPERIMENTAL TODO Also do in FCNT and TS

			# Send update event on behalf of the latest resources.
			# The oldest resource might not be changed. That is handled in the validate() method.
			CSE.event.changeResource(childResource, self.getLatestRI())	 # type: ignore [attr-defined]



	# Handle the removal of a CIN. 
	def childRemoved(self, childResource:Resource, originator:str) -> None:
		L.isDebug and L.logDebug(f'Child resource removed: {childResource.ri}')
		super().childRemoved(childResource, originator)
		if childResource.ty == ResourceTypes.CIN:	# Validate if child was CIN
			self.instanceRemoved(childResource)		# Update cni and cbs
			self.dbUpdate(True)


	# Validating the Container. This means recalculating cni, cbs as well as
	# removing ContentInstances when the limits are met.
	def validate(self, originator:Optional[str] = None, 
					   dct:Optional[JSON] = None, 
					   parentResource:Optional[Resource] = None) -> None:
		super().validate(originator, dct, parentResource)
		self._validateChildren()


	# TODO Align this and FCNT implementations
	# TODO use raw for TS and TCNT
	
	def _validateChildren(self) -> None:
		""" Internal validation and checks. This called more often then just from
			the validate() method.
		"""
		# Check whether we already are in validation the children (ie prevent unfortunate recursion by the Dispatcher)
		if self.__validating:
			return
		self.__validating = True

		# No validation needed if no limits set
		mni = self.mni
		mbs = self.mbs
		if mbs is None and mni is None:
			self.dbUpdate(True)
			return
		
		# TODO optimize the following a bit. 
		# - only when cni/cbs > limits


		# Only get the CINs in raw format. Instantiate them as resources if needed
		cinsRaw = cast(JSONLIST, sorted(CSE.storage.directChildResources(self.ri, ResourceTypes.CIN, raw = True), key = lambda x: x['ct']))
		cni = len(cinsRaw)			
		cin:Resource = None

		# Check number of instances
		if mni is not None:
			while cni > mni and cni > 0:
				# Only instantiate the <cin> when needed here for deletion
				cin = Factory.resourceFromDict(cinsRaw[0])
				L.isDebug and L.logDebug(f'cni > mni: Removing <cin>: {cin.ri}')
				# remove oldest
				# Deleting a child must not cause a notification for 'deleteDirectChild'.
				# Don't do a delete check means that CNT.childRemoved() is not called, where subscriptions for 'deleteDirectChild'  is tested.
				CSE.dispatcher.deleteLocalResource(cin, parentResource = self, doDeleteCheck = False)
				del cinsRaw[0]	# Remove from list
				cni -= 1	# decrement cni when deleting a <cin>

		# Calculate cbs of remaining cins
		cbs = sum([ each['cs'] for each in cinsRaw])

		# check size
		if mbs is not None:
			while cbs > mbs and cbs > 0:
				# Only instantiate the <cin> when needed here for deletion
				cin = Factory.resourceFromDict(cinsRaw[0])
				L.isDebug and L.logDebug(f'cbs > mbs: Removing <cin>: {cin.ri}')
				# remove oldest
				cbs -= cin.cs
				# Deleting a child must not cause a notification for 'deleteDirectChild'.
				# Don't do a delete check means that CNT.childRemoved() is not called, where subscriptions for 'deleteDirectChild'  is tested.
				CSE.dispatcher.deleteLocalResource(cin, parentResource = self, doDeleteCheck = False)
				del cinsRaw[0]	# Remove from list
				cni -= 1	# decrement cni when deleting a <cin>

		# Some attributes may have been updated, so store the resource 
		self['cni'] = cni
		self['cbs'] = cbs
		self.dbUpdate(True)

		# If cin is not None anymore then we have a new "oldest" resource.
		# cin is NOT the oldest resource, but the one that was deleted last. The new
		# oldest resource is the first in the list of cinsRaw.
		# This means that we need to send an "update" event for the oldest resource.
		if cin is not None and len(cinsRaw):
			CSE.event.changeResource(Factory.resourceFromDict(cinsRaw[0]), self.getOldestRI())	 # type: ignore [attr-defined]
	
		# End validating
		self.__validating = False


	def setLCPLink(self, lcpRi:str) -> None:
		"""	Set the link to the <lcp> resource. This is called from the <lcp> resource.
			This also sets the link in the <latest> resource.
		
			Args:
				lcpRi:	The resource id of the <lcp> resource.
		"""

		self.setAttribute('li', lcpRi)

		# Also, set in the <latest> resource
		if (latest := CSE.dispatcher.retrieveLocalResource(self.getLatestRI())) is not None:
			latest.setLCPLink(lcpRi)
			latest.dbUpdate()

		self.dbUpdate()
