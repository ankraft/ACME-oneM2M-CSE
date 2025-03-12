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
from typing import Any, cast, Optional, List

from copy import deepcopy

from ..etc.Types import ResourceTypes, Result, NotificationEventType, CSERequest, JSON, BasicType, Operation
from ..etc.ResponseStatusCodes import ResponseException, BAD_REQUEST, INTERNAL_SERVER_ERROR
from ..etc.RequestUtils import removeNoneValuesFromDict
from ..etc.IDUtils import isValidID, uniqueRI, uniqueRN
from ..etc.ACMEUtils import resourceDiff, isUniqueRI
from ..etc.Utils import normalizeURL
from ..helpers.TextTools import findXPath, setXPath
from ..etc.DateUtils import getResourceDate
from ..runtime.Logging import Logging as L
from ..runtime import CSE
from ..etc.Constants import Constants

# Future TODO: Check RO/WO etc for attributes (list of attributes per resource?)
# TODO cleanup optimizations
# TODO _remodeID - is anybody using that one??


internalAttributes	= [ Constants.attrRtype,
					  	Constants.attrSrn, 
						Constants.attrNode, 
						Constants.attrCreatedInternallyRI, 
						Constants.attrImported, 
						Constants.attrIsManuallyInstantiated,
						Constants.attrLocCoordinate,
						Constants.attrOriginator, 
						Constants.attrModified, 
						Constants.attrRemoteID,
						Constants.attrRvi,
						Constants.attrSubscriptionCounter
					 ]
"""	List of internal attributes and which do not belong to the oneM2M resource attributes """


class Resource(object):
	""" Base class for all oneM2M resource types,
	
		Attributes:

	"""

	inheritACP = False
	"""	Flag to indicate if the resource type inherits the ACP from the parent resource. """


	__slots__ = (
		'typeShortname',
		'dict',
		'_originalDict',
	)

	_excludeFromUpdate = [ 'ri', 'ty', 'pi', 'ct', 'lt', 'st', 'rn', 'mgd' ]
	"""	Resource attributes that are excluded when updating the resource """


	def __init__(self, dct:JSON, create:Optional[bool] = False) -> None:
		"""	Initialization of a Resource instance.
		
			Args:
				dct: Mandatory resource attributes.
		"""

		self.dict 		= {}
		"""	Dictionary for public and internal resource attributes. """
		# self._originalDict = {}
		# """	When retrieved from the database: Holds a temporary version of the resource attributes as they were read from the database. """

		if dct is not None: 
			self.dict = deepcopy(dct.get(self.typeShortname))	# type:ignore[has-type]
			if not self.dict:
				self.dict = deepcopy(dct)
		else:
			# no Dict, so the resource is instantiated programmatically
			self.setAttribute(Constants.attrIsManuallyInstantiated, True)
		
		# The original dictionary is only set when the resource is created. It is not
		# required later
		if create:
			self._originalDict = deepcopy(self.dict)	# keep for validation in activate() later



	def initialize(self, pi:str, originator:str) -> None:
		""" This method is called when a new resource is created and before written to the database.

			Args:
				pi: The parent resource's ID.
				originator: The request originator.
		"""
		# Store the shortname of the resource type
		self.setAttribute(Constants.attrRtype, self.typeShortname)

		# Set the parent resource ID
		self.setAttribute('pi', pi if pi is not None else '', overwrite = False) # test for None bc pi might be '' (for cse). pi is used subsequently here

		# if not already set: determine and add the srn
		self.setResourceID()

		# Create an RN if there is none (not given, none in the resource)
		if not self.hasAttribute('rn'):	# a bit of optimization bc the function call might cost some time
			self.setResourceName(uniqueRN(self.typeShortname))

		# Set the internal structure resource name
		self.setSrn(self.structuredPath())

		# Handle resource type
		self.setAttribute('ty', int(self.resourceType))

		# Remove empty / null attributes from dict
		# But see also the comment in update() !!!
		self.dict = removeNoneValuesFromDict(self.dict, ['cr'])	# allow the cr attribute to stay in the dictionary. It will be handled with in the RegistrationManager


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


		# Set some more attributes
		ts = getResourceDate()
		self.setAttribute('ct', ts, overwrite = False)
		self.setAttribute('lt', ts, overwrite = False)

		# Set the internal

		# validate the attributes but only when the resource is not instantiated.
		# We assume that an instantiated resource is always correct
		# Also don't validate virtual resources
		if not self[Constants.attrIsManuallyInstantiated] and not self.isVirtual() :
			CSE.validator.validateAttributes(self._originalDict, 
											 self.typeShortname, 
											 self.ty, 
											 self._attributes, 
											 isImported = self[Constants.attrImported],
											 createdInternally = self.isCreatedInternally(), 
											 isAnnounced = self.isAnnounced())

		# Set the internal originator that creates the resource.
		self.setOriginator(originator, overwrite = False)

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

		self.setAttribute(Constants.attrRtype, self.typeShortname, overwrite = False) 


	def willBeDeactivated(self, originator:str, parentResource:Resource) -> None:
		""" This method is called before a resource will be deactivated.
			
			This method is implemented in some sub-classes, which may throw an
			execption if the resource cannot be deactivated. If it is implemented
			it should call the super class' `willBeDeactivated()` method to check
			for child resources.			

			Args:
				originator: The request originator.
				parentResource: The resource's parent resource.
		"""
		L.isDebug and L.logDebug(f'Perform deactivation check for: {self.ri}')
		
		# Don't do anything when the resource is virtual
		if self.isVirtual():
			return

		# Check all child resources
		for r in CSE.dispatcher.retrieveDirectChildResources(self.ri):
			if r.isVirtual():
				continue
			r.willBeDeactivated(originator, self)


	def deactivate(self, originator:str, parentresource:Resource) -> None:
		"""	Deactivate an active resource.

			This usually happens when creating the resource via a request.
			A subscription check for deletion is performed.

			This method is implemented in sub-classes as well.

			Args:
				originator: The requests originator that let to the deletion of the resource.
				parentResource: The resource's parent resource.
		"""
		L.isDebug and L.logDebug(f'Deactivating and removing sub-resources for: {self.ri}')
		# First check notification because the subscription will be removed
		# when the subresources are removed
		CSE.notification.checkSubscriptions(self, 
									  		NotificationEventType.resourceDelete, 
											originator)
		CSE.notification.checkOperationSubscription(self, Operation.DELETE, originator)
		
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
			# if self.typeShortname not in dct and self.ty not in [ResourceTypes.FCNTAnnc]:	# Don't check announced versions of announced FCNT
			# 	L.isWarn and L.logWarn("Update type doesn't match target")
			# 	raise CONTENTS_UNACCEPTABLE('resource types mismatch')

			# # validate the attributes
			# if doValidateAttributes:
			# 	CSE.validator.validateAttributes(dct, 
			# 									 self.typeShortname, 
			# 									 self.ty, 
			# 									 self._attributes, 
			# 									 create = False, 
			# 									 createdInternally = 
			# 									 self.isCreatedInternally(), 
			# 									 isAnnounced = self.isAnnounced())

			if self.ty not in [ResourceTypes.FCNTAnnc]:
				updatedAttributes = dct[self.typeShortname] # get structure under the resource type specifier
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
		self[Constants.attrModified] = resourceDiff(dictOrg, self.dict, updatedAttributes)


		# Check subscriptions
		CSE.notification.checkSubscriptions(self, 
									  		NotificationEventType.resourceUpdate, 
											originator,
									  		modifiedAttributes = self[Constants.attrModified])
		CSE.notification.checkOperationSubscription(self, Operation.UPDATE, originator)

		self.dbUpdate()

		# Check Attribute Trigger
		# TODO CSE.action.checkTrigger, self, modifiedAttributes=self[Constants.attrModified])

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
		CSE.notification.checkOperationSubscription(self, request.op, originator)	# could also be DISCOVERY


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
		CSE.notification.checkSubscriptions(self, 
									  		NotificationEventType.createDirectChild, 
											originator,
											childResource)
		CSE.notification.checkOperationSubscription(self, Operation.CREATE, originator)



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
		CSE.notification.checkSubscriptions(self, 
									  		NotificationEventType.deleteDirectChild, 
											originator,
											childResource)


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
		
		# check loc validity: geo type and number of coordinates
		if (loc := self.getFinalResourceAttribute('loc', dct)) is not None:

			# The following line is a hack that is necessary because the name "location" is used with different meanings
			# and types in different resources (MgmtObj-DVI and normal resources). This is a quick fix for the moment.
			# It only check if this is a DVI resource. If yes, then the loc attribute is not checked.
			if CSE.validator.getAttributePolicy(self.ty if self.mgd is None else self.mgd, 'loc').type != BasicType.string:
				# crd should have been already check as valid JSON before
				# Let's optimize and store the coordinates as a JSON object
				crd = CSE.validator.validateGeoLocation(loc)
				if dct is not None:
					setXPath(dct, f'{self.typeShortname}/{Constants.attrLocCoordinate}', crd, overwrite = True)
				else:
					self.setLocationCoordinates(crd)


	#########################################################################

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
					if k not in internalAttributes 				# if k is not in internal attributes (starting with __), AND
					and not (noACP and k == 'acpi')						# if not noACP is True and k is 'acpi', AND
					and not (update and k in self._excludeFromUpdate) 	# if not update is True and k is in _excludeFromUpdate)
				}
		if sort:
			dct = dict(sorted(dct.items())) # sort the dictionary by key
		return { self.typeShortname : dct } if embedded else dct


	def isCreatedInternally(self) -> bool:
		""" Test whether a resource has been created for another resource.

			Return:
				True if this resource has been created for another resource.
		"""
		return self[Constants.attrCreatedInternallyRI] is not None


	def setCreatedInternally(self, ri:str) -> None:
		"""	Save the resource ID for which this resource was created for.
		
			This has some impacts on internal handling and checks.

			Args:
				ri: Resource ID of the resource for which this resource has been created for.

		"""
		self[Constants.attrCreatedInternallyRI] = ri


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
	#	Other directed request handling
	#

	def handleNotification(self, request:CSERequest, originator:str) -> None:
		"""	Process a notification request that is directed to a resource.
		
			This method is implemented in some sub-classes. Those implementations
			override this method to handle the notification request.

			Args:
				request: The request to process.
				originator: The request's originator.
			
			Raises:
				`INTERNAL_SERVER_ERROR`: In case the method is not implemented and overridden in a sub-class.
		"""
		raise INTERNAL_SERVER_ERROR('handleNotification() not implemented')


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
		if key in self.dict and overwrite:
			self.dict[key] = value
			return
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
		try:
			return self.dict[key]
		except KeyError:
			return findXPath(self.dict, key, default)


	def hasAttribute(self, key:str) -> bool:
		"""	Check whether an attribute exists for the resource.

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
	

	def getAttributes(self, includingInternal:bool = False) -> dict[str, Any]:
		""" Get all attributes of the resource. 

			Args:
				includingInternal: Optional indicator whether internal attributes shall be included.
		
			Return:
				Dictionary with a copy of all attributes.
		"""
		_dct = deepcopy(self.dict)
		if not includingInternal:
			for key in internalAttributes:
				if key in _dct:
					del _dct[key]
		return _dct
	

	def getFinalResourceAttribute(self, key:str, dct:Optional[JSON]) -> Any:
		"""	Determine and return the final value of an attribute during an update.
		
			Args:
				key: Attribute name.
				dct: The dictionary with updated attributes.
			
			Return:
				The either updated attribute, or old value if the attribute is not updated. The method returns *None* if the attribute does not exists.
		"""
		value = self.attribute(key)	# old value
		if dct is not None:
			_dct = dct[self.typeShortname]
			if key in _dct:
				value = _dct[key]
			# newValue = findXPath(dct, f'{self.typeShortname}/{key}')
			# value = newValue if newValue is not None else value
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
	

	def hasAttributeDefined(self, name:str) -> bool:
		"""	Test whether a resource supports the specified attribute.
			This method may be overwritten in sub-classes, for example for virtual resources.
		
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
		return f'{self.typeShortname}(ri={self.ri}, srn={self.getSrn()})'


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
		return self[Constants.attrOriginator]
	

	def getCurrentOriginator(self) -> str:
		"""	Retrieve the current originator. This could be different from
			the originator / creator of the resource in case of the *custodian* attribute is set.

			Return:
				The current originator.
		"""
		if (cstn := self.custn) is not None:
			return cstn
		return self.getOriginator()


	def setOriginator(self, originator:str, overwrite:Optional[bool] = True) -> None:
		"""	Set a resource's originator.

			This is the originator that created the resource. It is stored internally within the resource.

			Args:
				originator: The originator to assign to a resource.
		"""
		self.setAttribute(Constants.attrOriginator, originator, overwrite = overwrite)
	
	
	def setResourceName(self, rn:str) -> None:
		"""	Set the resource name. 
		
			Also set/update the internal structured resource name.
			
			Args:
				rn: The new resource name for the resource.
		"""

		self.setAttribute('rn', rn)

		# determine and add the srn, only when this is a local resource, otherwise we don't need this information
		# It is *not* a remote resource when the __remoteID__ is set
		if not self[Constants.attrRemoteID]:
			self.setSrn(self.structuredPath())


	def setResourceID(self) -> None:
		"""	Set the resource ID for the resource if not already set.
		"""
		if not self.ri:
			self.setAttribute('ri', uniqueRI(self.typeShortname))
			while not isUniqueRI(self.ri):
				L.isWarn and L.logWarn(f'RI: {self.ri} is already assigned. Generating new RI.')
				self.setAttribute('ri', uniqueRI(self.typeShortname))


	def getSrn(self) -> str:
		"""	Retrieve a resource's full structured resource name.

			Return:
				The resource's full structured resource name.
		"""
		return self[Constants.attrSrn]
	

	def setSrn(self, srn:str) -> None:
		"""	Set a resource's full structured resource name.

			Args:
				srn: The full structured resource name to assign to a resource.
		"""
		self.setAttribute(Constants.attrSrn, srn)


	def getRVI(self) -> str:
		"""	Retrieve a resource's release version indicator.

			Return:
				The resource's *rvi*.
		"""
		return self[Constants.attrRvi]
	

	def setRVI(self, rvi:str) -> None:
		"""	Assign the release version for a resource.

			This is usually assigned from the *rvi* indicator in the resource's CREATE request.

			Args:
				rvi: Original CREATE request's *rvi*.
		"""
		self.setAttribute(Constants.attrRvi, rvi)


	def getLocationCoordinates(self) -> list:
		"""	Retrieve a resource's location coordinates (internal attribute).

			Return:
				The resource's location coordinates. Might be None.
		"""
		return self.attribute(Constants.attrLocCoordinate)
	

	def setLocationCoordinates(self, crd:JSON) -> None:
		"""	Set a resource's location coordinates (internal attribute).

			Args:
				crd: The location coordinates to assign to a resource.
		"""
		self.setAttribute(Constants.attrLocCoordinate, crd)


	def selectAttributes(self, request:CSERequest, attributeList:Optional[list[str]] = None) -> None:
		"""	Determine the selected attributes for a partial retrieve of a resource.

			Args:
				attributeList: The list of attributes to filter.


			Raises:
				BAD_REQUEST: In case an attribute is not defined for the resource.
		"""
		# Validate that the attribute(s) are actual resouce attributes
		if attributeList:
			for a in attributeList:
				if not self.hasAttributeDefined(a):
					raise BAD_REQUEST(L.logWarn(f'Undefined attribute: {a} in partial retrieve for resource type: {self.ty}'))
		
		# Set the selected attributes in the request. The actual filtering is done in the response processing.
		request.selectedAttributes = attributeList
		

	def incrementSubscriptionCounter(self) -> None:
		""" Increment the subscription counter for the resource.

			This is used to determine whether a resource has active subscriptions.
		"""
		ctr = self.getSubscriptionCounter()
		self.setAttribute(Constants.attrSubscriptionCounter, ctr + 1)
		self.dbUpdate()
	

	def decrementSubscriptionCounter(self) -> None:
		""" Decrement the subscription counter for the resource.

			This is used to determine whether a resource has active subscriptions.
		"""
		self.setAttribute(Constants.attrSubscriptionCounter, self.getSubscriptionCounter() - 1)
		self.dbUpdate()
	

	def getSubscriptionCounter(self) -> int:
		""" Retrieve the subscription counter for the resource.

			Return:
				The current subscription counter value.
		"""
		return self.attribute(Constants.attrSubscriptionCounter, 0)


#########################################################################
#
#	Internal helper functions
#

def addToInternalAttributes(name:str) -> None:
	"""	Add a *name* to the names of internal attributes. 
	
		*name* is only added if	it is not already present.

		Args:
			name: Attribute name to add.
	"""
	if name not in internalAttributes:
		internalAttributes.append(name)


def isInternalAttribute(name:str) -> bool:
	"""	Check whether an attribute is an internal attribute.

		Args:
			name: Attribute name to check.
		Return:
			True if the attribute is an internal attribute.
	"""
	return name in internalAttributes
