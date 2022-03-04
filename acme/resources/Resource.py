#
#	Resource.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Base class for all resources
#

# The following import allows to use "Resource" inside a method typing definition
from __future__ import annotations
from typing import Any, List, Tuple, cast
from copy import deepcopy

from ..etc.Constants import Constants as C
from ..etc.Types import ResourceTypes as T, Result, NotificationEventType, ResponseStatusCode as RC, CSERequest, JSON
from ..etc import Utils as Utils
from ..etc import DateUtils as DateUtils
from ..services.Logging import Logging as L
from ..services.Configuration import Configuration
from ..services import CSE as CSE
from .Resource import *

# Future TODO: Check RO/WO etc for attributes (list of attributes per resource?)
# TODO cleanup optimizations
# TODO _remodeID - is anybody using that one??




class Resource(object):
	_rtype 				= '__rtype__'
	_srn				= '__srn__'
	_node				= '__node__'
	_createdInternally	= '__createdInternally__'	# TODO better name. This is actually an RI
	_imported			= '__imported__'
	_isVirtual 			= '__isVirtual__'
	_announcedTo 		= '__announcedTo__'			# List
	_isInstantiated		= '__isInstantiated__'
	_isAnnounced 		= '__isAnnounced__'	
	_originator			= '__originator__'			# Or creator
	_modified			= '__modified__'
	_remoteID			= '__remoteID__'			# When this is a resource from another CSE

	# ATTN: There is a similar definition in FCNT, TSB! Don't Forget to add attributes there as well
	internalAttributes	= [ _rtype, _srn, _node, _createdInternally, _imported, _isVirtual, _isInstantiated, _originator, _announcedTo, _modified, _isAnnounced, _remoteID ]

	def __init__(self, ty:T, dct:JSON=None, pi:str=None, tpe:str=None, create:bool=False, inheritACP:bool=False, 
				 readOnly:bool=False, rn:str=None, isVirtual:bool=False, isAnnounced:bool=False) -> None:
		self.tpe = tpe
		if ty not in [ T.FCNT, T.FCI ]: 	# For some types the tpe/root is empty and will be set later in this method
			self.tpe = ty.tpe() if not tpe else tpe
	
		self.readOnly	= readOnly
		self.inheritACP	= inheritACP
		self.dict 		= {}

		if dct: 
			self.isImported = dct.get(self._imported)	# might be None, or boolean
			self.dict = deepcopy(dct.get(self.tpe))
			if not self.dict:
				self.dict = deepcopy(dct)
			# if self.tpe in dct:
			# 	self.dict = deepcopy(dct[self.tpe])
			# else:
			# 	self.dict = deepcopy(dct)
			self._originalDict = deepcopy(dct)	# keep for validation in activate() later
		else:
			# no Dict, so the resource is instantiated programmatically
			self.setAttribute(self._isInstantiated, True)


		if self.dict:
			if not self.tpe: # and _rtype in self:
				self.tpe = self.__rtype__
			if not self.hasAttribute('ri'):
				self.setAttribute('ri', Utils.uniqueRI(self.tpe), overwrite=False)
			if pi is not None: # test for None bc pi might be '' (for cse). pi is used subsequently here
				self.setAttribute('pi', pi)

			# override rn if given
			if rn:
				self.setResourceName(rn)

			# Create an RN if there is none (not given, none in the resource)
			if not self.hasAttribute('rn'):	# a bit of optimization bc the function call might cost some time
				self.setResourceName(Utils.uniqueRN(self.tpe))

			# Check uniqueness of ri. otherwise generate a new one. Only when creating
			if create:
				while not Utils.isUniqueRI(ri := self.ri):
					L.isWarn and L.logWarn(f'RI: {ri} is already assigned. Generating new RI.')
					self['ri'] = Utils.uniqueRI(self.tpe)

			# Indicate whether this is a virtual resource
			if isVirtual:
				self.setAttribute(self._isVirtual, isVirtual)
			
			# Indicate whether this is an announced resource
			self.setAttribute(self._isAnnounced, isAnnounced)
			
			# Set some more attributes
			if not (self.hasAttribute('ct') and self.hasAttribute('lt')):
				ts = DateUtils.getResourceDate()
				self.setAttribute('ct', ts, overwrite=False)
				self.setAttribute('lt', ts, overwrite=False)

			if self.ty not in [ T.CSEBase ] and not self.hasAttribute('et'):
				self.setAttribute('et', DateUtils.getResourceDate(Configuration.get('cse.expirationDelta')), overwrite=False) 
			if ty is not None:	# ty is an int
				if T.isStateTagResourceTypes(ty):		# Only for allowed resources
					self.setAttribute('st', 0, overwrite=False)
				self.setAttribute('ty', int(ty))

			#
			## Note: ACPI is handled in activate() and update()
			#

			# Remove empty / null attributes from dict
			# But see also the comment in update() !!!
			self.dict = Utils.removeNoneValuesFromDict(self.dict, ['cr'])	# allow the ct attribute to stay in the dictionary. It will be handled with in the RegistrationManager

			self[self._rtype] = self.tpe
			self.setAttribute(self._announcedTo, [], overwrite=False)



	# Default encoding implementation. Overwrite in subclasses
	_excludeFromUpdate = [ 'ri', 'ty', 'pi', 'ct', 'lt', 'st', 'rn', 'mgd' ]
	def asDict(self, embedded:bool=True, update:bool=False, noACP: bool=False) -> JSON:
		# remove (from a copy) all internal attributes before printing
		# dct = deepcopy(self.dict)
		# for k in self.internalAttributes:
		# 	if k in dct: 
		# 		del dct[k]

		# if noACP:
		# 	if 'acpi' in dct:
		# 		del dct['acpi']

		# if update:
		# 	for k in [ 'ri', 'ty', 'pi', 'ct', 'lt', 'st', 'rn', 'mgd']:
		# 		dct.pop(k, None) # instead of using "del dct[k]" this doesn't throw an exception if k doesn't exist

		dct = { k:deepcopy(v) for k,v in self.dict.items() 				# Copy k:v to the new dictionary, ...
					if k not in self.internalAttributes 				# if k is not in internal attributes (starting with __), AND
					and not (noACP and k == 'acpi')						# if not noACP is True and k is 'acpi', AND
					and not (update and k in self._excludeFromUpdate) 	# if not update is True and k is in _excludeFromDict)
				}

		return { self.tpe : dct } if embedded else dct



	def activate(self, parentResource:Resource, originator:str) -> Result:
		"""	This method is called to to activate a resource. 
			This is not always the case, e.g. when a resource object is just used temporarly.
			NO notification on activation/creation!
			Implemented in sub-classes as well.
			Note: CR is set in RegistrationManager	(TODO: Check this)
		"""
		L.isDebug and L.logDebug(f'Activating resource: {self.ri}')

		# validate the attributes but only when the resource is not instantiated.
		# We assume that an instantiated resource is always correct
		# Also don't validate virtual resources
		# if (self[self._isInstantiated] is None or not self[self._isInstantiated]) and not self[self._isVirtual] :
		if not self[self._isInstantiated] and not self[self._isVirtual] :
			if not (res := CSE.validator.validateAttributes(self._originalDict, self.tpe, self.ty, self._attributes, isImported = self.isImported, createdInternally = self.isCreatedInternally(), isAnnounced = self.isAnnounced())).status:
				return res

		# validate the resource logic
		if not (res := self.validate(originator, create = True, parentResource = parentResource)).status:
			return res
		self.dbUpdate()
		# increment parent resource's state tag
		if parentResource and parentResource.st is not None:	# st is an int
			parentResource = parentResource.dbReload().resource	# Read the resource again in case it was updated in the DB
			parentResource['st'] = parentResource.st + 1
			if not (res := parentResource.dbUpdate()).resource:
				return Result(status = False, rsc = res.rsc, dbg = res.dbg)
		
		#
		#	Various ACPI handling
		# ACPI: Check <ACP> existence and convert <ACP> references to CSE relative unstructured
		if self.acpi is not None and not T(self.ty).isAnnounced():
			# Test wether an empty array is provided				
			if len(self.acpi) == 0:
				return Result(status = False, rsc = RC.badRequest, dbg = 'acpi must not be an empty list')
			if not (res := self._checkAndFixACPIreferences(self.acpi)).status:
				return res
			self.setAttribute('acpi', res.data)


		self.setAttribute(self._originator, originator, overwrite = False)
		self.setAttribute(self._rtype, self.tpe, overwrite = False) 

		return Result(status = True, rsc = RC.OK)


	# Deactivate an active resource.
	# Send notification on deletion
	def deactivate(self, originator:str) -> None:
		L.isDebug and L.logDebug(f'Deactivating and removing sub-resources for: {self.ri}')
		# First check notification because the subscription will be removed
		# when the subresources are removed
		CSE.notification.checkSubscriptions(self, NotificationEventType.resourceDelete)
		
		# Remove directChildResources
		CSE.dispatcher.deleteChildResources(self, originator)
		
		# Removal of a deleted resource from group(s) is done 
		# asynchronously in GroupManager, triggered by an event.


	# Update this resource with (new) fields.
	# Call validate() afterward to react on changes.
	def update(self, dct:JSON = None, originator:str = None) -> Result:
		dictOrg = deepcopy(self.dict)	# Save for later for notification

		updatedAttributes = None
		if dct:
			if self.tpe not in dct and self.ty not in [T.FCNTAnnc]:	# Don't check announced versions of announced FCNT
				L.isWarn and L.logWarn("Update type doesn't match target")
				return Result(status = False, rsc = RC.contentsUnacceptable, dbg = 'resource types mismatch')

			# validate the attributes
			if not (res := CSE.validator.validateAttributes(dct, self.tpe, self.ty, self._attributes, create = False, createdInternally = self.isCreatedInternally(), isAnnounced = self.isAnnounced())).status:
				return res

			if self.ty not in [T.FCNTAnnc]:
				updatedAttributes = dct[self.tpe] # get structure under the resource type specifier
			else:
				updatedAttributes = Utils.findXPath(dct, '{0}')

			# Check that acpi, if present, is the only attribute
			if 'acpi' in updatedAttributes and updatedAttributes['acpi'] is not None:	# No further checks for access here. This has been done before in the Dispatcher.processUpdateRequest()	
																						# Removing acpi by setting it to None is handled in the else:
																						# acpi can be None! Therefore the complicated test
				# Test wether an empty array is provided				
				if len(ua := updatedAttributes['acpi']) == 0:
					return Result(status = False, rsc = RC.badRequest, dbg = 'acpi must not be an empty list')
				# Check whether referenced <ACP> exists. If yes, change ID also to CSE relative unstructured
				if not (res := self._checkAndFixACPIreferences(ua)).status:
					return res
				
				self.setAttribute('acpi', res.data, overwrite = True) # copy new value or add new attributes

			else:

				# Update other  attributes
				for key in updatedAttributes:
					# Leave out some attributes
					if key in ['ct', 'lt', 'pi', 'ri', 'rn', 'st', 'ty']:
						continue
					value = updatedAttributes[key]

					# Special handling for et when deleted/set to Null: set a new et
					if key == 'et' and not value:
						self['et'] = DateUtils.getResourceDate(Configuration.get('cse.expirationDelta'))
						continue
					self.setAttribute(key, value, overwrite = True) # copy new value or add new attributes
			

		# - state and lt
		if 'st' in self.dict:	# Update the state
			self['st'] += 1
		if 'lt' in self.dict:	# Update the lastModifiedTime
			self['lt'] = DateUtils.getResourceDate()

		# Remove empty / null attributes from dict
		# 2020-08-10 : 	TinyDB doesn't overwrite the whole document but makes an attribute-by-attribute 
		#				update. That means that removed attributes are NOT removed. There is now a 
		#				procedure in the Storage component that removes nulled attributes as well.
		#self.dict = {k: v for (k, v) in self.dict.items() if v is not None }

		# Do some extra validations, if necessary
		if not (res := self.validate(originator, dct = dct)).status:
			return res

		# store last modified attributes
		self[self._modified] = Utils.resourceDiff(dictOrg, self.dict, updatedAttributes)

		# Check subscriptions
		CSE.notification.checkSubscriptions(self, NotificationEventType.resourceUpdate, modifiedAttributes = self[self._modified])
		self.dbUpdate()

		# Check Attribute Trigger
		# TODO CSE.action.checkTrigger, self, modifiedAttributes=self[self._modified])

		# Notify parent that a child has been updated
		if not (parent := cast(Resource, self.retrieveParentResource())):
			L.logErr(dbg := f'cannot retrieve parent resource')
			return Result(status = False, rsc = RC.internalServerError, dbg = dbg)
		parent.childUpdated(self, updatedAttributes, originator)

		return Result(status = True)


	def updated(self, dct:JSON = None, originator:str = None) -> None:
		"""	Signal to a resource that is was successfully updated. This handler can be used to perform
			additional actions after the resource was updated, stored etc.
			
			Args:
				dct: JSON dictionary with the updated attributes.
				originator: the request originator.
		"""
		pass


	def willBeRetrieved(self, originator:str, request:CSERequest, subCheck:bool = True) -> Result:
		""" Called before a resource will be send back in a response.
			
			Args:
				originator: the request originator.
			Return:
				A Result object.
		"""
		# Check for blockingRetrieve or blockingRetrieveDirectChild
		if subCheck:
			if not (res := CSE.notification.checkPerformBlockingRetrieve(self, originator, request, finished = lambda: self.dbReloadDict())).status:
				return res
		return Result(status = True)


	def childWillBeAdded(self, childResource:Resource, originator:str) -> Result:
		""" Called before a child will be added to a resource.
			
			Args:
				childResource: Resource that will be added as a child to the resource.
				originator: the request originator.
			Return:
				A Result object with status True, or Fale case the adding must be rejected, and an error code.
		"""
		return Result(status = True)


	def childAdded(self, childResource:Resource, originator:str) -> None:
		""" Called after a child resource was added to the resource.
					
			Args:
				childResource: Resource that was be added as a child to the resource.
				originator: the request originator.
 		"""
		# Check Subscriptions
		CSE.notification.checkSubscriptions(self, NotificationEventType.createDirectChild, childResource)


	def childUpdated(self, childResource:Resource, updatedAttributes:JSON, originator:str) -> None:
		"""	Called when a child resource was updated.
							
			Args:
				childResource: Resource that was be added as a child to the resource.
				updatedAttributes: JSON dictionary with the updated attributes.
				originator: the request originator.
		"""
		pass


	def childRemoved(self, childResource:Resource, originator:str) -> None:
		""" Call when child resource was removed from the resource. 
		"""
		CSE.notification.checkSubscriptions(self, NotificationEventType.deleteDirectChild, childResource)


	def canHaveChild(self, resource:Resource) -> bool:
		""" Check whether a fresource may have `resource` as a child resources. 
		"""
		from .Unknown import Unknown # Unknown imports this class, therefore import only here
		return resource.ty in self._allowedChildResourceTypes or isinstance(resource, Unknown)


	def validate(self, originator:str = None, create:bool = False, dct:JSON = None, parentResource:Resource = None) -> Result:
		""" Validate a resource. Usually called within activate() or update() methods.

			Args:
				originator: Request originator
				create: Indicator whether this is CREATE request
				dct: Attributes to validate
				parentResource: The parent resource
		"""
		L.isDebug and L.logDebug(f'Validating resource: {self.ri}')
		if not ( Utils.isValidID(self.ri) and
				 Utils.isValidID(self.pi, allowEmpty = self.ty == T.CSEBase) and # pi is empty for CSEBase
				 Utils.isValidID(self.rn)):
			L.logDebug(dbg := f'Invalid ID: ri: {self.ri}, pi: {self.pi}, or rn: {self.rn})')
			return Result(status = False, rsc = RC.contentsUnacceptable, dbg = dbg)

		# expirationTime handling
		if et := self.et:
			if self.ty == T.CSEBase:
				L.logWarn(dbg := 'expirationTime is not allowed in CSEBase')
				return Result(status = False, rsc = RC.badRequest, dbg = dbg)
			if len(et) > 0 and et < (etNow := DateUtils.getResourceDate()):
				L.logWarn(dbg := f'expirationTime is in the past: {et} < {etNow}')
				return Result(status = False, rsc = RC.badRequest, dbg = dbg)
			if et > (etMax := DateUtils.getResourceDate(Configuration.get('cse.maxExpirationDelta'))):
				L.isDebug and L.logDebug(f'Correcting expirationDate to maxExpiration: {et} -> {etMax}')
				self['et'] = etMax
		return Result(status=True)


	def createAnnouncedDict(self) -> Tuple[JSON, int, str]:
		"""	Create an announceable resource. This method is implemented by the
			resource implementations that support announceable versions.
		"""
		return None, RC.badRequest, 'wrong resource type or announcement not supported'

	#########################################################################

	def createdInternally(self) -> str:
		""" Return the resource.ri for which this ACP was created, or None. """
		return str(self[self._createdInternally])


	def isCreatedInternally(self) -> bool:
		""" Return the resource.ri for which this resource was created, or None. """
		return self[self._createdInternally] is not None


	def setCreatedInternally(self, value:str) -> None:
		"""	Save the RI for which this resource was created for. This has some
			impacts on internal handling and checks.
		"""
		self[self._createdInternally] = value


	def isAnnounced(self) -> bool:
		""" Return whether a resource is an announced resource. """
		return cast(bool, self[self._isAnnounced])

	
	def isVirtual(self) -> bool:
		"""	Test whether the resource is a virtual resource. 

			Return:
				Returns `False` when the resource is not a virtual resource.
		"""
		return cast(bool, self[self._isVirtual]) == True	# might be none

	#########################################################################
	#
	#	request handler stubs for virtual resources
	#

	def handleRetrieveRequest(self, request:CSERequest = None, id:str = None, originator:str = None) -> Result:
		""" MUST be implemented by virtual class."""
		raise NotImplementedError('handleRetrieveRequest()')

	
	def handleCreateRequest(self, request:CSERequest, id:str, originator:str) -> Result:
		""" MUST be implemented by virtual class."""
		raise NotImplementedError('handleCreateRequest()')


	def handleUpdateRequest(self, request:CSERequest, id:str, originator:str) -> Result:
		""" MUST be implemented by virtual class."""
		raise NotImplementedError('handleUpdateRequest()')


	def handleDeleteRequest(self, request:CSERequest, id:str, originator:str) -> Result:
		""" MUST be implemented by virtual class."""
		raise NotImplementedError('handleDeleteRequest()')



	#########################################################################

	#
	#	Attribute handling
	#


	def setAttribute(self, key:str, value:Any, overwrite:bool = True) -> None:
		"""	Assign a value to a resource attribute.
		
			Args:
				key: Name of the resource attribute
				value: Value to assign
				overwrite: Overwrite if present
		"""
		Utils.setXPath(self.dict, key, value, overwrite)


	def attribute(self, key:str, default:Any = None) -> Any:
		"""	Return the value of an attribute.
		
			Args:
				key: Key to look for. This can be a path (see `findXPath()`)
				default: A default to return if the attribute is not set
			Return:
				The attribute's value, the `default`, or None
				"""
		return Utils.findXPath(self.dict, key, default)


	def hasAttribute(self, key:str) -> bool:
		"""	Check whether an attribute exists.
		
			Todo:
				Check sub-elements as well via findXPath
			Args:
				key: attribute to look for
			Return:
				Boolean
		"""
		# TODO check sub-elements as well via findXPath
		return key in self.dict


	def delAttribute(self, key: str, setNone: bool = True) -> None:
		""" Delete the attribute 'key' from the resource. By default the attribute
			is not deleted but set to 'None' and are removed correctly in the 
			DB later. If 'setNone' is False, then the attribute 'key' is 
			really deleted from the resource.
		"""
		if self.hasAttribute(key):
			if setNone:
				self.dict[key] = None
			else:
				del self.dict[key]


	def __setitem__(self, key: str, value: Any) -> None:
		self.setAttribute(key, value)


	def __getitem__(self, key: str) -> Any:
		return self.attribute(key)


	def __delitem__(self, key: str) -> None:
		self.delAttribute(key)


	def __contains__(self, key: str) -> bool:
		return self.hasAttribute(key)


	def __getattr__(self, key: str) -> Any:
		return self.attribute(key)


	#########################################################################

	#
	#	Attribute specific helpers
	#

	def _normalizeURIAttribute(self, attributeName:str) -> None:
		""" Normalize the URLs in the poa, nu etc. """
		if uris := self[attributeName]:
			if isinstance(uris, list):	# list of uris
				self[attributeName] = [ Utils.normalizeURL(uri) for uri in uris ] 
			else: 							# single uri
				self[attributeName] = Utils.normalizeURL(uris)


	def _checkAndFixACPIreferences(self, acpi:list[str]) -> Result:
		""" Check whether referenced <ACP> exists. If yes, change ID also to CSE relative unstructured.
		"""
		newACPIList =[]
		for ri in acpi:
			if not CSE.importer.isImporting:

				if not (acp := CSE.dispatcher.retrieveResource(ri).resource):
					L.logDebug(dbg := f'Referenced <ACP> resource not found: {ri}')
					return Result(status = False, rsc = RC.badRequest, dbg = dbg)



					# TODO CHECK TYPE + TEST




				newACPIList.append(acp.ri)
			else:
				newACPIList.append(ri)
		return Result(status=True, data=newACPIList)



	#########################################################################

	#
	#	Database functions
	#

	def dbDelete(self) -> Result:
		""" Delete the Resource from the database. """
		return CSE.storage.deleteResource(self)


	def dbUpdate(self) -> Result:
		""" Update the Resource in the database. """
		return CSE.storage.updateResource(self)


	def dbCreate(self, overwrite: bool = False) -> Result:
		return CSE.storage.createResource(self, overwrite)


	def dbReload(self) -> Result:
		"""  Load a new copy from the database. The current resource is NOT changed. """
		return CSE.storage.retrieveResource(ri = self.ri)


	def dbReloadDict(self) -> Result:
		"""  Load a new copy from the database. The current resource's internal dict is updated with the load dict. """
		if (res := CSE.storage.retrieveResource(ri = self.ri)).status:
			self.dict = res.resource.dict
		return res


	#########################################################################

	#
	#	Misc utilities
	#

	def __str__(self) -> str:
		""" String representation.
		"""
		return str(self.asDict())


	def __repr__(self) -> str:
		""" Object representation as string.
		"""
		return f'{self.tpe}(ri={self.ri}, srn={self[self._srn]})'


	def __eq__(self, other: object) -> bool:
		"""	Test for equality.
		"""
		return isinstance(other, Resource) and self.ri == other.ri


	def isModifiedSince(self, otherResource: Resource) -> bool:
		"""	Test whether this resource has been modified after another resource.
		"""
		return str(self.lt) > str(otherResource.lt)


	def retrieveParentResource(self) -> Resource:
		"""	Retrieve the parent resource of this resouce.

			Return:
				Parent Resource of the resource
		"""
		return CSE.dispatcher.retrieveLocalResource(self.pi).resource	#type:ignore[no-any-return]


	def retrieveParentResourceRaw(self) -> JSON:
		"""	Retrieve the raw (!) parent resource of this resouce.

			Return:
				Document of the parent resource
		"""
		return CSE.storage.retrieveResource(self.pi, raw = True).resource



	def getOriginator(self) -> str:
		"""	This is a conveniance method to return the creating originator 
			of this resource. This method doesn't seem to add much functionality,
			but the author still struggled in the past to do it right many times.
		"""
		return self[self._originator]
	

	def setOriginator(self, originator:str) -> None:
		"""	Set a resource's originator.
		"""
		self.setAttribute(self._originator, originator, overwrite=True)
	

	def getAnnouncedTo(self) -> list[Tuple[str, str]]:
		"""	This is a conveniance method to return the internal announcedTo
			list of this resource. This method doesn't seem to add much functionality,
			but the author still struggled in the past to do it right many times.
		"""
		return self[self._announcedTo]

	
	def setResourceName(self, rn:str) -> None:
		self.setAttribute('rn', rn)

		# determine and add the srn, only when this is a local resource, otherwise we don't need this information
		# It is *not* a remote resource when the __remoteID__ is set
		if not self[self._remoteID]:
			self[self._srn] = Utils.structuredPath(self)
		# L.logWarn(self[self._srn])
		


