#
#	Storage.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Store, retrieve and manage resources in the database. It currently relies on
#	the document database TinyDB. It is possible to store resources either on disc
#	or just in memory.
#

"""	This module defines storage managers and drivers for database access.

	Storage managers are used to store, retrieve and manage resources and other runtime data in the database.

	Storage drivers are used to access the database. Currently, the only supported database is TinyDB.

	See also:
		- `TinyDBBetterTable`
		- `TinyDBBufferedStorage`
"""

from __future__ import annotations
from typing import Callable, cast, List, Optional, Sequence

import os, shutil
from threading import Lock
from pathlib import Path
from tinydb import TinyDB, Query
from tinydb.storages import MemoryStorage
from tinydb.table import Document
from tinydb.operations import delete 

from ..etc.Types import ResourceTypes, JSON, Operation
from ..etc.ResponseStatusCodes import ResponseStatusCode, NOT_FOUND, INTERNAL_SERVER_ERROR, CONFLICT
from ..helpers.TinyDBBufferedStorage import TinyDBBufferedStorage
from ..helpers.TinyDBBetterTable import TinyDBBetterTable
from ..etc.DateUtils import utcTime, fromDuration
from ..services.Configuration import Configuration
from ..services import CSE
from ..resources.Resource import Resource
from ..resources.ACTR import ACTR
from ..resources.SCH import SCH
from ..resources.Factory import resourceFromDict
from ..services.Logging import Logging as L


# Constants for database and table names
_resources = 'resources'
""" Name of the resources table. """
_identifiers = 'identifiers'
""" Name of the identifiers table. """
_children = 'children'
""" Name of the children table. """
_subscriptions = 'subscriptions'
""" Name of the subscriptions table. """
_batchNotifications = 'batchNotifications'
""" Name of the batchNotifications table. """
_statistics = 'statistics'
""" Name of the statistics table. """
_actions = 'actions'
""" Name of the actions table. """
_requests = 'requests'
""" Name of the requests table. """
_schedules = 'schedules'
""" Name of the schedules table. """


class Storage(object):
	"""	This class implements the entry points to the CSE's underlying database functions.
	"""

	__slots__ = (
		'inMemory',
		'dbPath',
		'dbReset',
		'db',
	)
	""" Define slots for instance variables. """

	def __init__(self) -> None:
		"""	Initialization of the storage manager.

			Raises:
				RuntimeError: In case of an error during initialization.
		"""

		# create data directory
		self._assignConfig()

		if not self.inMemory:
			if self.dbPath:
				L.isInfo and L.log('Using data directory: ' + self.dbPath)
				os.makedirs(self.dbPath, exist_ok = True)
			else:
				raise RuntimeError(L.logErr('database.path not set'))

		# create DB object and open DB
		self.db = TinyDBBinding(self.dbPath, CSE.cseCsi[1:]) # add CSE CSI as postfix
		""" The database object. """

		# Reset dbs?
		if self.dbReset:
			self._backupDB()	# In this case do a backup *before* startup.
			self.purge()
		
		# Check validity
		if not self.dbReset and not self._validateDB():
			raise RuntimeError('DB error. Please check or remove database files.')
		
		# Make backup *after* validation, only when *not* reset
		if not self.inMemory and not self.dbReset and not self._backupDB():
			raise RuntimeError('DB Error')

		L.isInfo and L.log('Storage initialized')


	def shutdown(self) -> bool:
		"""	Shutdown the storage manager.
		
			Return:
				Always True.
		"""
		self.db.closeDB()
		self.db = None
		L.isInfo and L.log('Storage shut down')
		return True


	def _assignConfig(self) -> None:
		"""	Assign default configurations.
		"""
		self.inMemory 	= Configuration.get('database.inMemory')
		""" Indicator whether the database is located in memory (volatile) or on disk. """
		self.dbPath 	= Configuration.get('database.path')
		""" In case *inMemory* is "False" this attribute contains the path to a directory where the database is stored in disk. """
		self.dbReset 	= Configuration.get('database.resetOnStartup') 
		""" Indicator that the database should be reset or cleared during start-up. """


	def purge(self) -> None:
		"""	Reset and clear the databases.
		"""
		try:
			self.db.purgeDB()
		except Exception as e:
			L.logErr(f'Exception during purge: {e}', exc=e)
			quit()


	def _validateDB(self) -> bool:
		"""	Trying to validate the database files.
		
			This is only a simple test. It performs a couple of read
			operations on the available database files.

			Return:
				Boolean indicating the validity of the databases.

		"""
		L.isDebug and L.logDebug('Validating database files')
		dbFile = ''
		try:
			dbFile = _resources
			self.hasResource('_')
			dbFile = _identifiers
			self.structuredIdentifier('_')
			self.directChildResources('_')
			dbFile = _subscriptions
			self.getSubscription('_')
			dbFile = _batchNotifications
			self.countBatchNotifications('_', '_')
			dbFile = _statistics
			self.getStatistics()
			dbFile = _actions
			self.getActions()
			dbFile = _schedules
			self.getSchedules()

			# TODO requests

		except Exception as e:
			L.logErr(f'Error validating data files. Error in {dbFile} database.', exc = e)
			return False
		return True
	

	def _backupDB(self) -> bool:
		"""	Creating a backup from the DB to a sub directory.

			Return:
				Boolean indicating the success of the backup operation.
		"""
		dir = f'{self.dbPath}/backup'
		L.isDebug and L.logDebug(f'Creating DB backup in directory: {dir}')
		os.makedirs(dir, exist_ok = True)
		return self.db.backupDB(dir)
		

	#########################################################################
	##
	##	Resources
	##


	def createResource(self, resource:Resource, overwrite:Optional[bool] = True) -> None:
		"""	Create a new resource in the database.
		
			Args:
				resource: The resource to store in the database.
				overwrite: Indicator whether an existing resource shall be overwritten.
			
			Raises:
				CONFLICT: In case the resource already exists and *overwrite* is "False".
		"""
		ri  = resource.ri
		srn = resource.getSrn()
		if overwrite:
			L.isDebug and L.logDebug('Resource enforced overwrite')
			self.db.upsertResource(resource, ri)
		else: 
			if not self.hasResource(ri, srn):	# Only when resource with same ri or srn does not exist yet
				self.db.insertResource(resource, ri)
			else:
				raise CONFLICT(L.logWarn(f'Resource already exists (Skipping): {resource} ri: {ri} srn:{srn}'))

		# Add path to identifiers db
		self.db.upsertIdentifier(resource, ri, srn)

		# Add record to childResources db
		self.db.upsertChildResource(resource, ri)


	def hasResource(self, ri:Optional[str] = None, srn:Optional[str] = None) -> bool:
		"""	Check whether a resource with either the ri or the srn already exists.

			Either one of *ri* or *srn* must be provided.

			Args:
				ri: Optional resource ID.
				srn: Optional structured resource name.

			Returns:
				True when a resource with the ID or name exists.
		"""
		return (ri is not None and self.db.hasResource(ri = ri)) or (srn is not None and self.db.hasResource(srn = srn))


	def retrieveResource(self,	ri:Optional[str] = None, 
								csi:Optional[str] = None,
								srn:Optional[str] = None, 
								aei:Optional[str] = None) -> Resource:
		""" Return a resource via different addressing methods. 

			Either one of *ri*, *srn*, *csi*, or *aei* must be provided.

			Args:
				ri:  The resource is retrieved via its rersource ID.
				csi: The resource is retrieved via its CSE-ID.
				srn: The resource is retrieved via its structured resource name.
				aei: The resource is retrieved via its AE-ID.

			Returns:
				The resource.
			
			Raises:
				NOT_FOUND: In case the resource does not exist.
				INTENRAL_SERVER_ERROR: In case of a database inconsistency.
		"""
		resources = []

		if ri:		# get a resource by its ri
			# L.logDebug(f'Retrieving resource ri: {ri}')
			resources = self.db.searchResources(ri = ri)

		elif srn:	# get a resource by its structured rn
			# L.logDebug(f'Retrieving resource srn: {srn}')
			# get the ri via the srn from the identifers table
			resources = self.db.searchResources(srn = srn)

		elif csi:	# get the CSE by its csi
			# L.logDebug(f'Retrieving resource csi: {csi}')
			resources = self.db.searchResources(csi = csi)
		
		elif aei:	# get an AE by its AE-ID
			resources = self.db.searchResources(aei = aei)

		match len(resources):
			case 1:
				return resourceFromDict(resources[0])
			case 0:
				raise NOT_FOUND('resource not found')

		raise INTERNAL_SERVER_ERROR('database inconsistency')


	def retrieveResourceRaw(self, ri:str) -> JSON:
		"""	Retrieve a resource as a raw dictionary.

			Args:
				ri:  The resource is retrieved via its rersource ID.

			Returns:
				The resource dictionary.

			Raises:
				NOT_FOUND: In case the resource does not exist.
				INTENRAL_SERVER_ERROR: In case of a database inconsistency.
		"""
		resources = self.db.searchResources(ri = ri)
		match len(resources):
			case 1:
				return resources[0]
			case 0: 
				raise NOT_FOUND('resource not found')

		raise INTERNAL_SERVER_ERROR('database inconsistency')


	def retrieveResourcesByType(self, ty:ResourceTypes) -> list[Document]:
		""" Return all resources of a certain type. 

			Args:
				ty: resource type to retrieve.

			Returns:
				List of resource *Document* objects	. 
		"""
		# L.logDebug(f'Retrieving all resources ty: {ty}')
		return self.db.searchResources(ty = int(ty))


	def updateResource(self, resource:Resource) -> Resource:
		"""	Update a resource in the database.

			Args:
				resource: Resource to update.

			Return:
				Updated Resource object.
		"""
		ri = resource.ri
		# L.logDebug(f'Updating resource (ty: {resource.ty}, ri: {ri}, rn: {resource.rn})')
		return self.db.updateResource(resource, ri)


	def deleteResource(self, resource:Resource) -> None:
		"""	Delete a resource from the database.

			Args:
				resource: Resource to delete.
			
			Raises:
				NOT_FOUND: In case the resource does not exist.
		"""
		# L.logDebug(f'Removing resource (ty: {resource.ty}, ri: {resource.ri}, rn: {resource.rn})')
		try:
			self.db.deleteResource(resource)
			self.db.deleteIdentifier(resource)
			self.db.removeChildResource(resource)
		except KeyError:
			raise NOT_FOUND(L.logDebug(f'Cannot remove: {resource.ri} (NOT_FOUND). Could be an expected error.'))


	def directChildResources(self, pi:str, 
								   ty:Optional[ResourceTypes|list[ResourceTypes]] = None, 
								   raw:Optional[bool] = False) -> list[Document]|list[Resource]:
		"""	Return a list of direct child resources, or an empty list

			Args:
				pi: The parent resource's Resource ID.
				ty: Optional resource type or list of resource types to filter the result.
				raw: When "True" then return the child resources as resource dictionary instead of resources.

			Returns:
				Return a list of resources, or a list of raw resource dictionaries.
		"""
		if (_ris := self.db.searchChildResourcesByParentRI(pi, ty)):
			docs = [self.db.searchResources(ri = _ri)[0] for _ri in _ris]
			return docs if raw else cast(List[Resource], list(map(lambda x: resourceFromDict(x), docs)))
		return []	# type:ignore[return-value]
	

	def directChildResourcesRI(self, pi:str, 
			    					 ty:Optional[ResourceTypes|list[ResourceTypes]] = None) -> list[str]:
		"""	Return a list of direct child resource IDs, or an empty list

			Args:
				pi: The parent resource's Resource ID.
				ty: Optional resource type or list of resource types to filter the result.

			Returns:
				Return a list of resource IDs.
		"""
		return self.db.searchChildResourcesByParentRI(pi, ty)


	def countDirectChildResources(self, pi:str, ty:Optional[ResourceTypes] = None) -> int:
		"""	Count the number of direct child resources.

			Args:
				pi: The parent resource's Resource ID.
				ty: Optional resource type to filter the result.

			Returns:
				The number of child resources.
		"""
		return len(self.db.searchResources(pi = pi, ty = int(ty) if ty is not None else None))


	def countResources(self) -> int:
		"""	Count the overall number of CSE resources.

			Returns:
				The number of CSE resources.
		"""
		return self.db.countResources()


	def identifier(self, ri:str) -> list[Document]:
		"""	Search for the resource identifer mapping with the given unstructured resource ID.

			Args:
				ri: Unstructured resource ID for the mapping to look for.

			Return:
				List of found resources identifier mappings, or an empty list.
		"""
		return self.db.searchIdentifiers(ri = ri)


	def structuredIdentifier(self, srn:str) -> list[Document]:
		"""	Search for the resource identifer mapping with the given structured resource ID.

			Args:
				srn: Structured resource ID for the mapping to look for.

			Return:
				List of found resources identifier mappings, or an empty list.
		"""
		return self.db.searchIdentifiers(srn = srn)


	def searchByFragment(self, dct:dict, filter:Optional[Callable[[JSON], bool]] = None) -> list[Resource]:
		""" Search and return all resources that match the given fragment dictionary/document.

			Args:
				dct: A fragment dictionary to use as a filter for the search.
				filter: An optional callback to provide additional filter functionality.

			Return:
				List of `Resource` objects.
		"""
		return	[ res	for each in self.db.searchByFragment(dct) 
						if (not filter or filter(each)) and (res := resourceFromDict(each)) # either there is no filter or the filter is called to test the resource
				] 


	def searchByFilter(self, filter:Callable[[JSON], bool]) -> list[Resource]:
		"""	Return a list of resources that match the given filter, or an empty list.

			Args:
				filter: A callback to provide filter functionality.

			Return:
				List of `Resource` objects.
		"""
		return	[ res	for each in self.db.discoverResourcesByFilter(filter)
						if (res := resourceFromDict(each))
				]


	#########################################################################
	##
	##	Subscriptions
	##

	def getSubscription(self, ri:str) -> Optional[Document]:
		"""	Retrieve a subscription representation (not a oneM2M `Resource` object) from the DB.

			Args:
				ri: The subscription's resource ID.

			Return:
				The subscription as a dictionary, or None.
		"""
		# L.logDebug(f'Retrieving subscription: {ri}')
		subs = self.db.searchSubscriptions(ri = ri)
		if not subs or len(subs) != 1:
			return None
		return subs[0]


	def getSubscriptionsForParent(self, pi:str) -> list[Document]:
		"""	Retrieve all subscriptions representations (not oneM2M `Resource` objects) for a parent resource.

			Args:
				pi: The parent resource's resource ID.

			Return:
				List of subscriptions.
		"""
		# L.logDebug(f'Retrieving subscriptions for parent: {pi}')
		return self.db.searchSubscriptions(pi = pi)


	def addSubscription(self, subscription:Resource) -> bool:
		"""	Add a subscription to the DB.
		
			Args:
				subscription: The subscription `Resource` to add.
				
			Return:	
				Boolean value to indicate success or failure.
		"""
		# L.logDebug(f'Adding subscription: {ri}')
		return self.db.upsertSubscription(subscription)


	def removeSubscription(self, subscription:Resource) -> bool:
		"""	Remove a subscription from the DB.

			Args:
				subscription: The subscription `Resource` to remove.

			Return:
				Boolean value to indicate success or failure.
			
			Raises:
				NOT_FOUND: In case the subscription does not exist.
		"""
		# L.logDebug(f'Removing subscription: {subscription.ri}')
		try:
			return self.db.removeSubscription(subscription)
		except KeyError as e:
			raise NOT_FOUND(L.logDebug(f'Cannot subscription data for: {subscription.ri} (NOT_FOUND). Could be an expected error.'))


	def updateSubscription(self, subscription:Resource) -> bool:
		"""	Update a subscription representation in the DB.

			Args:
				subscription: The subscription `Resource` to update.

			Return:
				Boolean value to indicate success or failure.
		"""
		# L.logDebug(f'Updating subscription: {ri}')
		return self.db.upsertSubscription(subscription)


	#########################################################################
	##
	##	BatchNotifications
	##

	def addBatchNotification(self, ri:str, nu:str, request:JSON) -> bool:
		"""	Add a batch notification to the DB.
		
			Args:
				ri: The resource ID of the target resource.
				nu: The notification URI.
				request: The request to store.
				
			Return:
				Boolean value to indicate success or failure.
		"""
		return self.db.addBatchNotification(ri, nu, request)


	def countBatchNotifications(self, ri:str, nu:str) -> int:
		"""	Count the number of batch notifications for a target resource and a notification URI.
		
			Args:
				ri: The resource ID of the target resource.
				nu: The notification URI.
				
			Return:
				The number of matching batch notifications.
		"""
		return self.db.countBatchNotifications(ri, nu)


	def getBatchNotifications(self, ri:str, nu:str) -> list[Document]:
		"""	Retrieve the batch notifications for a target resource and a notification URI.
		
			Args:
				ri: The resource ID of the target resource.
				nu: The notification URI.
				
			Return:
				List of batch notifications.
		"""
		return self.db.getBatchNotifications(ri, nu)


	def removeBatchNotifications(self, ri:str, nu:str) -> bool:
		"""	Remove the batch notifications for a target resource and a notification URI.

			Args:
				ri: The resource ID of the target resource.
				nu: The notification URI.
			
			Return:
				Boolean value to indicate success or failure.
		"""
		return self.db.removeBatchNotifications(ri, nu)


	#########################################################################
	##
	##	Statistics
	##

	def getStatistics(self) -> JSON:
		"""	Retrieve the statistics data from the DB.

			Return:
				The statistics data as a JSON dictionary.
		"""
		return self.db.searchStatistics()


	def updateStatistics(self, stats:JSON) -> bool:
		"""	Update the statistics DB with new data.

			Args:
				stats: The statistics data to store.

			Return:
				Boolean value to indicate success or failure.
		"""
		return self.db.upsertStatistics(stats)


	def purgeStatistics(self) -> None:
		"""	Purge the statistics DB.

			Return:
				Boolean value to indicate success or failure.
		"""
		self.db.purgeStatistics()


	#########################################################################
	##
	##	Actions
	##

	def getActions(self) -> list[Document]:
		"""	Retrieve all action representations from the DB.

			Return:
				List of *Documents*. May be empty.
		"""
		return self.db.searchActionReprs()
	

	def getAction(self, ri:str) -> Optional[Document]:
		"""	Retrieve the actions representation from the DB.

			Args:
				ri: The action's resource ID.

			Return:
				The action's data as a *Document*, or None.
		"""
		return self.db.getAction(ri)

	
	def searchActionsForSubject(self, ri:str) -> Sequence[JSON]:
		"""	Search for actions for a subject resource.
		
			Args:
				ri: The subject resource's resource ID.
			
			Return:
				List of matching action representations.
		"""
		return self.db.searchActionsDeprsForSubject(ri)


	def updateAction(self, action:ACTR, period:float, count:int) -> bool:
		"""	Update or add an action representation in the DB.
		
			Args:
				action: The action to update or insert.
				period: The period for the action.
				count: The run count for the action.

			Return:
				Boolean value to indicate success or failure.
		"""
		return self.db.upsertActionRepr(action, period, count)


	def updateActionRepr(self, actionRepr:JSON) -> bool:
		"""	Update an action representation in the DB.
		
			Args:
				actionRepr: The action representation to update.

			Return:
				Boolean value to indicate success or failure.
		"""
		return self.db.updateActionRepr(actionRepr)


	def removeAction(self, ri:str) -> bool:
		"""	Remove an action representation from the DB.
		
			Args:
				ri: The action's resource ID.

			Return:
				Boolean value to indicate success or failure.
		"""
		return self.db.removeActionRepr(ri)


	#########################################################################
	##
	##	Requests
	##

	def addRequest(self, op:Operation, 
						 ri:str, 
						 srn:str, 
						 originator:str, 
						 outgoing:bool, 
						 ot:str,
						 request:JSON, 
						 response:JSON) -> bool:
		"""	Add a request to the *requests* database.
		
			Args:
				op: Operation.
				ri: Resource ID of a request's target resource.
				srn: Structured resource ID of a request's target resource.
				originator: Request originator.
				outgoing: If true, then this is a request sent by the CSE.
				ot: Request creation time.
				request: The request to store.
				response: The response to store.
			
			Return:
				Boolean value to indicate success or failure.
			"""
		return self.db.insertRequest(op, ri, srn, originator, outgoing, ot, request, response)


	def getRequests(self, ri:Optional[str] = None, sortedByOt:bool = False) -> list[Document]:
		"""	Get requests for a resource ID, or all requests.
		
			Args:
				ri: The target resource's resource ID. If *None* or empty, then all requests are returned
				sortedByOt: If true, then the requests are sorted by their creation time.
			
			Return:
				List of *Documents*. May be empty.
		"""

		if sortedByOt:
			return sorted(self.db.getRequests(ri), key = lambda x: x['ot'])
		return self.db.getRequests(ri)
	

	def deleteRequests(self, ri:Optional[str] = None) -> None:
		"""	Delete all requests from the database.

			Args:
				ri: Optional resouce ID. Only requests for this resource ID will be deleted.
		"""
		return self.db.deleteRequests(ri)


	#########################################################################
	##
	##	Schedules
	##

	def getSchedules(self) -> list[Document]:
		"""	Retrieve the schedules data from the DB.

			Return:
				List of *Documents*. May be empty.
		"""
		return self.db.getSchedules()


	def searchScheduleForTarget(self, pi:str) -> list[str]:
		"""	Search for schedules for a target resource.

			Args:
				pi: The target resource's resource ID.
			
			Return:
				List of schedule resource IDs.
		"""
		result = []
		for s in self.db.searchSchedules(pi):
			result.extend(s['sce'])
		return result


	def upsertSchedule(self, schedule:SCH) -> bool:
		"""	Add or update a schedule in the DB.

			Args:
				schedule: The schedule to add or update.

			Return:
				Boolean value to indicate success or failure.
		"""
		return self.db.upsertSchedule(schedule.ri, schedule.pi, schedule.attribute('se/sce'))


	def removeSchedule(self, schedule:SCH) -> bool:
		"""	Remove a schedule from the DB.

			Args:
				schedule: The schedule to remove.
			
			Return:
				Boolean value to indicate success or failure.
		"""
		return self.db.removeSchedule(schedule.ri)

#########################################################################
#
#	DB class that implements the TinyDB binding
#
#	This class may be moved later to an own module.


class TinyDBBinding(object):
	"""	This class implements the TinyDB binding to the database. It is used by the Storage class.
	"""

	__slots__ = (
		'path',
		'cacheSize',
		'writeDelay',
		'maxRequests',
		
		'lockResources',
		'lockIdentifiers',
		'lockChildResources',
		'lockStructuredIDs',
		'lockSubscriptions',
		'lockBatchNotifications',
		'lockStatistics',
		'lockActions',
		'lockRequests',
		'lockSchedules',

		'fileResources',
		'fileIdentifiers',
		'fileSubscriptions',
		'fileBatchNotifications',
		'fileStatistics',
		'fileActions',
		'fileRequests',
		'fileSchedules',
		
		'dbResources',
		'dbIdentifiers', 		
		'dbSubscriptions', 	
		'dbBatchNotifications',
		'dbStatistics',
		'dbActions',	
		'dbRequests',	
		'dbSchedules',	

		'tabResources',
		'tabIdentifiers',
		'tabChildResources',
		'tabStructuredIDs',
		'tabSubscriptions',
		'tabBatchNotifications',
		'tabStatistics',
		'tabActions',
		'tabRequests',
		'tabSchedules',

		'resourceQuery',
		'identifierQuery',
		'subscriptionQuery',
		'batchNotificationQuery',
		'actionsQuery',
		'requestsQuery',
		'schedulesQuery',
	)
	""" Define slots for instance variables. """

	def __init__(self, path:str, postfix:str) -> None:
		"""	Initialize the TinyDB binding.
		
			Args:
				path: Path to the database directory.
				postfix: Postfix for the database file names.
		"""
		
		self.path = path
		""" Path to the database directory. """
		self._assignConfig()
		""" Assign configuration values. """
		L.isInfo and L.log(f'Cache Size: {self.cacheSize:d}')

		# create transaction locks
		self.lockResources				= Lock()
		""" Lock for the resources table."""
		self.lockIdentifiers			= Lock()
		""" Lock for the identifiers table."""
		self.lockChildResources			= Lock()
		""" Lock for the childResources table."""
		self.lockStructuredIDs			= Lock()
		""" Lock for the structuredIDs table."""
		self.lockSubscriptions			= Lock()
		""" Lock for the subscriptions table."""
		self.lockBatchNotifications		= Lock()
		""" Lock for the batchNotifications table."""
		self.lockStatistics 			= Lock()
		""" Lock for the statistics table."""
		self.lockActions 				= Lock()
		""" Lock for the actions table."""
		self.lockRequests 				= Lock()
		""" Lock for the requests table."""
		self.lockSchedules 				= Lock()
		""" Lock for the schedules table."""

		# file names
		self.fileResources				= f'{self.path}/{_resources}-{postfix}.json'
		""" Filename for the resources table."""
		self.fileIdentifiers			= f'{self.path}/{_identifiers}-{postfix}.json'
		""" Filename for the identifiers table."""
		self.fileSubscriptions			= f'{self.path}/{_subscriptions}-{postfix}.json'
		""" Filename for the subscriptions table."""
		self.fileBatchNotifications		= f'{self.path}/{_batchNotifications}-{postfix}.json'
		""" Filename for the batchNotifications table."""
		self.fileStatistics				= f'{self.path}/{_statistics}-{postfix}.json'
		""" Filename for the statistics table."""
		self.fileActions				= f'{self.path}/{_actions}-{postfix}.json'
		""" Filename for the actions table."""
		self.fileRequests				= f'{self.path}/{_requests}-{postfix}.json'
		""" Filename for the requests table."""
		self.fileSchedules				= f'{self.path}/{_schedules}-{postfix}.json'
		""" Filename for the schedules table."""

		# All databases/tables will use the smart query cache
		if Configuration.get('database.inMemory'):
			L.isInfo and L.log('DB in memory')
			self.dbResources 			= TinyDB(storage = MemoryStorage)
			""" The TinyDB database for the resources table."""
			self.dbIdentifiers 			= TinyDB(storage = MemoryStorage)
			""" The TinyDB database for the identifiers table."""
			self.dbSubscriptions 		= TinyDB(storage = MemoryStorage)
			""" The TinyDB database for the subscriptions table."""
			self.dbBatchNotifications	= TinyDB(storage = MemoryStorage)
			""" The TinyDB database for the batchNotifications table."""
			self.dbStatistics			= TinyDB(storage = MemoryStorage)
			""" The TinyDB database for the statistics table."""
			self.dbActions				= TinyDB(storage = MemoryStorage)
			""" The TinyDB database for the actions table."""
			self.dbRequests				= TinyDB(storage = MemoryStorage)
			""" The TinyDB database for the requests table."""
			self.dbSchedules			= TinyDB(storage = MemoryStorage)
			""" The TinyDB database for the schedules table."""
		else:
			L.isInfo and L.log('DB in file system')
			self.dbResources 			= TinyDB(self.fileResources, storage = TinyDBBufferedStorage, write_delay = self.writeDelay)
			""" The TinyDB database for the resources table."""
			self.dbIdentifiers 			= TinyDB(self.fileIdentifiers, storage = TinyDBBufferedStorage, write_delay = self.writeDelay)
			""" The TinyDB database for the identifiers table."""
			self.dbSubscriptions 		= TinyDB(self.fileSubscriptions, storage = TinyDBBufferedStorage, write_delay = self.writeDelay)
			""" The TinyDB database for the subscriptions table."""
			self.dbBatchNotifications 	= TinyDB(self.fileBatchNotifications, storage = TinyDBBufferedStorage, write_delay = self.writeDelay)
			""" The TinyDB database for the batchNotifications table."""
			self.dbStatistics 			= TinyDB(self.fileStatistics, storage = TinyDBBufferedStorage, write_delay = self.writeDelay)
			""" The TinyDB database for the statistics table."""
			self.dbActions	 			= TinyDB(self.fileActions, storage = TinyDBBufferedStorage, write_delay = self.writeDelay)
			""" The TinyDB database for the actions table."""
			self.dbRequests	 			= TinyDB(self.fileRequests, storage = TinyDBBufferedStorage, write_delay = self.writeDelay)
			""" The TinyDB database for the requests table."""
			self.dbSchedules	 		= TinyDB(self.fileSchedules, storage = TinyDBBufferedStorage, write_delay = self.writeDelay)
			""" The TinyDB database for the schedules table."""

		
		# Open/Create tables
		self.tabResources = self.dbResources.table(_resources, cache_size = self.cacheSize)
		""" The TinyDB table for the resources table."""
		TinyDBBetterTable.assign(self.tabResources)
		
		self.tabIdentifiers = self.dbIdentifiers.table(_identifiers, cache_size = self.cacheSize)
		""" The TinyDB table for the identifiers table."""
		TinyDBBetterTable.assign(self.tabIdentifiers)

		self.tabChildResources = self.dbIdentifiers.table(_children, cache_size = self.cacheSize)
		""" The TinyDB table for the childResources table."""
		TinyDBBetterTable.assign(self.tabChildResources)

		self.tabStructuredIDs = self.dbIdentifiers.table('srn', cache_size = self.cacheSize)
		""" The TinyDB table for the structuredIDs table."""
		TinyDBBetterTable.assign(self.tabStructuredIDs)
		
		self.tabSubscriptions = self.dbSubscriptions.table(_subscriptions, cache_size = self.cacheSize)
		""" The TinyDB table for the subscriptions table."""
		TinyDBBetterTable.assign(self.tabSubscriptions)
		
		self.tabBatchNotifications = self.dbBatchNotifications.table(_batchNotifications, cache_size = self.cacheSize)
		""" The TinyDB table for the batchNotifications table."""
		TinyDBBetterTable.assign(self.tabBatchNotifications)
		
		self.tabStatistics = self.dbStatistics.table(_statistics, cache_size = self.cacheSize)
		""" The TinyDB table for the statistics table."""
		TinyDBBetterTable.assign(self.tabStatistics)

		self.tabActions = self.dbActions.table(_actions, cache_size = self.cacheSize)
		""" The TinyDB table for the actions table."""
		TinyDBBetterTable.assign(self.tabActions)

		self.tabRequests = self.dbRequests.table(_requests, cache_size = self.cacheSize)
		""" The TinyDB table for the requests table."""
		TinyDBBetterTable.assign(self.tabRequests)

		self.tabSchedules = self.dbSchedules.table(_schedules, cache_size = self.cacheSize)
		""" The TinyDB table for the schedules table."""
		TinyDBBetterTable.assign(self.tabSchedules)



		# Create the Queries
		self.resourceQuery 				= Query()
		""" The TinyDB query object for the resources table."""
		self.identifierQuery 			= Query()
		""" The TinyDB query object for the identifiers table."""
		self.subscriptionQuery			= Query()
		""" The TinyDB query object for the subscriptions table."""
		self.batchNotificationQuery 	= Query()
		""" The TinyDB query object for the batchNotifications table."""
		self.actionsQuery				= Query()
		""" The TinyDB query object for the actions table."""
		self.requestsQuery				= Query()
		""" The TinyDB query object for the requests table."""
		self.schedulesQuery				= Query()
		""" The TinyDB query object for the schedules table."""


	def _assignConfig(self) -> None:
		"""	Assign default configurations.
		"""
		self.cacheSize = Configuration.get('database.cacheSize')
		""" Size of the cache for the TinyDB tables. """
		self.writeDelay = Configuration.get('database.writeDelay')
		""" Delay for writing to the database. """
		self.maxRequests = Configuration.get('cse.operation.requests.size')
		""" Maximum number of oneM2M recorded requests to keep in the database. """


	def closeDB(self) -> None:
		"""	Close the database.
		"""
		L.isInfo and L.log('Closing DBs')
		with self.lockResources:
			self.dbResources.close()
		with self.lockIdentifiers:
			self.dbIdentifiers.close()
		with self.lockSubscriptions:
			self.dbSubscriptions.close()
		with self.lockBatchNotifications:
			self.dbBatchNotifications.close()
		with self.lockStatistics:
			self.dbStatistics.close()
		with self.lockActions:
			self.dbActions.close()
		with self.lockRequests:
			self.dbRequests.close()
		with self.lockSchedules:
			self.dbSchedules.close()


	def purgeDB(self) -> None:
		"""	Purge the database.
		"""
		L.isInfo and L.log('Purging DBs')
		self.tabResources.truncate()
		self.tabIdentifiers.truncate()
		self.tabChildResources.truncate()
		self.tabStructuredIDs.truncate()
		self.tabSubscriptions.truncate()
		self.tabBatchNotifications.truncate()
		self.tabStatistics.truncate()
		self.tabActions.truncate()
		self.tabRequests.truncate()
		self.tabSchedules.truncate()
	

	def backupDB(self, dir:str) -> bool:
		"""	Backup the database to a directory.
		
			Args:
				dir: The directory to backup to.

			Return:
				Boolean value to indicate success or failure.
		"""
		for fn in [	self.fileResources,
					self.fileIdentifiers,
					self.fileSubscriptions,
					self.fileBatchNotifications,
					self.fileStatistics,
					self.fileActions,
					self.fileRequests,
					self.fileSchedules
					]:
			if Path(fn).is_file():
				shutil.copy2(fn, dir)
		return True


	#
	#	Resources
	#


	def insertResource(self, resource: Resource, ri:str) -> None:
		"""	Insert a resource into the database.
		
			Args:
				resource: The resource to insert.
				ri: The resource ID of the resource.
		"""
		with self.lockResources:
			self.tabResources.insert(Document(resource.dict, ri))	# type:ignore[arg-type]
	

	def upsertResource(self, resource: Resource, ri:str) -> None:
		"""	Update or insert a resource into the database.
		
			Args:
				resource: The resource to upate or insert.
				ri: The resource ID of the resource.
		"""
		#L.logDebug(resource)
		with self.lockResources:
			# Update existing or insert new when overwriting
			self.tabResources.upsert(Document(resource.dict, doc_id = ri))	# type:ignore[arg-type]
	

	def updateResource(self, resource: Resource, ri:str) -> Resource:
		"""	Update a resource in the database. Only the fields that are not None will be updated.
		
			Args:
				resource: The resource to update.
				ri: The resource ID of the resource.

			Return:
				The updated resource.
		"""
		#L.logDebug(resource)
		with self.lockResources:
			self.tabResources.update(resource.dict, doc_ids = [ri])	# type:ignore[call-arg, list-item]
			# remove nullified fields from db and resource
			for k in list(resource.dict):
				if resource.dict[k] is None:	# only remove the real None attributes, not those with 0
					self.tabResources.update(delete(k), doc_ids = [ri])	# type: ignore[no-untyped-call, call-arg, list-item]
					del resource.dict[k]
			return resource


	def deleteResource(self, resource:Resource) -> None:
		"""	Delete a resource from the database.

			Args:
				resource: The resource to delete.
		"""
		with self.lockResources:
			self.tabResources.remove(doc_ids = [resource.ri])	
	

	def searchResources(self, ri:Optional[str] = None, 
							  csi:Optional[str] = None, 
							  srn:Optional[str] = None, 
							  pi:Optional[str] = None, 
							  ty:Optional[int] = None, 
							  aei:Optional[str] = None) -> list[Document]:
		"""	Search for resources by structured resource name, resource ID, CSE-ID, parent resource ID, resource type,
		 	or application entity ID.
			
			Only one of the parameters may be used at a time. The order of precedence is: structured resource name,
			resource ID, CSE-ID, structured resource name, parent resource ID, resource type, application entity ID.

			Args:
				ri: A resource ID.
				csi: A CSE ID.
				srn: A structured resource name.
				pi: A parent resource ID.
				ty: A resource type.
				aei: An application entity ID.
			
			Return:
				A list of found resources, or an empty list.
		"""
		if not srn:
			with self.lockResources:
				if ri:
					_r = self.tabResources.get(doc_id = ri)	# type:ignore[arg-type]
					return [_r] if _r else [] 	# type:ignore[list-item]
				elif csi:
					return self.tabResources.search(self.resourceQuery.csi == csi)	
				elif pi:
					if ty is not None:	# ty is an int
						return self.tabResources.search((self.resourceQuery.pi == pi) & (self.resourceQuery.ty == ty))
					return self.tabResources.search(self.resourceQuery.pi == pi)
				elif ty is not None:	# ty is an int
					return self.tabResources.search(self.resourceQuery.ty == ty)	
				elif aei:
					return self.tabResources.search(self.resourceQuery.aei == aei)	
		
		else:
			# for SRN find the ri first and then try again recursively (outside the lock!!)
			if len((identifiers := self.searchIdentifiers(srn = srn))) == 1:
				return self.searchResources(ri = identifiers[0]['ri'])

		return []


	def discoverResourcesByFilter(self, func:Callable[[JSON], bool]) -> list[Document]:
		"""	Search for resources by a filter function.

			Args:
				func: The filter function to use.

			Return:
				A list of found resource documents, or an empty list.
		"""
		with self.lockResources:
			return self.tabResources.search(func)	# type: ignore [arg-type]


	def hasResource(self, ri:Optional[str] = None, 
						  csi:Optional[str] = None, 
						  srn:Optional[str] = None,
						  ty:Optional[int] = None) -> bool:
		"""	Check if a resource exists in the database.

			Only one of the parameters may be used at a time. The order of precedence is: structured resource name,
			resource ID, CSE-ID, resource type.
			
			Args:
				ri: A resource ID.
				csi: A CSE ID.
				srn: A structured resource name.
				ty: A resource type.
			
			Return:
				True if the resource exists, False otherwise.
		"""
		if not srn:
			with self.lockResources:
				if ri:
					return self.tabResources.contains(doc_id = ri)	# type:ignore[arg-type]
				elif csi :
					return self.tabResources.contains(self.resourceQuery.csi == csi)
				elif ty is not None:	# ty is an int
					return self.tabResources.contains(self.resourceQuery.ty == ty)
		else:
			# find the ri first and then try again recursively
			if len((identifiers := self.searchIdentifiers(srn = srn))) == 1:
				return self.hasResource(ri = identifiers[0]['ri'])
		return False


	def countResources(self) -> int:
		"""	Return the number of resources in the database.
		
			Return:
				The number of resources in the database.
		"""
		with self.lockResources:
			return len(self.tabResources)


	def searchByFragment(self, dct:dict) -> list[Document]:
		""" Search and return all resources that match the given dictionary/document. 
		
			Args:
				dct: The dictionary/document to search for.
				
			Return:
				A list of found resources, or an empty list.
		"""
		with self.lockResources:
			return self.tabResources.search(self.resourceQuery.fragment(dct))

	#
	#	Identifiers, Structured RI, Child Resources
	#

	def upsertIdentifier(self, resource:Resource, ri:str, srn:str) -> None:
		"""	Insert or update an identifier into the identifiers DB.

			Args:
				resource: The resource to insert.
				ri: The resource ID of the resource.
				srn: The structured resource name of the resource.
		"""
		# L.isDebug and L.logDebug({'ri' : ri, 'rn' : resource.rn, 'srn' : srn, 'ty' : resource.ty})		
		with self.lockIdentifiers:
			self.tabIdentifiers.upsert(Document(
				{	'ri' : ri, 
					'rn' : resource.rn, 
					'srn' : srn,
					'ty' : resource.ty 
				}, ri))	# type:ignore[arg-type]

		with self.lockStructuredIDs:
			self.tabStructuredIDs.upsert(
				Document({'srn': srn,
				  		  'ri' : ri 
						 }, srn))	# type:ignore[arg-type]


	def deleteIdentifier(self, resource:Resource) -> None:
		"""	Delete an identifier from the identifiers DB.

			Args:
				resource: The resource for which to delete the identifier.
		"""
		with self.lockIdentifiers:
			self.tabIdentifiers.remove(doc_ids = [resource.ri])

		with self.lockStructuredIDs:
			self.tabStructuredIDs.remove(doc_ids = [resource.getSrn()])	# type:ignore[arg-type,list-item]


	def searchIdentifiers(self, ri:Optional[str] = None, 
								srn:Optional[str] = None) -> list[Document]:
		"""	Search for an resource ID OR for a structured name in the identifiers DB.

			Either *ri* or *srn* shall be given. If both are given then *srn*
			is taken.
		
			Args:
				ri: Resource ID to search for.
				srn: Structured path to search for.
			Return:
				A list of found identifier documents (see `upsertIdentifier`), or an empty list if not found.
		 """
		_r:Document
		if srn:
			if (_r := self.tabStructuredIDs.get(doc_id = srn)):	# type:ignore[arg-type, assignment]
				ri = _r['ri'] if _r else None 
			else:
				return []

		if ri:
			with self.lockIdentifiers:
				_r = self.tabIdentifiers.get(doc_id = ri)	# type:ignore[arg-type, assignment]
				return [_r] if _r else []
		return []


	def upsertChildResource(self, resource:Resource, ri:str) -> None:
		"""	Add a child resource to the childResources DB.

			Args:
				resource: The resource to add as a child.
				ri: The resource ID of the resource.
		"""
		# L.isDebug and L.logDebug(f'insertChildResource ri:{ri}')		

		pi = resource.pi
		ty = resource.ty
		with self.lockChildResources:

			# First add a new record
			self.tabChildResources.upsert(
				Document({'ri' : ri,
				  		  'ch' : [] 
						 }, ri))	# type:ignore[arg-type]

			# Then add the child ri to the parent's record
			if pi:	# ATN: CSE has no parent
				_r:Document
				_r = self.tabChildResources.get(doc_id = pi) # type:ignore[arg-type, assignment]
				_ch = _r['ch']
				if ri not in _ch:
					_ch.append( [ri, ty] )
					_r['ch'] = _ch
					self.tabChildResources.update(_r, doc_ids = [pi])	# type:ignore[arg-type, list-item]

			
	def removeChildResource(self, resource:Resource) -> None:
		"""	Remove a child resource from the childResources DB.

			Args:
				resource: The resource to remove as a child.
		"""
		ri = resource.ri
		pi = resource.pi

		# L.isDebug and L.logDebug(f'removeChildResource ri:{ri} pi:{pi}')		
		with self.lockChildResources:

			# First remove the record
			self.tabChildResources.remove(doc_ids = [ri])	# type:ignore[arg-type, list-item]

			# Remove (ri, ty) tuple from parent record
			_r:Document = self.tabChildResources.get(doc_id = pi) # type:ignore[arg-type, assignment]
			_t = [ri, resource.ty]
			_ch = _r['ch']
			if _t in _ch:
				_ch.remove(_t)
				_r['ch'] = _ch
				# L.isDebug and L.logDebug(f'removeChildResource _r:{_r}')		
				self.tabChildResources.update(_r, doc_ids = [pi])	# type:ignore[arg-type, list-item]


	def searchChildResourcesByParentRI(self, pi:str, ty:Optional[ResourceTypes|list[ResourceTypes]] = None) -> list[str]:
		"""	Search for child resources by parent resource ID.

			Args:
				pi: The parent resource ID.
				ty: The resource type of the child resources to search for, or a list of resource types.

			Return:
				A list of child resource IDs, or an empty list if not found.
		"""
		# First convert ty to a list if it is just an int
		if isinstance(ty, int):
			ty = [ty]
		_r:Document = self.tabChildResources.get(doc_id = pi) #type:ignore[arg-type, assignment]
		if _r:
			if ty is None:	# optimization: only check ty once for None
				return [ c[0] for c in _r['ch'] ]
			return [ c[0] for c in _r['ch'] if c[1] in ty]	# c is a tuple (ri, ty)
		return []

	#
	#	Subscriptions
	#


	def searchSubscriptions(self, ri:Optional[str] = None, 
								  pi:Optional[str] = None) -> Optional[list[Document]]:
		"""	Search for subscription representations by resource ID or parent resource ID.

			Only one of the parameters may be used at a time. The order of precedence is: resource ID, parent resource ID.

			Args:
				ri: A resource ID.
				pi: A parent resource ID.

			Return:
				A list of found subscription representations, or None.
		"""
		with self.lockSubscriptions:
			if ri:
				_r:Document = self.tabSubscriptions.get(doc_id =  ri)	# type:ignore[arg-type, assignment]
				return [_r] if _r else []
			if pi:
				return self.tabSubscriptions.search(self.subscriptionQuery.pi == pi)
			return None


	def upsertSubscription(self, subscription:Resource) -> bool:
		"""	Update or insert a subscription representation into the database.

			Args:
				subscription: The `SUB` (subscription) to update or insert.

			Return:
				True if the subscription representation was updated or inserted, False otherwise.
		"""
		with self.lockSubscriptions:
			ri = subscription.ri
			return self.tabSubscriptions.upsert(
				Document({'ri'  	: ri, 
						  'pi'  	: subscription.pi,
						  'nct' 	: subscription.nct,
						  'net' 	: subscription['enc/net'],	# TODO perhaps store enc as a whole?
						  'atr' 	: subscription['enc/atr'],
						  'chty'	: subscription['enc/chty'],
						  'exc' 	: subscription.exc,
						  'ln'  	: subscription.ln,
						  'nus' 	: subscription.nu,
						  'bn'  	: subscription.bn,
						  'cr'  	: subscription.cr,
						  'nec'  	: subscription.nec,
						  'org'		: subscription.getOriginator(),
						  'ma' 		: fromDuration(subscription.ma) if subscription.ma else None, # EXPERIMENTAL ma = maxAge
						  'nse' 	: subscription.nse
						 }, ri)) is not None
					# self.subscriptionQuery.ri == ri) is not None


	def removeSubscription(self, subscription:Resource) -> bool:
		"""	Remove a subscription representation from the database.

			Args:
				subscription: The `SUB` (subscription) to remove.

			Return:
				True if the subscription representation was removed, False otherwise.
		"""
		with self.lockSubscriptions:
			return len(self.tabSubscriptions.remove(doc_ids = [subscription.ri])) > 0
			# return len(self.tabSubscriptions.remove(self.subscriptionQuery.ri == _ri)) > 0


	#
	#	BatchNotifications
	#

	def addBatchNotification(self, ri:str, nu:str, notificationRequest:JSON) -> bool:
		"""	Add a batch notification to the database.

			Args:
				ri: The resource ID of the resource.
				nu: The notification URI.
				notificationRequest: The notification request.

			Return:
				True if the batch notification was added, False otherwise.
		"""
		with self.lockBatchNotifications:
			return self.tabBatchNotifications.insert( 
					{	'ri' 		: ri,
						'nu' 		: nu,
						'tstamp'	: utcTime(),
						'request'	: notificationRequest
					}) is not None


	def countBatchNotifications(self, ri:str, nu:str) -> int:
		"""	Return the number of batch notifications for a resource and notification URI.

			Args:
				ri: The resource ID of the resource.
				nu: The notification URI.

			Return:
				The number of batch notifications for the resource and notification URI.
		"""
		with self.lockBatchNotifications:
			return self.tabBatchNotifications.count((self.batchNotificationQuery.ri == ri) & (self.batchNotificationQuery.nu == nu))


	def getBatchNotifications(self, ri:str, nu:str) -> list[Document]:
		"""	Return the batch notifications for a resource and notification URI.

			Args:
				ri: The resource ID of the resource.
				nu: The notification URI.

			Return:
				A list of batch notifications for the resource and notification URI.
		"""
		with self.lockBatchNotifications:
			return self.tabBatchNotifications.search((self.batchNotificationQuery.ri == ri) & (self.batchNotificationQuery.nu == nu))


	def removeBatchNotifications(self, ri:str, nu:str) -> bool:
		"""	Remove the batch notifications for a resource and notification URI.

			Args:
				ri: The resource ID of the resource.
				nu: The notification URI.

			Return:
				True if the batch notifications were removed, False otherwise.
		"""
		with self.lockBatchNotifications:
			return len(self.tabBatchNotifications.remove((self.batchNotificationQuery.ri == ri) & (self.batchNotificationQuery.nu == nu))) > 0


	#
	#	Statistics
	#

	def searchStatistics(self) -> JSON:
		"""	Search for statistics.

			Return:
				The statistics, or None if not found.
		"""
		with self.lockStatistics:
			stats = self.tabStatistics.all()
			# stats = self.tabStatistics.get(doc_id = 1)
			# return stats if stats is not None and len(stats) > 0 else None
			return stats[0] if stats else None


	def upsertStatistics(self, stats:JSON) -> bool:
		"""	Update or insert statistics.

			Args:
				stats: The statistics to update or insert.

			Return:
				True if the statistics were updated or inserted, False otherwise.
		"""
		with self.lockStatistics:
			if len(self.tabStatistics) > 0:
				doc_id = self.tabStatistics.all()[0].doc_id
				#return self.tabStatistics.update(stats, doc_ids = [1]) is not None
				return self.tabStatistics.update(stats, doc_ids = [doc_id]) is not None
			else:
				return self.tabStatistics.insert(stats) is not None


	def purgeStatistics(self) -> None:
		"""	Purge the statistics DB.
		"""
		with self.lockStatistics:
			self.tabStatistics.truncate()


	#
	#	Actions
	#

	def searchActionReprs(self) -> list[Document]:
		"""	Search for action representations.
		
			Return:
				A list of action representations, or None if not found.
		"""
		with self.lockActions:
			actions = self.tabActions.all()
			return actions if actions else None
	

	def getAction(self, ri:str) -> Optional[Document]:
		"""	Get an action representation by resource ID.
		
			Args:
				ri: The resource ID of the action representation.
			
			Return:
				The action representation, or None if not found.
		"""
		with self.lockActions:
			return self.tabActions.get(doc_id = ri)	# type:ignore[arg-type, return-value]


	def searchActionsDeprsForSubject(self, ri:str) -> Sequence[JSON]:
		"""	Search for action representations by subject.
		
			Args:
				ri: The resource ID of the action representation's subject.
			
			Return:
				A list of action representations, or None if not found.
		"""
		with self.lockActions:
			return self.tabActions.search(self.actionsQuery.subject == ri)
	

	def upsertActionRepr(self, action:ACTR, periodTS:float, count:int) -> bool:
		"""	Update or insert an action representation.
		
			Args:
				action: The action representation to update or insert.
				periodTS: The timestamp for periodic execution.
				count: The number of times the action will be executed.
			
			Return:
				True if the action representation was updated or inserted, False otherwise.
		"""
		with self.lockActions:
			_ri = action.ri
			_sri = action.sri
			return self.tabActions.upsert(Document(
					{	'ri':		_ri,
						'subject':	_sri if _sri else action.pi,
						'dep':		action.dep,
						'apy':		action.apy,
						'evm':		action.evm,
						'evc':		action.evc,	
						'ecp':		action.ecp,
						'periodTS': periodTS,
						'count':	count,
					}, _ri)) is not None


	def updateActionRepr(self, actionRepr:JSON) -> bool:
		"""	Update an action representation.
		
			Args:
				actionRepr: The action representation to update.
			
			Return:
				True if the action representation was updated, False otherwise.
		"""
		with self.lockActions:
			return self.tabActions.update(actionRepr, doc_ids = [actionRepr['ri']]) is not None	# type:ignore[arg-type]


	def removeActionRepr(self, ri:str) -> bool:
		"""	Remove an action representation.

			Args:
				ri: The action's resource ID.
			
			Return:
				True if the action representation was removed, False otherwise.
		"""
		with self.lockActions:
			if self.tabActions.get(doc_id = ri):	# type:ignore[arg-type]
				return len(self.tabActions.remove(doc_ids = [ri])) > 0	# type:ignore[arg-type, list-item]
			return False
			# return len(self.tabActions.remove(self.actionsQuery.ri == ri)) > 0


	#
	#	Requests
	#

	def insertRequest(self, op:Operation, 
							ri:str, 
							srn:str, 
							originator:str, 
							outgoing:bool, 
							ot: str,
							request:JSON, 
							response:JSON) -> bool:
		"""	Add a request to the *requests* database.
		
			Args:
				op: Operation.
				ri: Resource ID of a request's target resource.
				srn: Structured resource ID of a request's target resource.
				originator: Request originator.
				outgoing: If true, then this is a request sent by the CSE.
				ot: Request creation timestamp.
				request: The request to store.
				response: The response to store.
			
			Return:
				Boolean value to indicate success or failure.
			"""
		with self.lockRequests:
			try:
				# First check whether we reached the max number of allowed requests.
				# If yes, then remove the oldest.
				if (_a := self.tabRequests.all()):
					if len(_a) >= self.maxRequests:
						self.tabRequests.remove(doc_ids = [_a[0].doc_id])
				
				# Adding a request
				ts = utcTime()

				#op = request.get('op') if 'op' in request else Operation.NA
				rsc = response['rsc'] if 'rsc' in response else ResponseStatusCode.UNKNOWN

				# The following removes all None values from the request and response, and the requests structure
				_doc = {'ri': ri,
						 'srn': srn,
						 'ts': ts,
						 'org': originator,
						 'op': op,
						 'rsc': rsc,
						 'out': outgoing,
						 'ot': ot,
						 'req': { k: v for k, v in request.items() if v is not None }, 
						 'rsp': { k: v for k, v in response.items() if v is not None }
					   }
				self.tabRequests.insert(
					Document({k: v for k, v in _doc.items() if v is not None}, 
			    			 self.tabRequests.document_id_class(ts)))	# type:ignore[arg-type]

			except Exception as e:
				L.logErr(f'Exception inserting request/response for ri: {ri}', exc = e)
				return False
		return True
	

	def getRequests(self, ri:Optional[str] = None) -> list[Document]:
		"""	Get requests for a resource ID, or all requests.
		
			Args:
				ri: The target resource's resource ID. If *None* or empty, then all requests are returned
			
			Return:
				List of *Documents*. May be empty.
		"""
		with self.lockRequests:
			if not ri:
				return self.tabRequests.all()
			return self.tabRequests.search(self.requestsQuery.ri == ri)


	def deleteRequests(self, ri:Optional[str] = None) -> None:
		"""	Remnove all stord requests from the database.

			Args:
				ri: Optional resouce ID. Only requests for this resource ID will be deleted.
		"""
		if ri:
			with self.lockRequests:
				self.tabRequests.remove(self.requestsQuery.ri == ri)
		else:
			with self.lockRequests:
				self.tabRequests.truncate()

	#
	#	Schedules
	#

	def getSchedules(self) -> list[Document]:
		"""	Get all schedules from the database.
		
			Return:
				List of *Documents*. May be empty.
		"""
		with self.lockSchedules:
			return self.tabSchedules.all()


	def getSchedule(self, ri:str) -> Optional[Document]:
		"""	Get a schedule from the database.
		
			Args:
				ri: The resource ID of the schedule.

			Return:
				The schedule, or *None* if not found.
		"""
		with self.lockSchedules:
			return self.tabSchedules.get(doc_id = ri)	# type:ignore[arg-type, return-value]
	

	def searchSchedules(self, pi:str) -> list[Document]:
		"""	Search for schedules in the database.
		
			Args:
				pi: The resource ID of the parent resource.
			
			Return:
				List of *Documents*. May be empty.
		"""
		with self.lockSchedules:
			return self.tabSchedules.search(self.schedulesQuery.pi == pi)
	

	def upsertSchedule(self, ri:str, pi:str, schedule:list[str]) -> bool:
		"""	Add or update a schedule in the database.
		
			Args:
				ri: The resource ID of the schedule.
				pi: The resource ID of the schedule's parent resource.
				schedule: The schedule to store.
			
			Return:
				True if the schedule was added or updated, False otherwise.
		"""
		with self.lockSchedules:
			return self.tabSchedules.upsert(Document(
						{ 'ri': ri,
						  'pi': pi,
						  'sce': schedule }, 
						ri)) is not None	# type:ignore[arg-type]


	def removeSchedule(self, ri:str) -> bool:
		"""	Remove a schedule from the database.
		
			Args:
				ri: The resource ID of the schedule to remove.

			Return:
				True if the schedule was removed, False otherwise.
		"""
		with self.lockSchedules:
			return len(self.tabSchedules.remove(doc_ids = [ri])) > 0	# type:ignore[arg-type, list-item]