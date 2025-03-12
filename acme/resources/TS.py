#
#	TS.py
#
#	(c) 2021 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: TimeSeries
#

from __future__ import annotations
from typing import Optional

from ..etc.Types import AttributePolicyDict, ResourceTypes, JSON
from ..etc.ResponseStatusCodes import BAD_REQUEST, OPERATION_NOT_ALLOWED, NOT_ACCEPTABLE, CONFLICT
from ..helpers.TextTools import findXPath
from ..etc.DateUtils import getResourceDate, toISO8601Date
from ..runtime.Configuration import Configuration
from ..runtime import CSE
from ..runtime.Logging import Logging as L
from ..resources.Resource import Resource
from ..resources.ContainerResource import ContainerResource
from ..resources import Factory		# attn: circular import


# CSE default:
#	- peid is set to pei/2 if ommitted, and pei is set

class TS(ContainerResource):

	resourceType = ResourceTypes.TS
	""" The resource type """

	typeShortname = resourceType.typeShortname()
	"""	The resource's domain and type name. """

	# Specify the allowed child-resource types
	_allowedChildResourceTypes = [ ResourceTypes.ACTR, 
								   ResourceTypes.TSI, 
								   ResourceTypes.SMD, 
								   ResourceTypes.SUB,
								   ResourceTypes.TS_LA,
								   ResourceTypes.TS_OL ]

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
		'cr': None,
		'loc': None,

		# Resource attributes
		'mni': None,
		'mbs': None,
		'mia': None,
		'cni': None,
		'cbs': None,
		'pei': None,
		'peid': None,
		'mdd': None,
		'mdn': None,
		'mdlt': None,
		'mdc': None,
		'mdt': None,
		'cnf': None,
		'or': None,
	}


	def initialize(self, pi:str, originator:str) -> None:
		self.setAttribute('mdd', False, overwrite = False)	# Default is False if not provided
		self.setAttribute('cni', 0, overwrite = False)
		self.setAttribute('cbs', 0, overwrite = False)
		self.setAttribute('mdc', 0, overwrite = False)
		if Configuration.resource_ts_enableLimits:	# Only when limits are enabled
			self.setAttribute('mni', Configuration.resource_ts_mni, overwrite = False)
			self.setAttribute('mbs', Configuration.resource_ts_mbs, overwrite = False)
			self.setAttribute('mdn', Configuration.resource_ts_mdn, overwrite = False)

		self.__validating = False	# semaphore for validating
		
		super().initialize(pi, originator)


	def activate(self, parentResource:Resource, originator:str) -> None:
		super().activate(parentResource, originator)

		# Validation of CREATE is done in self.validate()

		# register latest and oldest virtual resources
		L.isDebug and L.logDebug(f'Registering latest and oldest virtual resources for: {self.ri}')

		# add latest
		resource = Factory.resourceFromDict({ 'et': self.et }, 
										    pi = self.ri, 
										    ty = ResourceTypes.TS_LA,
											create = True,
											originator = originator)	# rn is assigned by resource itself
		CSE.dispatcher.createLocalResource(resource, self)
		self.setLatestRI(resource.ri)	# Set the latest resource ID

		# add oldest
		resource = Factory.resourceFromDict({ 'et': self.et }, 
										    pi = self.ri, 
										    ty = ResourceTypes.TS_OL,
											create = True,
											originator = originator)	# rn is assigned by resource itself
		CSE.dispatcher.createLocalResource(resource, self)
		self.setOldestRI(resource.ri)	# Set the oldest resource ID

		# Set mni, mbn and mia to the default values if not present
		if Configuration.resource_ts_enableLimits:
			self.setAttribute('mni', Configuration.resource_ts_mni, overwrite = False)
			self.setAttribute('mbs', Configuration.resource_ts_mbs, overwrite = False)
			self.setAttribute('mia', Configuration.resource_ts_mia, overwrite = False)
		
		self._validateDataDetect()


	def deactivate(self, originator:str, parentResource:Resource) -> None:
		super().deactivate(originator, parentResource)
		CSE.timeSeries.stopMonitoringTimeSeries(self.ri)


	def update(self, dct:Optional[JSON] = None, 
					 originator:Optional[str] = None, 
					 doValidateAttributes:Optional[bool] = True) -> None:

		# Extra checks if mdd is present in an update
		updatedAttributes = findXPath(dct, 'm2m:ts')
		
		if (mddNew := updatedAttributes.get('mdd')) is not None:	# boolean
			# Check that mdd is updated alone
			if any(key in ['mdt', 'mdn', 'peid', 'pei'] for key in updatedAttributes.keys()):
				raise BAD_REQUEST(L.logDebug('mdd must not be updated together with mdt, mdn, pei or peid.'))

			# Clear the list if mddNew is deliberatly set to True
			if mddNew == True:
				self._clearMdlt()
				# Restart the monitoring process
				# The actual "restart" is happening when the next TSI is received
				L.isDebug and L.logDebug(f'(Re)Start monitoring <TS>: {self.ri}. Actual monitoring begins when first <TSI> is received.')
				CSE.timeSeries.pauseMonitoringTimeSeries(self.ri)
			else:
				L.isDebug and L.logDebug(f'Pause monitoring <TS>: {self.ri}')
				CSE.timeSeries.pauseMonitoringTimeSeries(self.ri)
		
		# Check that certain attributes are not updated when mdd is true
		if self.mdd  == True: # existing mdd
			if any(key in ['mdt', 'mdn', 'peid', 'pei'] for key in updatedAttributes.keys()):
				raise BAD_REQUEST(L.logDebug('mdd must not be True when mdt, mdn, pei or peid are updated.'))

		if (peiNew := updatedAttributes.get('pei')) is not None: # integer
			if 'peid' not in updatedAttributes:
				# Add peid if not provided to new attributes, real update below (!)
				updatedAttributes['peid'] = int(peiNew / 2)	# CSE internal policy
		# further pei / peid checks are done in validate()


		if mddNew == True or (mddNew is None and self.mdd == True):	# either mdd is set to True or was and stays True
			mdt = updatedAttributes.get('mdt', self.mdt) 		# old or new value,  default: self.mdt
			peid = updatedAttributes.get('peid', self.peid)		# old or new value, default: self.peid
			if mdt is not None and peid is not None and mdt <= peid:
				raise BAD_REQUEST(L.logDebug('mdt must be > peid'))

		# Set mni, mbs and mia to the default values if not present
		if self.getFinalResourceAttribute('mni', dct) is None and \
			self.getFinalResourceAttribute('mbs', dct) is None and \
			self.getFinalResourceAttribute('mia', dct) is None and \
			Configuration.resource_fcnt_enableLimits:	# Only when limits are enabled
				self.setAttribute('mni', Configuration.resource_ts_mni, overwrite = False)
				self.setAttribute('mbs', Configuration.resource_ts_mbs, overwrite = False)
				self.setAttribute('mia', Configuration.resource_ts_mia, overwrite = False)

		# Check if mdn was changed and shorten mdlt accordingly, if exists
		# shorten the mdlt if a limit is set in mdn
		# if (mdnNew := updatedAttributes.get('mdn') ) is not None:	# integer
		# 	if (mdlt := cast(list, self.mdlt)) and (l := len(mdlt)) > mdnNew:
		# 		mdlt = mdlt[l - mdnNew:]
		# 		self['mdlt'] = mdlt

		# Check if mdt was changed in an update
		# if 'mdt' in updatedAttributes:	# mdt is in the update, either True, False or None!
		# 	mdtNew = updatedAttributes.get('mdt')
		# 	if mdtNew is None and CSE.timeSeries.isMonitored(self.ri):	# it is in the update, but set to None, meaning remove the mdt from the TS
		# 		CSE.timeSeries.stopMonitoringTimeSeries(self.ri)

		# Do real update last
		super().update(dct, originator, doValidateAttributes)
		
		self._validateChildren()	# Check consequences from the update
		self._validateDataDetect(updatedAttributes)

 
	def validate(self, originator:Optional[str] = None, 
					   dct:Optional[JSON] = None, 
					   parentResource:Optional[Resource] = None) -> None:
		L.isDebug and L.logDebug(f'Validating timeSeries: {self.ri}')
		super().validate(originator, dct, parentResource)
		
		# Check the format of the CNF attribute
		if cnf := self.cnf:
			CSE.validator.validateCNF(cnf)

		# Check for peid
		if self.peid is not None and self.pei is not None:	# pei(d) is an int
			if not self.peid <= self.pei/2:	# complicated, but reflects the text in the spec
				raise BAD_REQUEST(L.logDebug('peid must be <= pei/2'))
		elif self.pei is not None:	# pei is an int
			if self.mdt is not None:
				if self.mdt <= self.pei/2:
					self.setAttribute('peid', int(self.mdt/2), False)	# CSE internal policy
				elif self.mdt > self.pei/2:
					self.setAttribute('peid', int(self.pei / 2), False)  # CSE internal policy

		# Checks for MDT
		if self.mdd: # present and True
			# Add mdlt and mdc, if not already added ( No overwrite !)
			self._clearMdlt(False)
			if self.mdt is None:
				raise BAD_REQUEST(L.logDebug('mdt must be set if mdd is True'))
			if self.mdt is not None and self.peid is not None and self.mdt <= self.peid:
				raise BAD_REQUEST(L.logDebug('mdt must be > peid'))
		
		self._validateChildren()	# dbupdate() happens here


	def childWillBeAdded(self, childResource:Resource, originator:str) -> None:
		super().childWillBeAdded(childResource, originator)
		
		# Check whether the child's rn is "ol" or "la".
		if (rn := childResource['rn']) and rn in ['ol', 'la']:
			raise OPERATION_NOT_ALLOWED('resource types "latest" or "oldest" cannot be added')
	
		# Check whether the size of the TSI doesn't exceed the mbs
		if childResource.ty == ResourceTypes.TSI and self.mbs is not None:					# mbs is an int
			if childResource.cs is not None and childResource.cs > self.mbs:	# cs is an int
				raise NOT_ACCEPTABLE('child content sizes would exceed mbs')

		# Check whether another TSI has the same dgt value set
		tsis = CSE.storage.searchByFragment({'ty': ResourceTypes.TSI,
											 'pi': self.ri,
											 'dgt': childResource.dgt})
		if len(tsis) > 0:	# Error if yes
			raise CONFLICT(f'timeSeriesInstance with the same dgt: {childResource.dgt} already exists')


	# Handle the addition of new TSI. Basically, get rid of old ones.
	def childAdded(self, childResource:Resource, originator:str) -> None:
		L.isDebug and L.logDebug(f'Child resource added: {childResource.ri}')
		super().childAdded(childResource, originator)
		match childResource.ty:
			case ResourceTypes.TSI:
				# Check for mia handling. This sets the et attribute in the TSI
				if self.mia is not None:
					# Take either mia or the maxExpirationDelta, whatever is smaller
					maxEt = getResourceDate(self.mia 
											if self.mia <= CSE.request.maxExpirationDelta 
											else CSE.request.maxExpirationDelta)
					# Only replace the childresource's et if it is greater than the calculated maxEt
					if childResource.et > maxEt:
						childResource.setAttribute('et', maxEt)
						childResource.dbUpdate(True)

				self.instanceAdded(childResource)
				self.validate(originator)	# Handle old TSI removals
				self.updateLaOlLatestTimestamp()	# EXPERIMENTAL

				# Add to monitoring if this is enabled for this TS (mdd & pei & mdt are not None, and mdd==True)
				if self.mdd and self.pei is not None and self.mdt is not None:
					CSE.timeSeries.updateTimeSeries(self, childResource)
			
				# Send update event on behalf of the latest resources.
				# The oldest resource might not be changed. That is handled in the validate() method.
				CSE.event.changeResource(childResource, self.getLatestRI())	 # type: ignore [attr-defined]

			case ResourceTypes.SUB:
				# start monitoring
				if childResource['enc/md']:
					CSE.timeSeries.addSubscription(self, childResource)



	# Handle the removal of a TSI. 
	def childRemoved(self, childResource:Resource, originator:str) -> None:
		L.isDebug and L.logDebug(f'Child resource removed: {childResource.ri}')
		super().childRemoved(childResource, originator)
		match childResource.ty:
			case ResourceTypes.TSI:
				# Validate if removed child was TSI
				self._validateChildren()
			case ResourceTypes.SUB:
				if childResource['enc/md']:
					CSE.timeSeries.removeSubscription(self, childResource)


	# handle eventuel updates of subscriptions
	def childUpdated(self, childResource:Resource, updatedAttributes:JSON, originator:str) -> None:
		super().childUpdated(childResource, updatedAttributes, originator)
		if childResource.ty == ResourceTypes.SUB and childResource['enc/md']:
			CSE.timeSeries.updateSubscription(self, childResource)		


	def _validateChildren(self) -> None:
		""" Internal validation and checks. This called more often then just from
			the validate() method.
		"""
		# Check whether we already are in validation the children (ie prevent unfortunate recursion by the Dispatcher)
		if self.__validating:
			return
		self.__validating = True

		# TODO Optimize: Do we really need the resources?
		tsis = self.timeSeriesInstances()	# retrieve TIS child resources
		cni = len(tsis)		
		tsi:Resource = None
			
		# Check number of instances
		if (mni := self.mni) is not None:	# mni is an int
			while cni > mni and cni > 0:
				tsi = tsis[0]
				L.isDebug and L.logDebug(f'cni > mni: Removing <tsi>: {tsi.ri}')
				# remove oldest
				# Deleting a child must not cause a notification for 'deleteDirectChild'.
				# Don't do a delete check means that TS.childRemoved() is not called, where subscriptions for 'deleteDirectChild'  is tested.
				CSE.dispatcher.deleteLocalResource(tsi, parentResource = self, doDeleteCheck = False)
				del tsis[0]
				cni -= 1	# decrement cni when deleting a <cin>

		# Calculate cbs
		cbs = sum([ each.cs for each in tsis])

		# check size
		if (mbs := self.mbs) is not None:
			while cbs > mbs and cbs > 0:
				tsi = tsis[0]
				L.isDebug and L.logDebug(f'cbs > mbs: Removing <tsi>: {tsi.ri}')
				# remove oldest
				# cbs -= tsis[0]['cs']
				cbs -= tsi.cs
				# Deleting a child must not cause a notification for 'deleteDirectChild'.
				# Don't do a delete check means that TS.childRemoved() is not called, where subscriptions for 'deleteDirectChild'  is tested.
				CSE.dispatcher.deleteLocalResource(tsi, parentResource = self, doDeleteCheck = False)
				del tsis[0]
				cni -= 1	# decrement cni when deleting a <tsi>

		# Some attributes may have been updated, so store the resource 
		self['cni'] = cni
		self['cbs'] = cbs
		self.dbUpdate(True)
	
		# If tsi is not None anymore then we have a new "oldest" resource.
		# tsi is NOT the oldest resource, but the one that was deleted last. The new
		# oldest resource is the first in the list of tsis.
		# This means that we need to send an "update" event for the oldest resource.
		if tsi is not None and len(tsis) > 0:
			CSE.event.changeResource(tsis[0], self.getOldestRI())	 # type: ignore [attr-defined]

		# End validating
		self.__validating = False


	def _validateDataDetect(self, updatedAttributes:Optional[JSON] = None) -> None:
		"""	This method checks and enables or disables certain data detect monitoring attributes.
		"""
		L.isDebug and L.logDebug('Validating data detection')

		mdd = self.mdd
		
		# If any of mdd, pei or mdt becomes None, or is mdd==False, then stop monitoring this TS
		if not mdd or not self.pei or not self.mdt:
			if CSE.timeSeries.isMonitored(self.ri):
				CSE.timeSeries.pauseMonitoringTimeSeries(self.ri)


        # If any parameters related to the missing data detection process (missingDataDetectTimer, missingDataMaxNr,
        # periodicIntervalDelta, periodicInterval) are updated while the data detection process is paused the Hosting CSE
        # will clear the missingDataList and missingDataCurrentNr.
		if self.mdd  == False:
			if updatedAttributes and any(key in ['mdt', 'mdn', 'peid', 'pei'] for key in updatedAttributes.keys()):
				self._clearMdlt()

		
		# # Check if mdn was changed and shorten mdlt accordingly, if exists
		# if updatedAttributes:
		# 	# shorten the mdlt if a limit is set in mdn
		# 	if self.mdlt and (newMdn := updatedAttributes.get('mdn') ) is not None:	# Returns None if dct is None or not found in dct
		# 		mdlt = self.mdlt
		# 		if (l := len(mdlt)) > newMdn:
		# 			mdlt = mdlt[l-newMdn:]
		# 			self['mdlt'] = mdlt

		# 	# Check if mdt was changed in an update
		# 	if (newMdt := updatedAttributes.get('mdt')):	# mdt is in the update, either True, False or None!
		# 		if newMdt is None and CSE.timeSeries.isMonitored(self.ri):				# it is in the update, but set to None, meaning remove the mdt from the TS
		# 			CSE.timeSeries.stopMonitoringTimeSeries(self.ri)

		# Always set the mdc to the length of mdlt if present
		if self.mdlt is not None:
			self.setAttribute('mdc', len(self.mdlt))
		else:
			self.setAttribute('mdc', 0)

		# Save changes
		self.dbUpdate(True)


	def _clearMdlt(self, overwrite:Optional[bool] = True) -> None:
		"""	Clear the missingDataList and missingDataCurrentNr attributes.
			Actually, this attribute will create a new mdlt and set mdc to 0 if they have not been created before.

			Args:
				overwrite: Force overwrite.
		"""
		self.setAttribute('mdlt', [], overwrite)
		self.setAttribute('mdc', 0, overwrite)

		# Remove the mdlt if it is empty. It will be created later on demand
		if self.mdlt is not None and len(self.mdlt) == 0:
			self.delAttribute('mdlt')
			L.isDebug and L.logDebug('mdlt empty and is removed')
		

	def timeSeriesInstances(self) -> list[Resource]:
		"""	Get all timeSeriesInstances of a timeSeries and return a sorted (by ct, oldest first) list.

			Returns:
				A sorted list of timeSeriesInstances.
		""" 
		return sorted(CSE.dispatcher.retrieveDirectChildResources(self.ri, ResourceTypes.TSI), key = lambda x: x.ct) # type:ignore[no-any-return]


	def addDgtToMdlt(self, dgtToAdd:float) -> None:
		"""	Add a dataGenerationTime *dgtToAdd* to the mdlt of this resource.
		"""
		self.setAttribute('mdlt', [], False)								# Add mdlt, just in case it hasn't created before
		self.mdlt.append(toISO8601Date(dgtToAdd))							# Add missing dgt to TS.mdlt
		self.setAttribute('mdc', len(self.mdlt), overwrite = True)			# Set the mdc

		if (mdn := self.mdn) is not None:									# mdn may not be set. Then this list grows forever
			if len(self.mdlt) > mdn:										# If mdlt is bigger then mdn allows
				self.setAttribute('mdlt', self.mdlt[1:], overwrite = True)	# Shorten the mdlt
			self.setAttribute('mdc', len(self.mdlt), overwrite = True)		# Set the mdc
		self.dbUpdate(True)													# Update in DB


