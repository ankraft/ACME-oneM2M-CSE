#
#	Resource.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#

""" Base class for all oneM2M resource types """

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
	""" Base class for all oneM2M resource types """

	# Contstants for internal attributes
	_rtype 				= '__rtype__'
	_srn				= '__srn__'
	_node				= '__node__'
	_createdInternally	= '__createdInternally__'	# TODO better name. This is actually an RI
	_imported			= '__imported__'
	_announcedTo 		= '__announcedTo__'			# List
	_isInstantiated		= '__isInstantiated__'
	_originator			= '__originator__'			# Or creator
	_modified			= '__modified__'
	_remoteID			= '__remoteID__'			# When this is a resource from another CSE

	_excludeFromUpdate = [ 'ri', 'ty', 'pi', 'ct', 'lt', 'st', 'rn', 'mgd' ]
	"""	Resource attributes that are excluded when updating the resource """

	# ATTN: There is a similar definition in FCNT, TSB, and others! Don't Forget to add attributes there as well
	internalAttributes	= [ _rtype, _srn, _node, _createdInternally, _imported, 
							_isInstantiated, _originator, _announcedTo, _modified, _remoteID ]
	"""	List of internal attributes and which do not belong to the oneM2M resource attributes """

	def __init__(self, 
				 ty:T, 
				 dct:JSON, 
				 pi:str = None, 
				 tpe:str = None,
				 create:bool = False,
				 inheritACP:bool = False, 
				 readOnly:bool = False, 
				 rn:str = None) -> None:
		"""	Initialization of a Resource instance.
		
			Args:
				ty: Mandatory resource type.
				dct: Mandatory resource attributes.
				pi: Optional parent resource identifier.
				tpe: Optional domain and resource name.
				create: Optional indicator whether this resource is just created or an instance of an existing resource.
				inheritACP: Optional indicator whether this resource inherits *acpi* attribute from its parent (if any).
				readOnly: Optional indicator whether this resource is read-only.
				rn: Optional resource name. If none is given and the resource is created, then a random name is assigned to the resource.
		"""

		self.tpe = tpe
		"""	The resource's domain and type name. """
		self.readOnly	= readOnly
		"""	Flag set during creation of a resource instance whether a resource type allows only read-only access to a resource. """
		self.inheritACP	= inheritACP
		"""	Flag set during creation of a resource instance whether a resource type inherits the `resources.ACP.ACP` from its parent resource. """
		self.dict 		= {}
		"""	Dictionary for public and internal resource attributes. """
		self.isImported	= False
		"""	Flag set during creation of a resource instance whether a resource is imported, which disables some validation checks. """
		self._originalDict = {}
		"""	When retrieved from the database: Holds a temporary version of the resource attributes as they were read from the database. """

		# For some types the tpe/root is empty and will be set later in this method
		if ty not in [ T.FCNT, T.FCI ]: 	
			self.tpe = ty.tpe() if not tpe else tpe

		if dct is not None: 
			self.isImported = dct.get(self._imported)	# might be None, or boolean
			self.dict = deepcopy(dct.get(self.tpe))
			if not self.dict:
				self.dict = deepcopy(dct)
			self._originalDict = deepcopy(dct)	# keep for validation in activate() later
		else:
			# no Dict, so the resource is instantiated programmatically
			self.setAttribute(self._isInstantiated, True)

		if self.dict is not None:
			if not self.tpe: # and _rtype in self:
				self.tpe = self.__rtype__
			if not self.hasAttribute('ri'):
				self.setAttribute('ri', Utils.uniqueRI(self.tpe), overwrite = False)
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

			# Set some more attributes
			if not (self.hasAttribute('ct') and self.hasAttribute('lt')):
				ts = DateUtils.getResourceDate()
				self.setAttribute('ct', ts, overwrite = False)
				self.setAttribute('lt', ts, overwrite = False)

			# Handle resource type
			if ty not in [ T.CSEBase ] and not self.hasAttribute('et'):
				self.setAttribute('et', DateUtils.getResourceDate(Configuration.get('cse.expirationDelta')), overwrite = False) 
			if ty is not None:
				self.setAttribute('ty', int(ty))

			#
			## Note: ACPI is handled in activate() and update()
			#

			# Remove empty / null attributes from dict
			# But see also the comment in update() !!!
			self.dict = Utils.removeNoneValuesFromDict(self.dict, ['cr'])	# allow the ct attribute to stay in the dictionary. It will be handled with in the RegistrationManager

			self[self._rtype] = self.tpe
			self.setAttribute(self._announcedTo, [], overwrite = False)


	# Default encoding implementation. Overwrite in subclasses
	def asDict(self, embedded:bool = True, update:bool = False, noACP: bool = False) -> JSON:
		"""	Get the JSON resource representation.
		
			Args:
				embedded: Optional indicator whether the resource should be embedded in another resource structure. In this case it is *not* embedded in its own "domain:name" structure.
				update: Optional indicator whether only the updated attributes shall be included in the result.
				noACP: Optional indicator whether the *acpi* attribute shall be included in the result.
		"""
		# remove (from a copy) all internal attributes before printing
		dct = { k:deepcopy(v) for k,v in self.dict.items() 				# Copy k:v to the new dictionary, ...
					if k not in self.internalAttributes 				# if k is not in internal attributes (starting with __), AND
					and not (noACP and k == 'acpi')						# if not noACP is True and k is 'acpi', AND
					and not (update and k in self._excludeFromUpdate) 	# if not update is True and k is in _excludeFromUpdate)
				}

		return { self.tpe : dct } if embedded else dct


	def activate(self, parentResource:Resource, originator:str) -> Result:
		"""	This method is called to activate a resource, usually in a CREATE request.

			This is not always the case, e.g. when a resource object is just used temporarly.
			**NO** notification on activation/creation happens in this method!

			This method is implemented in sub-classes as well.
			
			Args:
				parentResource: The resource's parent resource.
				originator: The request's originator.
			Return:
				Result object indicating success or failure.
		"""
		# TODO check whether 				CR is set in RegistrationManager
		L.isDebug and L.logDebug(f'Activating resource: {self.ri}')

		# validate the attributes but only when the resource is not instantiated.
		# We assume that an instantiated resource is always correct
		# Also don't validate virtual resources
		if not self[self._isInstantiated] and not self.isVirtual() :
			if not (res := CSE.validator.validateAttributes(self._originalDict, self.tpe, self.ty, self._attributes, isImported = self.isImported, createdInternally = self.isCreatedInternally(), isAnnounced = self.isAnnounced())).status:
				return res

		# validate the resource logic
		if not (res := self.validate(originator, create = True, parentResource = parentResource)).status:
			return res
		self.dbUpdate()
		
		# Various ACPI handling
		# ACPI: Check <ACP> existence and convert <ACP> references to CSE relative unstructured
		if self.acpi is not None and not self.isAnnounced():
			# Test wether an empty array is provided				
			if len(self.acpi) == 0:
				return Result(status = False, rsc = RC.badRequest, dbg = 'acpi must not be an empty list')
			if not (res := self._checkAndFixACPIreferences(self.acpi)).status:
				return res
			self.setAttribute('acpi', res.data)

		self.setAttribute(self._originator, originator, overwrite = False)
		self.setAttribute(self._rtype, self.tpe, overwrite = False) 

		# return Result(status = True, rsc = RC.OK)
		return Result.successResult()


	def deactivate(self, originator:str) -> None:
		"""	Deactivate an active resource.

			This usually happens when creating the resource via a request.
			A subscription check for deletion is performed.

			This method is implemented in sub-classes as well.

			Args:
				originator: The requests originator that let to the deletion of the resource.
		"""
		L.isDebug and L.logDebug(f'Deactivating and removing sub-resources for: {self.ri}')
		# First check notification because the subscription will be removed
		# when the subresources are removed
		CSE.notification.checkSubscriptions(self, NotificationEventType.resourceDelete)
		
		# Remove directChildResources
		CSE.dispatcher.deleteChildResources(self, originator)
		
		# Removal of a deleted resource from group(s) is done 
		# asynchronously in GroupManager, triggered by an event.


	def update(self, dct:JSON = None, originator:str = None) -> Result:
		"""	Update, add or remove resource attributes.

			A subscription check for update is performed.

			This method is implemented in sub-classes as well.

			Args:
				dct: An optional JSON dictionary with the attributes to be updated.
				originator: The optional requests originator that let to the update of the resource.
			Return:
				Result object indicating success or failure.
		"""
		dictOrg = deepcopy(self.dict)	# Save for later for notification

		updatedAttributes = None
		if dct:
			if self.tpe not in dct and self.ty not in [T.FCNTAnnc]:	# Don't check announced versions of announced FCNT
				L.isWarn and L.logWarn("Update type doesn't match target")
				return Result.errorResult(rsc = RC.contentsUnacceptable, dbg = 'resource types mismatch')

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
					return Result.errorResult(dbg = 'acpi must not be an empty list')
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
			

		# Update lt for those resources that have these attributes
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
			return Result.errorResult(rsc = RC.internalServerError, dbg = dbg)
		parent.childUpdated(self, updatedAttributes, originator)

		return Result.successResult()


	def willBeUpdated(self, dct:JSON = None, originator:str = None, subCheck:bool = True) -> Result:
		""" This method is called before a resource will be updated and before calling the `update()` method.
			
			This method is implemented in some sub-classes.

			Args:
				originator: The request originator.
				request: The RETRIEVE request.
				subCheck: Optional indicator that a blocking Update shall be performed, if configured.
			Return:
				Result object indicating success or failure.
		"""
		# Perform BlockingUpdate check, and reload resource if necessary
		if not (res := CSE.notification.checkPerformBlockingUpdate(self, originator, dct, finished = lambda: self.dbReloadDict())).status:
			return res
		return Result.successResult()


	def updated(self, dct:JSON = None, originator:str = None) -> None:
		"""	Signal to a resource that is was successfully updated. 
		
			This handler can be used to perform	additional actions after the resource was updated, stored etc.
			
			This method is implemented in some sub-classes.

			Args:
				dct: Optional JSON dictionary with the updated attributes.
				originator: The optional request originator.
		"""
		pass


	def willBeRetrieved(self, originator:str, request:CSERequest, subCheck:bool = True) -> Result:
		""" This method is called before a resource will be send back in a RETRIEVE response.
			
			This method is implemented in some sub-classes.

			Args:
				originator: The request originator.
				request: The RETRIEVE request.
				subCheck: Optional indicator that a blocking Retrieve shall be performed, if configured.
			Return:
				Result object indicating success or failure.
		"""
		# Check for blockingRetrieve or blockingRetrieveDirectChild
		if subCheck:
			if not (res := CSE.notification.checkPerformBlockingRetrieve(self, originator, request, finished = lambda: self.dbReloadDict())).status:
				return res
		return Result.successResult()


	def childWillBeAdded(self, childResource:Resource, originator:str) -> Result:
		""" Called before a child will be added to a resource.
			
			This method is implemented in some sub-classes.

			Args:
				childResource: Resource that will be added as a child to the resource.
				originator: The request originator.
			Return:
				A Result object with status True, or False (in which case the adding will be rejected), and an error code.
		"""
		return Result.successResult()


	def childAdded(self, childResource:Resource, originator:str) -> None:
		""" Called after a child resource was added to the resource.

			This method is implemented in some sub-classes.

			Args:
				childResource: The child resource that was be added as a child to the resource.
				originator: The request originator.
 		"""
		# Check Subscriptions
		CSE.notification.checkSubscriptions(self, NotificationEventType.createDirectChild, childResource)


	def childUpdated(self, childResource:Resource, updatedAttributes:JSON, originator:str) -> None:
		"""	Called when a child resource was updated.
					
			This method is implemented in some sub-classes.
		
			Args:
				childResource: The child resource that was be updates.
				updatedAttributes: JSON dictionary with the updated attributes.
				originator: The request originator.
		"""
		pass


	def childRemoved(self, childResource:Resource, originator:str) -> None:
		""" Called when a child resource of the resource was removed.

			This method is implemented in some sub-classes.

		Args:
			childResource: The removed child resource.
			originator: The request originator.
		"""
		CSE.notification.checkSubscriptions(self, NotificationEventType.deleteDirectChild, childResource)


	def canHaveChild(self, resource:Resource) -> bool:
		""" Check whether *resource* is a valild child resource for this resource. 

		Args:
			resource: The resource to test.
		Return:
			Boolean indicating whether *resource* is a an allowed resorce for this resource.
		"""
		from .Unknown import Unknown # Unknown imports this class, therefore import only here
		return resource.ty in self._allowedChildResourceTypes or isinstance(resource, Unknown)


	def validate(self, originator:str = None, create:bool = False, dct:JSON = None, parentResource:Resource = None) -> Result:
		""" Validate a resource. 
		
			Usually called within activate() or update() methods.

			This method is implemented in some sub-classes.

			Args:
				originator: Optional request originator
				create: Optional indicator whether this is CREATE request
				dct: Updated attributes to validate
				parentResource: The parent resource
			Return:
				A Result object with status True, or False (in which case the request will be rejected), and an error code.
		"""
		L.isDebug and L.logDebug(f'Validating resource: {self.ri}')
		if not ( Utils.isValidID(self.ri) and
				 Utils.isValidID(self.pi, allowEmpty = self.ty == T.CSEBase) and # pi is empty for CSEBase
				 Utils.isValidID(self.rn)):
			L.logDebug(dbg := f'Invalid ID: ri: {self.ri}, pi: {self.pi}, or rn: {self.rn})')
			return Result.errorResult(rsc = RC.contentsUnacceptable, dbg = dbg)

		# expirationTime handling
		if et := self.et:
			if self.ty == T.CSEBase:
				L.logWarn(dbg := 'expirationTime is not allowed in CSEBase')
				return Result.errorResult(dbg = dbg)
			if len(et) > 0 and et < (etNow := DateUtils.getResourceDate()):
				L.logWarn(dbg := f'expirationTime is in the past: {et} < {etNow}')
				return Result.errorResult(dbg = dbg)
			if et > (etMax := DateUtils.getResourceDate(Configuration.get('cse.maxExpirationDelta'))):
				L.isDebug and L.logDebug(f'Correcting expirationDate to maxExpiration: {et} -> {etMax}')
				self['et'] = etMax
		return Result.successResult()


	#########################################################################

	def createdInternally(self) -> str:
		""" Return the resource.ri for which a resource was created.

			This is done in case a resource must be created as a side-effect when another resource
			is, for example, created.
		
			Return:
				Resource ID of the resource for which this resource has been created, or None.
		"""
		return str(self[self._createdInternally])


	def isCreatedInternally(self) -> bool:
		""" Test whether a resource has been created for another resource.

			Return:
				True if this resource has been created for another resource.
		"""
		return self[self._createdInternally] is not None


	def setCreatedInternally(self, ri:str) -> None:
		"""	Save the resource ID for which this resource was created for.
		
			This has some impacts on internal handling and checks.

			Args:
				ri: Resource ID of the resource for which this resource has been created for.

		"""
		self[self._createdInternally] = ri


	def isAnnounced(self) -> bool:
		""" Test whether a the resource's type is an announced type. 
		
			Returns:
				True if the resource is an announced resource type.
		"""
		return T(self.ty).isAnnounced()

	
	def isVirtual(self) -> bool:
		"""	Test whether the resource is a virtual resource. 

			Return:
				True when the resource is a virtual resource.
		"""
		return T(self.ty).isVirtual()


	#########################################################################
	#
	#	request handler stubs for virtual resources
	#

	def handleRetrieveRequest(self, request:CSERequest = None, id:str = None, originator:str = None) -> Result:
		"""	Process a RETRIEVE request that is directed to a virtual resource.

			This method **must** be implemented by virtual resource class.
			
			Args:
				request: The request to process.
				id: The structured or unstructured resource ID of the target resource.
				originator: The request's originator.
			Return:
				Result object indicating success or failure.
			"""
		raise NotImplementedError('handleRetrieveRequest()')

	
	def handleCreateRequest(self, request:CSERequest, id:str, originator:str) -> Result:
		"""	Process a CREATE request that is directed to a virtual resource.

			This method **must** be implemented by virtual resource class.
			
			Args:
				request: The request to process.
				id: The structured or unstructured resource ID of the target resource.
				originator: The request's originator.
			Return:
				Result object indicating success or failure.
			"""		
		raise NotImplementedError('handleCreateRequest()')


	def handleUpdateRequest(self, request:CSERequest, id:str, originator:str) -> Result:
		"""	Process a UPDATE request that is directed to a virtual resource.

			This method **must** be implemented by virtual resource class.
			
			Args:
				request: The request to process.
				id: The structured or unstructured resource ID of the target resource.
				originator: The request's originator.
			Return:
				Result object indicating success or failure.
			"""	
		raise NotImplementedError('handleUpdateRequest()')


	def handleDeleteRequest(self, request:CSERequest, id:str, originator:str) -> Result:
		"""	Process a DELETE request that is directed to a virtual resource.

			This method **must** be implemented by virtual resource class.
			
			Args:
				request: The request to process.
				id: The structured or unstructured resource ID of the target resource.
				originator: The request's originator.
			Return:
				Result object indicating success or failure.
			"""
		raise NotImplementedError('handleDeleteRequest()')


	#########################################################################
	#
	#	Attribute handling
	#


	def setAttribute(self, key:str, value:Any, overwrite:bool = True) -> None:
		"""	Assign a value to a resource attribute.

			If the attribute doesn't exist then it is created.
		
			Args:
				key: The resource attribute's name. This can be a path (see `etc.Utils.setXPath`).
				value: Value to assign to the attribute.
				overwrite: Overwrite the value if already set.
		"""
		Utils.setXPath(self.dict, key, value, overwrite)


	def attribute(self, key:str, default:Any = None) -> Any:
		"""	Return the value of an attribute.
		
			Args:
				key: Resource attribute name to look for. This can be a path (see `etc.Utils.findXPath`).
				default: A default value to return if the attribute is not set.
			Return:
				The attribute's value, the *default* value, or None
		"""
		return Utils.findXPath(self.dict, key, default)


	def hasAttribute(self, key:str) -> bool:
		"""	Check whether an attribute exists.

			Args:
				key: Resource attribute name to look for.
			Return:
				Boolean, indicating the existens of an attribute
		"""
		# TODO check sub-elements as well via findXPath
		return key in self.dict


	def delAttribute(self, key:str, setNone:bool = True) -> None:
		""" Delete the attribute 'key' from the resource. 
		
			Args:
				key: Name of the resource attribute name to delete.
				setNone:  By default (*True*) the attribute is not deleted but set to *None* and later removed 
						  when storing the resource in the DB. If *setNone' is *False*, then the attribute is immediately
						  deleted from the resource instance's internal dictionary.
		"""
		if self.hasAttribute(key):
			if setNone:
				self.dict[key] = None
			else:
				del self.dict[key]


	def __setitem__(self, key:str, value:Any) -> None:
		""" Implementation of the *self[key]* operation for assigning to attributes.
		
			It maps to the `setAttribute()` method, and always overwrites existing values.

			Args:
				key: The resource attribute's name. This can be a path (see `etc.Utils.setXPath`).
				value: Value to assign to the attribute.
		"""
		self.setAttribute(key, value)


	def __getitem__(self, key:str) -> Any:
		"""	Implementation of the *self[key|* operation for retrieving attributes.

			It maps to the `attribute()` method, but there is no default value.

			Args:
				key: Resource attribute name to look for. This can be a path (see `etc.Utils.findXPath`).
			Return:
				The attribute's value, or None
		"""
		return self.attribute(key)


	def __delitem__(self, key:str) -> None:
		"""	Implementation of the *self[key|* operation for deleting attributes.

			It maps to the `delAttribute()` method, with *setNone* implicitly set to the default.

			Args:
				key: Resource attribute name to delete. This can be a path (see `etc.Utils.findXPath`).
		"""
		self.delAttribute(key)


	def __contains__(self, key: str) -> bool:
		""" Implementation of the membership test operator.

			It maps to the `hasAttribute()` method.

			Args:
				key: Resource attribute name to test for.
			Return:
				Boolean, indicating the existens of an attribute
		"""
		return self.hasAttribute(key)


	def __getattr__(self, key: str) -> Any:
		""" Map the normal object attribute access to the internal resource attribute dictionary.

			It maps to the `attribute()` method, but there is no default value.

			Args:
				key: Resource attribute name to get.
			Return:
				The attribute's value, or None
		"""
		return self.attribute(key)


	#########################################################################

	#
	#	Attribute specific helpers
	#

	def _normalizeURIAttribute(self, attributeName:str) -> None:
		""" Normalize the URLs in the given attribute.
		
			Various changes are made to the URI in case they are not fully compliant.
			This could be, for example, *poa*, *nu* and other attributes that usually hold a URI.

			If the target attribute is a list of URI then all the URIs in the list are normalized.
			
			Args:
				attributeName: Name of the attribute to normalize.
		"""
		if uris := self[attributeName]:
			if isinstance(uris, list):	# list of uris
				self[attributeName] = [ Utils.normalizeURL(uri) for uri in uris ] 
			else: 							# single uri
				self[attributeName] = Utils.normalizeURL(uris)


	def _checkAndFixACPIreferences(self, acpi:list[str]) -> Result:
		""" Check whether a referenced `ACP` resoure exists, and if yes, change the ID in the list to CSE relative unstructured format.

			Args:
				acpi: List if resource IDs to `ACP` resources.
			Return:
				Result instance. If fully successful (ie. all `ACP` resources exist), then a new list with all IDs converted is returned in *Result.data*.
		"""
		newACPIList =[]
		for ri in acpi:
			if not CSE.importer.isImporting:

				if not (acp := CSE.dispatcher.retrieveResource(ri).resource):
					L.logDebug(dbg := f'Referenced <ACP> resource not found: {ri}')
					return Result.errorResult(dbg = dbg)

					# TODO CHECK TYPE + TEST

				newACPIList.append(acp.ri)
			else:
				newACPIList.append(ri)
		return Result(status = True, data = newACPIList)


	#########################################################################
	#
	#	Database functions
	#

	def dbDelete(self) -> Result:
		""" Delete the resource from the database.
		
			Return:
				Result object indicating success or failure.
		 """
		return CSE.storage.deleteResource(self)


	def dbUpdate(self) -> Result:
		""" Update the resource in the database. 

			Return:
				Result object indicating success or failure.
		"""
		return CSE.storage.updateResource(self)


	def dbCreate(self, overwrite:bool = False) -> Result:
		"""	Add the resource to the database.
		
			Args:
				overwrite: If true an already existing resource with the same resource ID is overwritten.
			Return:
				Result object indicating success or failure.
		"""
		return CSE.storage.createResource(self, overwrite)


	def dbReload(self) -> Result:
		""" Load a new copy of the same resource from the database. 
			
			The current resource is NOT changed. 
			
			Note:
				The version of the resource in the database might be different, e.g. when the resource instance has been modified but not updated in the database.
			Return:
				Result object indicating success or failure. The resource is returned in the *Result.resource* attribute.		
			"""
		return CSE.storage.retrieveResource(ri = self.ri)


	def dbReloadDict(self) -> Result:
		"""	Reload the resource instance from the database.
		
			The current resource's internal attributes are updated with the versions from the database.

			Return:
				Result object indicating success or failure. The resource is returned as well in the *Result.resource* attribute.		
		 """
		if (res := CSE.storage.retrieveResource(ri = self.ri)).status:
			self.dict = res.resource.dict
		return res

	#########################################################################
	#
	#	Misc utilities
	#

	def __str__(self) -> str:
		""" String representation of the resource's attributes.

			Return:
				String with the resource formatted as a JSON structure
		"""
		return str(self.asDict())


	def __repr__(self) -> str:
		""" Object representation as string.

			Return:
				String that identifies the resource.
		"""
		return f'{self.tpe}(ri={self.ri}, srn={self[self._srn]})'


	def __eq__(self, other:object) -> bool:
		"""	Test for equality of the resource to another resource.

			Args:
				other: Other object to test for.
			Return:
				If the *other* object is a Resource instance and has the same resource ID, then *True* is returned, of *False* otherwise.
		"""
		return isinstance(other, Resource) and self.ri == other.ri


	def isModifiedAfter(self, otherResource:Resource) -> bool:
		"""	Test whether this resource has been modified after another resource.

			Args:
				otherResource: Another resource used for the test.
			Return:
				True if this resource has been modified after *otherResource*.
		"""
		return str(self.lt) > str(otherResource.lt)


	def retrieveParentResource(self) -> Resource:
		"""	Retrieve the parent resource of this resouce.

			Return:
				The parent Resource of the resource.
		"""
		return CSE.dispatcher.retrieveLocalResource(self.pi).resource	#type:ignore[no-any-return]


	def retrieveParentResourceRaw(self) -> JSON:
		"""	Retrieve the raw (!) parent resource of this resouce.

			Return:
				Document of the parent resource
		"""
		return CSE.storage.retrieveResource(self.pi, raw = True).resource



	def getOriginator(self) -> str:
		"""	Retrieve a resource's originator.

			Return:
				The resource's originator.
		"""
		return self[self._originator]
	

	def setOriginator(self, originator:str) -> None:
		"""	Set a resource's originator.

			This is the originator that created the resource. It is stored internally within the resource.

			Args:
				originator: The originator to assign to a resource.
		"""
		self.setAttribute(self._originator, originator, overwrite = True)
	

	def getAnnouncedTo(self) -> list[Tuple[str, str]]:
		"""	Return the internal announcedTo list of a resource.

			Return:
				The internal list of announcedTo tupples (csi, remote resource ID) for this resource.
		"""
		return self[self._announcedTo]

	
	def setResourceName(self, rn:str) -> None:
		"""	Set the resource name. 
		
			Also set/update the internal structured resource name.
			
			Args:
				rn: The new resource name for the resource.
		"""
		self.setAttribute('rn', rn)

		# determine and add the srn, only when this is a local resource, otherwise we don't need this information
		# It is *not* a remote resource when the __remoteID__ is set
		if not self[self._remoteID]:
			self[self._srn] = Utils.structuredPath(self)
