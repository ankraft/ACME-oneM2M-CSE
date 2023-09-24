#
#	Resource.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#

""" Base class for all oneM2M resource types.
"""

# The following import allows to use "Resource" inside a method typing definition
from __future__ import annotations
from typing import Any, Tuple, cast, Optional, List, overload

from copy import deepcopy

from ..etc.Types import ResourceTypes, Result, NotificationEventType, CSERequest, JSON
from ..etc.ResponseStatusCodes import ResponseException, BAD_REQUEST, CONTENTS_UNACCEPTABLE, INTERNAL_SERVER_ERROR
from ..etc.Utils import isValidID, uniqueRI, uniqueRN, isUniqueRI, removeNoneValuesFromDict, resourceDiff, normalizeURL, pureResource
from ..helpers.TextTools import findXPath, setXPath
from ..etc.DateUtils import getResourceDate
from ..services.Logging import Logging as L
from ..services import CSE
from ..etc.Constants import Constants

# Future TODO: Check RO/WO etc for attributes (list of attributes per resource?)
# TODO cleanup optimizations
# TODO _remodeID - is anybody using that one??



# Optimize access to names of internal attributes (fewer look-up)
_rtype = Constants.attrRtype
_srn = Constants.attrSrn
_node = Constants.attrNode
_createdInternallyRI = Constants.attrCreatedInternallyRI
_imported = Constants.attrImported
_isInstantiated = Constants.attrIsInstantiated
_originator = Constants.attrOriginator
_modified = Constants.attrModified
_remoteID = Constants.attrRemoteID
_rvi = Constants.attrRvi
_et = Constants.attrExpireTime


class Resource(object):
	""" Base class for all oneM2M resource types,
	
		Attributes:

	"""

	__slots__ = (
		'tpe',
		'readOnly',
		'inheritACP',
		'dict',
		'isImported',
		'_originalDict',
	)

	_excludeFromUpdate = [ 'ri', 'ty', 'pi', 'ct', 'lt', 'st', 'rn', 'mgd' ]
	"""	Resource attributes that are excluded when updating the resource """

	# ATTN: There is a similar definition in FCNT, TSB, and others! Don't Forget to add attributes there as well

	internalAttributes	= [ _rtype, _srn, _node, _createdInternallyRI, _imported, 
							_isInstantiated, _originator, _modified, _remoteID, _rvi, _et]
	"""	List of internal attributes and which do not belong to the oneM2M resource attributes """

	def __init__(self, 
				 ty:ResourceTypes, 
				 dct:JSON, 
				 pi:Optional[str] = None, 
				 tpe:Optional[str] = None,
				 create:Optional[bool] = False,
				 inheritACP:Optional[bool] = False, 
				 readOnly:Optional[bool] = False, 
				 rn:Optional[str] = None) -> None:
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
		if ty not in [ ResourceTypes.FCNT, ResourceTypes.FCI ]: 	
			self.tpe = ty.tpe() if not tpe else tpe

		if dct is not None: 
			self.isImported = dct.get(_imported)	# might be None, or boolean
			self.dict = deepcopy(dct.get(self.tpe))
			if not self.dict:
				self.dict = deepcopy(dct)
			self._originalDict = deepcopy(dct)	# keep for validation in activate() later
		else:
			# no Dict, so the resource is instantiated programmatically
			self.setAttribute(_isInstantiated, True)

		# if self.dict is not None:
		if not self.tpe: 
			self.tpe = self.__rtype__
		if not self.hasAttribute('ri'):
			self.setAttribute('ri', uniqueRI(self.tpe), overwrite = False)
		if pi is not None: # test for None bc pi might be '' (for cse). pi is used subsequently here
			self.setAttribute('pi', pi)

		# override rn if given
		if rn:
			self.setResourceName(rn)

		# Create an RN if there is none (not given, none in the resource)
		if not self.hasAttribute('rn'):	# a bit of optimization bc the function call might cost some time
			self.setResourceName(uniqueRN(self.tpe))

		# Check uniqueness of ri. otherwise generate a new one. Only when creating
		if create:
			while not isUniqueRI(ri := self.ri):
				L.isWarn and L.logWarn(f'RI: {ri} is already assigned. Generating new RI.')
				self['ri'] = uniqueRI(self.tpe)

		# Set some more attributes
		if not (self.hasAttribute('ct') and self.hasAttribute('lt')):
			ts = getResourceDate()
			self.setAttribute('ct', ts, overwrite = False)
			self.setAttribute('lt', ts, overwrite = False)

		# Handle resource type
		if ty is not None:
			self.setAttribute('ty', int(ty))

		#
		## Note: ACPI is handled in activate() and update()
		#

		# Remove empty / null attributes from dict
		# But see also the comment in update() !!!
		self.dict = removeNoneValuesFromDict(self.dict, ['cr'])	# allow the cr attribute to stay in the dictionary. It will be handled with in the RegistrationManager

		self.setAttribute(_rtype, self.tpe)


	# Default encoding implementation. Overwrite in subclasses
	def asDict(self, embedded:Optional[bool] = True, 
					 update:Optional[bool] = False, 
					 noACP:Optional[bool] = False,
					 sort:bool = False) -> JSON:
		"""	Get the JSON resource representation.
		
			Args:
				embedded: Optional indicator whether the resource should be embedded in another resource structure. In this case it is *not* embedded in its own "domain:name" structure.
				update: Optional indicator whether only the updated attributes shall be included in the result.
				noACP: Optional indicator whether the *acpi* attribute shall be included in the result.
			
			Return:
				A `JSON` object with the resource representation.
		"""
		# remove (from a copy) all internal attributes before printing
		dct = { k:deepcopy(v) for k,v in self.dict.items() 				# Copy k:v to the new dictionary, ...
					if k not in self.internalAttributes 				# if k is not in internal attributes (starting with __), AND
					and not (noACP and k == 'acpi')						# if not noACP is True and k is 'acpi', AND
					and not (update and k in self._excludeFromUpdate) 	# if not update is True and k is in _excludeFromUpdate)
				}
		if sort:
			dct = dict(sorted(dct.items())) # sort the dictionary by key
		return { self.tpe : dct } if embedded else dct


	def activate(self, parentResource:Resource, originator:str) -> None:
		"""	This method is called to activate a resource, usually in a CREATE request.

			This is not always the case, e.g. when a resource object is just used temporarly.
			**NO** notification on activation/creation happens in this method!

			This method is implemented in sub-classes as well.
			
			Args:
				parentResource: The resource's parent resource.
				originator: The request's originator.

			Raises:
				`BAD_REQUEST`: In case of an invalid attribute.
		"""
		# TODO check whether 				CR is set in RegistrationManager
		L.isDebug and L.logDebug(f'Activating resource: {self.ri}')

		# validate the attributes but only when the resource is not instantiated.
		# We assume that an instantiated resource is always correct
		# Also don't validate virtual resources
		if not self[_isInstantiated] and not self.isVirtual() :
			CSE.validator.validateAttributes(self._originalDict, 
											 self.tpe, 
											 self.ty, 
											 self._attributes, 
											 isImported = self.isImported, 
											 createdInternally = self.isCreatedInternally(), 
											 isAnnounced = self.isAnnounced())

		# validate the resource logic
		self.validate(originator, parentResource = parentResource)
		self.dbUpdate()
		
		# Various ACPI handling
		# ACPI: Check <ACP> existence and convert <ACP> references to CSE relative unstructured
		if self.acpi is not None and not self.isAnnounced():
			# Test wether an empty array is provided				
			if len(self.acpi) == 0:
				raise BAD_REQUEST('acpi must not be an empty list')
			self.setAttribute('acpi', self._checkAndFixACPIreferences(self.acpi))

		self.setAttribute(_originator, originator, overwrite = False)
		self.setAttribute(_rtype, self.tpe, overwrite = False) 


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
		
		# Remove directChildResources. Don't do checks (e.g. subscriptions) for the sub-resources
		CSE.dispatcher.deleteChildResources(self, originator, doDeleteCheck = False)
		
		# Removal of a deleted resource from group(s) is done 
		# asynchronously in GroupManager, triggered by an event.


	def update(self, dct:Optional[JSON] = None, 
					 originator:Optional[str] = None, 
					 doValidateAttributes:Optional[bool] = True) -> None:
		"""	Update, add or remove resource attributes.

			A subscription check for update is performed.

			This method is implemented in sub-classes as well.

			Note:
				This method updates the resource in the database. It should be called only after all other checks where performed.

			Args:
				dct: An optional JSON dictionary with the attributes to be updated.
				originator: The optional requests originator that let to the update of the resource.
				doValidateAttributes: If *True* optionally call the resource's `validate()` method.

			Raises:
				`CONTENTS_UNACCEPTABLE`: In case of a resource mismatch.
				`BAD_REQUEST`: In case of an invalid attribute.
				`INTERNAL_SERVER_ERROR`: In case the parent resource coudln't be retrieved.
		"""
		dictOrg = deepcopy(self.dict)	# Save for later for notification

		updatedAttributes:dict[str, Any] = None
		if dct:
			CSE.validator.validateResourceUpdate(self, dct, doValidateAttributes)
			# if self.tpe not in dct and self.ty not in [ResourceTypes.FCNTAnnc]:	# Don't check announced versions of announced FCNT
			# 	L.isWarn and L.logWarn("Update type doesn't match target")
			# 	raise CONTENTS_UNACCEPTABLE('resource types mismatch')

			# # validate the attributes
			# if doValidateAttributes:
			# 	CSE.validator.validateAttributes(dct, 
			# 									 self.tpe, 
			# 									 self.ty, 
			# 									 self._attributes, 
			# 									 create = False, 
			# 									 createdInternally = 
			# 									 self.isCreatedInternally(), 
			# 									 isAnnounced = self.isAnnounced())

			if self.ty not in [ResourceTypes.FCNTAnnc]:
				updatedAttributes = dct[self.tpe] # get structure under the resource type specifier
			else:
				updatedAttributes = findXPath(dct, '{*}')

			# Check that acpi, if present, is the only attribute
			if 'acpi' in updatedAttributes and (ua := updatedAttributes['acpi']) is not None:	
				
				# No further checks for access here. This has been done before in the Dispatcher.processUpdateRequest()	
				# Removing acpi by setting it to None is handled in the else:
				# acpi can be None! Therefore the complicated test

				# Test wether an empty array is provided				
				if len(ua) == 0:
					raise BAD_REQUEST('acpi must not be an empty list')

				# Check whether referenced <ACP> exists. If yes, change ID also to CSE relative unstructured
				self.setAttribute('acpi', self._checkAndFixACPIreferences(ua), overwrite = True) # copy new value or add new attributes

			else:

				# Update other  attributes
				for key, value in updatedAttributes.items():
					# Leave out some attributes
					if key in ['ct', 'lt', 'pi', 'ri', 'rn', 'st', 'ty']:
						continue
					# copy new value or add new attributes.
					# Also setting it to Null/None would later remove it
					self.setAttribute(key, value, overwrite = True) 
			

		# Update lt for those resources that have these attributes
		if 'lt' in self.dict:	# Update the lastModifiedTime
			self['lt'] = getResourceDate()

		# Remove empty / null attributes from dict
		# 2020-08-10 : 	TinyDB doesn't overwrite the whole document but makes an attribute-by-attribute 
		#				update. That means that removed attributes are NOT removed. There is now a 
		#				procedure in the Storage component that removes nulled attributes as well.
		#self.dict = {k: v for (k, v) in self.dict.items() if v is not None }

		# Retrieve the parent resource for validation
		if not (parentResource := cast(Resource, self.retrieveParentResource())):
			raise INTERNAL_SERVER_ERROR(L.logErr(f'cannot retrieve parent resource'))

		# Do some extra validations, if necessary
		self.validate(originator, dct = dct, parentResource = parentResource)

		# store last modified attributes
		self[_modified] = resourceDiff(dictOrg, self.dict, updatedAttributes)

		# Check subscriptions
		CSE.notification.checkSubscriptions(self, NotificationEventType.resourceUpdate, modifiedAttributes = self[_modified])
		self.dbUpdate()

		# Check Attribute Trigger
		# TODO CSE.action.checkTrigger, self, modifiedAttributes=self[_modified])

		# Notify parent that a child has been updated
		parentResource.childUpdated(self, updatedAttributes, originator)


	def willBeUpdated(self, dct:Optional[JSON] = None, 
							originator:Optional[str] = None, 
							subCheck:Optional[bool] = True) -> None:
		""" This method is called before a resource will be updated and before calling the `update()` method.
			
			This method is implemented in some sub-classes.

			Args:
				dct: `JSON` dictionary with the attributes that will be updated.
				originator: The request originator.
				subCheck: Optional indicator that a blocking Update shall be performed, if configured.
		"""
		# Perform BlockingUpdate check, and reload resource if necessary
		CSE.notification.checkPerformBlockingUpdate(self, originator, dct, finished = lambda: self.dbReloadDict())


	def updated(self, dct:Optional[JSON] = None, 
					  originator:Optional[str] = None) -> None:
		"""	Signal to a resource that is was successfully updated. 
		
			This handler can be used to perform	additional actions after the resource was updated, stored etc.
			
			This method is implemented in some sub-classes.

			Args:
				dct: Optional JSON dictionary with the updated attributes.
				originator: The optional request originator.
		"""
		...


	def willBeRetrieved(self, originator:str, 
							  request:Optional[CSERequest] = None, 
							  subCheck:Optional[bool] = True) -> None:
		""" This method is called before a resource will be send back in a RETRIEVE response.
			
			This method is implemented in some sub-classes.

			Args:
				originator: The request originator.
				request: The RETRIEVE request.
				subCheck: Optional indicator that a blocking Retrieve shall be performed, if configured.
		"""
		# Check for blockingRetrieve or blockingRetrieveDirectChild
		if subCheck and request:
			CSE.notification.checkPerformBlockingRetrieve(self, request, finished = lambda: self.dbReloadDict())


	def childWillBeAdded(self, childResource:Resource, originator:str) -> None:
		""" Called before a child will be added to a resource.
			
			This method is implemented in some sub-classes.

			Args:
				childResource: Resource that will be added as a child to the resource.
				originator: The request originator.

		"""
		...


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
		...


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


	def validate(self, originator:Optional[str] = None, 
					   dct:Optional[JSON] = None, 
					   parentResource:Optional[Resource] = None) -> None:
		""" Validate a resource. 
		
			Usually called within `activate()` or `update()` methods.

			This method is implemented in some sub-classes.

			Args:
				originator: Optional request originator
				dct: Updated attributes to validate
				parentResource: The parent resource

			Raises
				`BAD_REQUEST`: In case of a validation error.
		"""
		L.isDebug and L.logDebug(f'Validating resource: {self.ri}')
		if not ( isValidID(self.ri) and
				 isValidID(self.pi, allowEmpty = self.ty == ResourceTypes.CSEBase) and # pi is empty for CSEBase
				 isValidID(self.rn)):
			raise BAD_REQUEST(L.logDebug(f'Invalid ID: ri: {self.ri}, pi: {self.pi}, or rn: {self.rn})'))

		# expirationTimestamp handling
		if et := self.et:
			if self.ty == ResourceTypes.CSEBase:
				raise BAD_REQUEST(L.logWarn('expirationTime is not allowed in CSEBase'))
			
			# In the past?
			if len(et) > 0 and et < (etNow := getResourceDate()):
				raise BAD_REQUEST(L.logWarn(f'expirationTime is in the past: {et} < {etNow}'))

			# Check if the et is later than the parent's et
			if parentResource and parentResource.ty != ResourceTypes.CSEBase and et > parentResource.et:
				L.isDebug and L.logDebug(f'et is later than the parent\'s et. Correcting.')
				self.setAttribute('et', parentResource.et)

			# Maximum Expiration time
			if et > (etMax := getResourceDate(CSE.request.maxExpirationDelta)):
				L.isWarn and L.logWarn(f'Correcting expirationDate to maxExpiration: {et} -> {etMax}')
				self.setAttribute('et', etMax)

		else:	# set et to the parents et if not in the resource yet
			if self.ty != ResourceTypes.CSEBase:	# Only when not CSEBase
				if not (et := parentResource.et):
					et = getResourceDate(CSE.request.maxExpirationDelta)
				self.setAttribute('et', et)


	#########################################################################

	def isCreatedInternally(self) -> bool:
		""" Test whether a resource has been created for another resource.

			Return:
				True if this resource has been created for another resource.
		"""
		return self[_createdInternallyRI] is not None


	def setCreatedInternally(self, ri:str) -> None:
		"""	Save the resource ID for which this resource was created for.
		
			This has some impacts on internal handling and checks.

			Args:
				ri: Resource ID of the resource for which this resource has been created for.

		"""
		self[_createdInternallyRI] = ri


	def isAnnounced(self) -> bool:
		""" Test whether a the resource's type is an announced type. 
		
			Returns:
				True if the resource is an announced resource type.
		"""
		return ResourceTypes(self.ty).isAnnounced()

	
	def isVirtual(self) -> bool:
		"""	Test whether the resource is a virtual resource. 

			Return:
				True when the resource is a virtual resource.
		"""
		return ResourceTypes(self.ty).isVirtual()


	#########################################################################
	#
	#	request handler stubs for virtual resources
	#


	def handleRetrieveRequest(self, request:Optional[CSERequest] = None,
									id:Optional[str] = None,
									originator:Optional[str] = None) -> Result:
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


	def setAttribute(self, key:str, 
						   value:Any, 
						   overwrite:Optional[bool] = True) -> None:
		"""	Assign a value to a resource attribute.

			If the attribute doesn't exist then it is created.
		
			Args:
				key: The resource attribute's name. This can be a path (see `setXPath`).
				value: Value to assign to the attribute.
				overwrite: Overwrite the value if already set.
		"""
		setXPath(self.dict, key, value, overwrite)


	def attribute(self, key:str, 
						default:Optional[Any] = None) -> Any:
		"""	Return the value of an attribute.
		
			Args:
				key: Resource attribute name to look for. This can be a path (see `findXPath`).
				default: A default value to return if the attribute is not set.
			Return:
				The attribute's value, the *default* value, or None
		"""
		return findXPath(self.dict, key, default)


	def hasAttribute(self, key:str) -> bool:
		"""	Check whether an attribute exists.

			Args:
				key: Resource attribute name to look for.
			Return:
				Boolean, indicating the existens of an attribute
		"""
		# TODO check sub-elements as well via findXPath
		return key in self.dict


	def delAttribute(self, key:str, 
						   setNone:Optional[bool] = True) -> None:
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
	

	def getFinalResourceAttribute(self, key:str, dct:Optional[JSON]) -> Any:
		"""	Determine and return the final value of an attribute during an update.
		
			Args:
				key: Attribute name.
				dct: The dictionary with updated attributes.
			
			Return:
				The either updated attribute, or old value if the attribute is not updated. The methon returns *None* if the attribute does not exists.
		"""
		value = self.attribute(key)	# old value
		if dct is not None:
			newValue = findXPath(dct, f'{self.tpe}/{key}')
			value = newValue if newValue is not None else value
		return value


	def __setitem__(self, key:str, value:Any) -> None:
		""" Implementation of the *self[key]* operation for assigning to attributes.
		
			It maps to the `setAttribute()` method, and always overwrites existing values.

			Args:
				key: The resource attribute's name. This can be a path (see `setXPath`).
				value: Value to assign to the attribute.
		"""
		self.setAttribute(key, value)


	def __getitem__(self, key:str) -> Any:
		"""	Implementation of the *self[key|* operation for retrieving attributes.

			It maps to the `attribute()` method, but there is no default value.

			Args:
				key: Resource attribute name to look for. This can be a path (see `findXPath`).
			Return:
				The attribute's value, or None
		"""
		return self.attribute(key)


	def __delitem__(self, key:str) -> None:
		"""	Implementation of the *self[key|* operation for deleting attributes.

			It maps to the `delAttribute()` method, with *setNone* implicitly set to the default.

			Args:
				key: Resource attribute name to delete. This can be a path (see `findXPath`).
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
				self[attributeName] = [ normalizeURL(uri) for uri in uris ] 
			else: 							# single uri
				self[attributeName] = normalizeURL(uris)


	def _checkAndFixACPIreferences(self, acpi:list[str]) -> List[str]:
		""" Check whether a referenced `ACP` resoure exists, and if yes, change the ID in the list to CSE relative unstructured format.

			Args:
				acpi: List if resource IDs to `ACP` resources.

			Return:
				If fully successful (ie. all `ACP` resources exist), then a new list with all IDs converted is returned.
		"""

		newACPIList:List[str] = []
		for ri in acpi:
			if not CSE.importer.isImporting:
				try:
					acp = CSE.dispatcher.retrieveResource(ri)
				except ResponseException as e:
					raise BAD_REQUEST(L.logDebug(f'Referenced <ACP> resource not found: {ri} : {e.dbg}'))

					# TODO CHECK TYPE + TEST

				newACPIList.append(acp.ri)
			else:
				newACPIList.append(ri)
		return newACPIList
	

	def _addToInternalAttributes(self, name:str) -> None:
		"""	Add a *name* to the names of internal attributes. 
		
			*name* is only added if	it is not already present.

			Args:
				name: Attribute name to add.
		"""
		if name not in self.internalAttributes:
			self.internalAttributes.append(name)


	def hasAttributeDefined(self, name:str) -> bool:
		"""	Test whether a resource supports the specified attribute.
		
			Args:
				name: Attribute to test.
			Return:
				Boolean with the result of the test.
		"""
		return self._attributes.get(name) is not None


	#########################################################################
	#
	#	Database functions
	#

	def dbDelete(self) -> None:
		""" Delete the resource from the database.
		
			Return:
				Result object indicating success or failure.
		 """
		CSE.storage.deleteResource(self)


	def dbUpdate(self, finalize:bool = False) -> Resource:
		""" Update the resource in the database.

			This also raises a CSE internal *updateResource* event.

			Args:
				finalize: Treat this database write as a final update to the resource. Only then an event is raised.

			Return:
				Result object indicating success or failure.
		"""
		CSE.storage.updateResource(self)
		# L.logWarn(f'{finalize} - {self.ri}')
		if finalize and not self.isVirtual():
				CSE.event.changeResource(self)	 # type: ignore [attr-defined]
		return self


	def dbCreate(self, overwrite:Optional[bool] = False) -> None:
		"""	Add the resource to the database.
		
			Args:
				overwrite: If true an already existing resource with the same resource ID is overwritten.
			Return:
				Result object indicating success or failure.
		"""
		CSE.storage.createResource(self, overwrite)


	def dbReload(self) -> Resource:
		""" Load a **new** copy of the same resource from the database. 
			
			The current resource is NOT changed. 
			
			Note:
				The version of the resource in the database might be different, e.g. when the resource instance has been modified but not updated in the database.

			Return:
				Resource instance.	
			"""
		return CSE.storage.retrieveResource(ri = self.ri)


	def dbReloadDict(self) -> Resource:
		"""	Reload the resource instance from the database.
		
			The current resource's internal attributes are updated with the versions from the database.

			Return:
				Updated Resource instance.	
		 """
		resource = CSE.storage.retrieveResource(ri = self.ri)
		self.dict = resource.dict
		return self

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
		return f'{self.tpe}(ri={self.ri}, srn={self.getSrn()})'


	def __eq__(self, other:object) -> bool:
		"""	Test for equality of the resource to another resource.

			Args:
				other: Other object to test for.
			Return:
				If the *other* object is a Resource instance and has the same resource ID, then *True* is returned, of *False* otherwise.
		"""
		return isinstance(other, Resource) and self.ri == other.ri


	def structuredPath(self) -> Optional[str]:
		""" Determine the structured path of a resource.

			Return:
				Structured path of the resource or None
		"""
		rn:str = self.rn
		if self.ty == ResourceTypes.CSEBase: # if CSE
			return rn

		# retrieve identifier record of the parent
		if not (pi := self.pi):
			# L.logErr('PI is None')
			return rn
		if len(rpi := CSE.storage.identifier(pi)) == 1:
			return cast(str, f'{rpi[0]["srn"]}/{rn}')
		# L.logErr(traceback.format_stack())
		L.logErr(f'Parent {pi} not found in DB')
		return rn # fallback


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
		return CSE.dispatcher.retrieveLocalResource(self.pi)	#type:ignore[no-any-return]


	def retrieveParentResourceRaw(self) -> JSON:
		"""	Retrieve the raw (!) parent resource of this resouce.

			Return:
				Document of the parent resource
		"""
		return CSE.storage.retrieveResourceRaw(self.pi)


	def getOriginator(self) -> str:
		"""	Retrieve a resource's originator.

			Return:
				The resource's originator.
		"""
		return self[_originator]
	

	def setOriginator(self, originator:str) -> None:
		"""	Set a resource's originator.

			This is the originator that created the resource. It is stored internally within the resource.

			Args:
				originator: The originator to assign to a resource.
		"""
		self.setAttribute(_originator, originator)
	
	
	def setResourceName(self, rn:str) -> None:
		"""	Set the resource name. 
		
			Also set/update the internal structured resource name.
			
			Args:
				rn: The new resource name for the resource.
		"""
		self.setAttribute('rn', rn)

		# determine and add the srn, only when this is a local resource, otherwise we don't need this information
		# It is *not* a remote resource when the __remoteID__ is set
		if not self[_remoteID]:
			self.setSrn(self.structuredPath())


	def getSrn(self) -> str:
		"""	Retrieve a resource's full structured resource name.

			Return:
				The resource's full structured resource name.
		"""
		return self[_srn]
	

	def setSrn(self, srn:str) -> None:
		"""	Set a resource's full structured resource name.

			Args:
				srn: The full structured resource name to assign to a resource.
		"""
		self.setAttribute(_srn, srn)


	def getRVI(self) -> str:
		"""	Retrieve a resource's release version indicator.

			Return:
				The resource's *rvi*.
		"""
		return self[_rvi]
	

	def setRVI(self, rvi:str) -> None:
		"""	Assign the release version for a resource.

			This is usually assigned from the *rvi* indicator in the resource's CREATE request.

			Args:
				rvi: Original CREATE request's *rvi*.
		"""
		self.setAttribute(_rvi, rvi)