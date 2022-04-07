#
#	CNT.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: Container
#

from __future__ import annotations
from typing import List
from ..etc.Types import AttributePolicyDict, ResourceTypes as T, Result, ResponseStatusCode as RC, JSON
from ..etc import Utils, DateUtils
from ..services import CSE as CSE
from ..services.Logging import Logging as L
from ..services.Configuration import Configuration
from ..resources.Resource import *
from .AnnounceableResource import AnnounceableResource
from ..resources import Factory


class CNT(AnnounceableResource):

	_allowedChildResourceTypes =  [ T.ACTR, T.CNT, T.CIN, T.FCNT, T.SUB, T.TS ]

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
			'disr': None
	}


	def __init__(self, dct:JSON = None, pi:str = None, create:bool = False) -> None:
		super().__init__(T.CNT, dct, pi, create=create)

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
		if L.isDebug: L.logDebug(f'Registering latest and oldest virtual resources for: {self.ri}')

		# add latest
		latestResource = Factory.resourceFromDict({}, pi = self.ri, ty = T.CNT_LA).resource		# rn is assigned by resource itself
		if not (res := CSE.dispatcher.createResource(latestResource)).resource:
			return Result(status = False, rsc = res.rsc, dbg = res.dbg)

		# add oldest
		oldestResource = Factory.resourceFromDict({}, pi = self.ri, ty = T.CNT_OL).resource		# rn is assigned by resource itself
		if not (res := CSE.dispatcher.createResource(oldestResource)).resource:
			return Result(status = False, rsc = res.rsc, dbg = res.dbg)

		return Result.successResult()


	def update(self, dct:JSON = None, originator:str = None) -> Result:

		# remember disr update first, handle later after the update
		disrOrg = self.disr
		disrNew = Utils.findXPath(dct, f'{self.tpe}/disr')

		# Generic update
		if not (res := super().update(dct, originator)).status:
			return res
		
		# handle disr: delete all <cin> when disr was set to TRUE and is now FALSE.
		#if disrOrg is not None and disrOrg == True and disrNew is not None and disrNew == False:
		if disrOrg and disrNew == False:
			CSE.dispatcher.deleteChildResources(self, originator, ty=T.CIN)

		# Update stateTag when modified
		self.setAttribute('st', self.st + 1)

		return Result.successResult()


	def childWillBeAdded(self, childResource:Resource, originator:str) -> Result:
		if not (res := super().childWillBeAdded(childResource, originator)).status:
			return res
		
		# Check whether the child's rn is "ol" or "la".
		if (rn := childResource.rn) is not None and rn in ['ol', 'la']:
			return Result.errorResult(rsc = RC.operationNotAllowed, dbg = 'resource types "latest" or "oldest" cannot be added')
	
		# Check whether the size of the CIN doesn't exceed the mbs
		if childResource.ty == T.CIN and self.mbs is not None:
			if childResource.cs is not None and childResource.cs > self.mbs:
				return Result.errorResult(rsc = RC.notAcceptable, dbg = 'child content sizes would exceed mbs')
		return Result.successResult()


	# Handle the addition of new CIN. Basically, get rid of old ones.
	def childAdded(self, childResource:Resource, originator:str) -> None:
		if L.isDebug: L.logDebug(f'Child resource added: {childResource.ri}')
		super().childAdded(childResource, originator)
		if childResource.ty == T.CIN:	# Validate if child is CIN

			# Check for mia handling. This sets the et attribute in the CIN
			if self.mia is not None:
				# Take either mia or the maxExpirationDelta, whatever is smaller
				maxEt = DateUtils.getResourceDate(self.mia if self.mia <= (med := Configuration.get('cse.maxExpirationDelta')) else med)
				# Only replace the childresource's et if it is greater than the calculated maxEt
				if childResource.et > maxEt:
					childResource.setAttribute('et', maxEt)
					childResource.dbUpdate()

			self.validate(originator)


	# Handle the removal of a CIN. 
	def childRemoved(self, childResource:Resource, originator:str) -> None:
		if L.isDebug: L.logDebug(f'Child resource removed: {childResource.ri}')
		super().childRemoved(childResource, originator)
		if childResource.ty == T.CIN:	# Validate if child was CIN
			self._validateChildren()


	# Validating the Container. This means recalculating cni, cbs as well as
	# removing ContentInstances when the limits are met.
	def validate(self, originator:str=None, create:bool = False, dct:JSON = None, parentResource:Resource = None) -> Result:
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
		cinsRaw = cast(List[JSON], sorted(CSE.storage.directChildResources(self.ri, T.CIN, raw = True), key = lambda x: x['ct']))
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
				CSE.dispatcher.deleteResource(cin, parentResource = self, doDeleteCheck = False)
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
				CSE.dispatcher.deleteResource(cin, parentResource = self, doDeleteCheck = False)
				del cinsRaw[0]	# Remove from list
				cni -= 1	# decrement cni when deleting a <cin>

		# Some attributes may have been updated, so store the resource 
		self['cni'] = cni
		self['cbs'] = cbs
		self.dbUpdate()
	
		# End validating
		self.__validating = False

