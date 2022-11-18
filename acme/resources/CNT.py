#
#	CNT.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: Container
#

from __future__ import annotations
from typing import Optional, cast

from ..etc.Types import AttributePolicyDict, ResourceTypes, Result, ResponseStatusCode, JSON, JSONLIST
from ..etc import Utils, DateUtils
from ..services import CSE
from ..services.Logging import Logging as L
from ..services.Configuration import Configuration
from ..resources.Resource import Resource
from ..resources.AnnounceableResource import AnnounceableResource
from ..resources import Factory


class CNT(AnnounceableResource):

	_allowedChildResourceTypes =  [ ResourceTypes.ACTR,
									ResourceTypes.CNT, 
									ResourceTypes.CIN,
									ResourceTypes.FCNT,
									ResourceTypes.SMD,
									ResourceTypes.SUB,
									ResourceTypes.TS ]

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


	def __init__(self, dct:Optional[JSON] = None, 
					   pi:Optional[str] = None, 
					   create:Optional[bool] = False) -> None:
		super().__init__(ResourceTypes.CNT, dct, pi, create = create)

		if Configuration.get('cse.cnt.enableLimits'):	# Only when limits are enabled
			self.setAttribute('mni', Configuration.get('cse.cnt.mni'), overwrite = False)
			self.setAttribute('mbs', Configuration.get('cse.cnt.mbs'), overwrite = False)
		self.setAttribute('cni', 0, overwrite = False)
		self.setAttribute('cbs', 0, overwrite = False)
		self.setAttribute('st', 0, overwrite = False)

		self.__validating = False	# semaphore for validating


	def activate(self, parentResource:Resource, originator:str) -> Result:
		if not (res := super().activate(parentResource, originator)).status:
			return res
		
		# register latest and oldest virtual resources
		L.isDebug and L.logDebug(f'Registering latest and oldest virtual resources for: {self.ri}')

		# add latest
		latestResource = Factory.resourceFromDict({}, pi = self.ri, ty = ResourceTypes.CNT_LA).resource		# rn is assigned by resource itself
		if not (res := CSE.dispatcher.createLocalResource(latestResource)).resource:
			return Result(status = False, rsc = res.rsc, dbg = res.dbg)

		# add oldest
		oldestResource = Factory.resourceFromDict({}, pi = self.ri, ty = ResourceTypes.CNT_OL).resource		# rn is assigned by resource itself
		if not (res := CSE.dispatcher.createLocalResource(oldestResource)).resource:
			return Result(status = False, rsc = res.rsc, dbg = res.dbg)

		return Result.successResult()


	def update(self, dct:JSON = None, originator:Optional[str] = None, doValidateAttributes:Optional[bool] = True) -> Result:

		# remember disr update first, handle later after the update
		disrOrg = self.disr
		disrNew = Utils.findXPath(dct, '{*}/disr')

		# Generic update
		if not (res := super().update(dct, originator)).status:
			return res
		
		# handle disr: delete all <cin> when disr was set to TRUE and is now FALSE.
		#if disrOrg is not None and disrOrg == True and disrNew is not None and disrNew == False:
		if disrOrg and disrNew == False:
			CSE.dispatcher.deleteChildResources(self, originator, ty = ResourceTypes.CIN)

		# Update stateTag when modified
		self.setAttribute('st', self.st + 1)

		return Result.successResult()


	def childWillBeAdded(self, childResource:Resource, originator:str) -> Result:
		if not (res := super().childWillBeAdded(childResource, originator)).status:
			return res
		
		# Check whether the child's rn is "ol" or "la".
		# TODO check necessary?
		if (rn := childResource.rn) is not None and rn in ['ol', 'la']:
			return Result.errorResult(rsc = ResponseStatusCode.operationNotAllowed, dbg = 'resource types "latest" or "oldest" cannot be added')
	
		# Check whether the size of the CIN doesn't exceed the mbs
		if childResource.ty == ResourceTypes.CIN and self.mbs is not None:
			if childResource.cs is not None and childResource.cs > self.mbs:
				return Result.errorResult(rsc = ResponseStatusCode.notAcceptable, dbg = 'child content sizes would exceed mbs')
		return Result.successResult()


	# Handle the addition of new CIN. Basically, get rid of old ones.
	def childAdded(self, childResource:Resource, originator:str) -> None:
		L.isDebug and L.logDebug(f'Child resource added: {childResource.ri}')
		super().childAdded(childResource, originator)
		if childResource.ty == ResourceTypes.CIN:	# Validate if child is CIN

			# Check for mia handling. This sets the et attribute in the CIN
			if self.mia is not None:
				# Take either mia or the maxExpirationDelta, whatever is smaller. 
				# Don't change if maxExpirationDelta is 0.
				maxEt = DateUtils.getResourceDate(self.mia 
												  if self.mia <= CSE.request.maxExpirationDelta 
												  else CSE.request.maxExpirationDelta)
				# Only replace the childresource's et if it is greater than the calculated maxEt
				if childResource.et > maxEt:
					childResource.setAttribute('et', maxEt)
					childResource.dbUpdate()

			self.validate(originator)


	# Handle the removal of a CIN. 
	def childRemoved(self, childResource:Resource, originator:str) -> None:
		L.isDebug and L.logDebug(f'Child resource removed: {childResource.ri}')
		super().childRemoved(childResource, originator)
		if childResource.ty == ResourceTypes.CIN:	# Validate if child was CIN
			self._validateChildren()


	# Validating the Container. This means recalculating cni, cbs as well as
	# removing ContentInstances when the limits are met.
	def validate(self, originator:Optional[str] = None, 
					   create:Optional[bool] = False, 
					   dct:Optional[JSON] = None, 
					   parentResource:Optional[Resource] = None) -> Result:
		if (res := super().validate(originator, create, dct, parentResource)).status == False:
			return res
		self._validateChildren()
		return Result.successResult()


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

		# Only get the CINs in raw format. Instantiate them as resources if needed
		cinsRaw = cast(JSONLIST, sorted(CSE.storage.directChildResources(self.ri, ResourceTypes.CIN, raw = True), key = lambda x: x['ct']))
		cni = len(cinsRaw)			
			
		# Check number of instances
		if (mni := self.mni) is not None:
			while cni > mni and cni > 0:
				# Only instantiate the <cin> when needed here for deletion
				cin = Factory.resourceFromDict(cinsRaw[0]).resource
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
		if (mbs := self.mbs) is not None:
			while cbs > mbs and cbs > 0:
				# Only instantiate the <cin> when needed here for deletion
				cin = Factory.resourceFromDict(cinsRaw[0]).resource
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
		self.dbUpdate()
	
		# End validating
		self.__validating = False

