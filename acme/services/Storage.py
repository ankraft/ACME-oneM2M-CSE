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
"""

from __future__ import annotations
from typing import Callable, cast, List, Optional, Sequence
from enum import Enum
from datetime import datetime

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
from ..resources.Factory import resourceFromDict
from ..services.Logging import Logging as L
from ..services.StorageMongo import MongoBinding


# Constants for database and table names
_resources = 'resources'
_identifiers = 'identifiers'
_children = 'children'
_srn = 'srn'
_subscriptions = 'subscriptions'
_batchNotifications = 'batchNotifications'
_statistics = 'statistics'
_actions = 'actions'
_requests = 'requests'


class Database(Enum):
    TINYDB		= 1
    MONGODB 	= 2


class Storage(object):
	"""	This class implements the entry points to the CSE's underlying database functions.

		Attributes:
			inMemory: Indicator whether the database is located in memory (volatile) or on disk.
			dbPath: In case *inMemory* is "False" this attribute contains the path to a directory where the database is stored in disk.
			dbReset: Indicator that the database should be reset or cleared during start-up.
	"""

	__slots__ = (
		'inMemory',
		'dbPath',
		'dbReset',
		'db',
		'dbMode'
	)

	def __init__(self) -> None:
		"""	Initialization of the storage manager.
		"""

		# create data directory
		self._assignConfig()

		if self.dbMode == Database.MONGODB:
			self.db = MongoBinding()
			L.isInfo and L.log('Storage initialized')
			return
      
		if not self.inMemory:
			if self.dbPath:
				L.isInfo and L.log('Using data directory: ' + self.dbPath)
				os.makedirs(self.dbPath, exist_ok = True)
			else:
				raise RuntimeError(L.logErr('database.path not set'))

		# create DB object and open DB
		self.db = TinyDBBinding(self.dbPath, CSE.cseCsi[1:]) # add CSE CSI as postfix

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


	def isMongoDB(self) -> bool:
		return (self.dbMode == Database.MONGODB)


	def _assignConfig(self) -> None:
		"""	Assign default configurations.
		"""
		self.inMemory 		 = Configuration.get('database.inMemory')
		self.dbPath 		 = Configuration.get('database.path')
		self.dbReset 		 = Configuration.get('database.resetOnStartup') 
		self.dbMode		     = Database.MONGODB if Configuration.get('database.mongo.enable') == True else Database.TINYDB
   

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
		"""
		ri  = resource.ri
		srn = resource.getSrn()
		# L.logDebug(f'Adding resource (ty: {resource.ty}, ri: {resource.ri}, rn: {resource.rn}, srn: {srn}')
		if overwrite:
			L.isDebug and L.logDebug('Resource enforced overwrite')
			self.db.upsertResource(resource, ri)
		else: 
			if not self.hasResource(ri, srn):	# Only when resource with same ri or srn does not exist yet
				self.db.insertResource(resource, ri)
			else:
				raise CONFLICT(L.logWarn(f'Resource already exists (Skipping): {resource} ri: {ri} srn:{srn}'))

		# Add path to identifiers db
		self.db.insertIdentifier(resource, ri, srn)

		# Add record to childResources db
		self.db.addChildResource(resource, ri)


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

		if (l := len(resources)) == 1:
			return resourceFromDict(resources[0])
		elif l == 0:
			raise NOT_FOUND('resource not found')

		raise INTERNAL_SERVER_ERROR('database inconsistency')


	def retrieveResourceRaw(self, ri:str) -> JSON:
		"""	Retrieve a resource as a raw dictionary.

			Args:
				ri:  The resource is retrieved via its rersource ID.
			Returns:
				The resource dictionary.
		"""
		resources = self.db.searchResources(ri = ri)
		if (l := len(resources)) == 1:
			return resources[0]
		elif l == 0:
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
		tmp = self.db.searchResources(ty = int(ty))
		L.logDebug(f'result: {tmp}')
		return tmp


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
		"""
		# L.logDebug(f'Removing resource (ty: {resource.ty}, ri: {resource.ri}, rn: {resource.rn})')
		try:
			self.db.deleteResource(resource)
			self.db.deleteIdentifier(resource)
			self.db.removeChildResource(resource)
		except KeyError as e:
			L.isDebug and L.logDebug(f'Cannot remove: {resource.ri} (NOT_FOUND). Could be an expected error.')
			raise NOT_FOUND(dbg = str(e))


	def directChildResources(self, pi:str, 
								   ty:Optional[ResourceTypes] = None, 
								   raw:Optional[bool] = False) -> list[Document]|list[Resource]:
		"""	Return a list of direct child resources, or an empty list

			Args:
				pi: The parent resource's Resource ID.
				ty: Optional resource type to filter the result.
				raw: When "True" then return the child resources as resource dictionary instead of resources.
			Returns:
				Return a list of resources, or a list of raw resource dictionaries.
		"""
		if (_ris := self.db.searchChildResourcesByParentRI(pi, ty)):
			docs = [self.db.searchResources(ri = _ri)[0] for _ri in _ris]
			return docs if raw else cast(List[Resource], list(map(lambda x: resourceFromDict(x), docs)))
		return []	# type:ignore[return-value]
	

	def directChildResourcesRI(self, pi:str, 
			    					 ty:Optional[ResourceTypes] = None) -> list[str]:
		"""	Return a list of direct child resource IDs, or an empty list

			Args:
				pi: The parent resource's Resource ID.
				ty: Optional resource type to filter the result.
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
  
	def retrieveLatestOldestResource(self, oldest: bool, ty: int, pi: Optional[str]) -> Optional[Resource]:
		""" Retrieve latest or oldest resource

		Args:
			oldest (bool): True if want to find oldest, False otherwise
			ty (int): Resource type to retrieve
			pi (Optional[str]): Find specific resource that has pi as parents

		Returns:
			Optional[Resource]: Resource or None
		"""
		if (resource := self.db.retrieveLatestOldestResource(oldest, ty, pi)):
			return resourceFromDict(resource)
		return None


	def retrieveResourcesByContain(self, 
                                field: str, 
                                contain: Optional[str] = None,
                                startswith: Optional[str] = None,
                                endswith: Optional[str] = None,
                                filter:Optional[Callable[[JSON], bool]] = None) -> list[Resource]:
		""" Retrieve resources by checking value exist in array field

		Args:
			field (str): Target field to find
			contain (str): Value to find in an array

		Returns:
			list[Resource]: List of found resources
		"""
  
		temporaryResult = self.db.retrieveResourcesByContain(field, contain, startswith, endswith)
		result = []

		# Do filter function callback
		if filter:
			for res in temporaryResult:
				if filter(res):
					result.append(res)
		else:
			result = temporaryResult
  
		return  [ res for each in result
					if (res := resourceFromDict(each))
				]
  
	
	def retrieveResourcesByLessDate(self, field: str, dt: datetime) -> list[Resource]:
		""" Retrieve resource by searching date field that less than provided datetime

		Args:
			field (str): Target field of date value that will search
            dt (datetime): Filter value in python datetime object

		Returns:
			list[Resource]: List of Resource data that match filter
		"""
		return [ res	for each in self.db.retrieveResourcesByLessDate(field, dt)
						if (res := resourceFromDict(each))
				]


	#########################################################################
	##
	##	Subscriptions
	##

	def getSubscription(self, ri:str) -> Optional[Document]:
		# L.logDebug(f'Retrieving subscription: {ri}')
		subs = self.db.searchSubscriptions(ri = ri)
		if not subs or len(subs) != 1:
			return None
		return subs[0]


	def getSubscriptionsForParent(self, pi:str) -> list[Document]:
		# L.logDebug(f'Retrieving subscriptions for parent: {pi}')
		return self.db.searchSubscriptions(pi = pi)


	def addSubscription(self, subscription:Resource) -> bool:
		# L.logDebug(f'Adding subscription: {ri}')
		return self.db.upsertSubscription(subscription)


	def removeSubscription(self, subscription:Resource) -> bool:
		# L.logDebug(f'Removing subscription: {subscription.ri}')
		return self.db.removeSubscription(subscription)


	def updateSubscription(self, subscription:Resource) -> bool:
		# L.logDebug(f'Updating subscription: {ri}')
		return self.db.upsertSubscription(subscription)


	#########################################################################
	##
	##	BatchNotifications
	##

	def addBatchNotification(self, ri:str, nu:str, request:JSON) -> bool:
		return self.db.addBatchNotification(ri, nu, request)


	def countBatchNotifications(self, ri:str, nu:str) -> int:
		return self.db.countBatchNotifications(ri, nu)


	def getBatchNotifications(self, ri:str, nu:str) -> list[Document]:
		return self.db.getBatchNotifications(ri, nu)


	def removeBatchNotifications(self, ri:str, nu:str) -> bool:
		return self.db.removeBatchNotifications(ri, nu)



	#########################################################################
	##
	##	Statistics
	##

	def getStatistics(self) -> JSON:
		"""	Retrieve the statistics data from the DB.
		"""
		return self.db.searchStatistics()


	def updateStatistics(self, stats:JSON) -> bool:
		"""	Update the statistics DB with new data.
		"""
		return self.db.upsertStatistics(stats)


	def purgeStatistics(self) -> None:
		"""	Purge the statistics DB.
		"""
		self.db.purgeStatistics()



	#########################################################################
	##
	##	Actions
	##

	def getActions(self) -> list[Document]:
		"""	Retrieve the actions data from the DB.
		"""
		return self.db.searchActionReprs()
	

	def getAction(self, ri:str) -> Optional[Document]:
		"""	Retrieve the actions data from the DB.
		"""
		return self.db.getAction(ri)

	
	def searchActionsForSubject(self, ri:str) -> Sequence[JSON]:
		return self.db.searchActionsDeprsForSubject(ri)


	def updateAction(self, action:ACTR, period:float, count:int) -> bool:
		return self.db.upsertActionRepr(action, period, count)


	def updateActionRepr(self, actionRepr:JSON) -> bool:
		return self.db.updateActionRepr(actionRepr)


	def removeAction(self, ri:str) -> bool:
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
#
#	DB class that implements the TinyDB binding
#
#	This class may be moved later to an own module.


class TinyDBBinding(object):

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

		'fileResources',
		'fileIdentifiers',
		'fileSubscriptions',
		'fileBatchNotifications',
		'fileStatistics',
		'fileActions',
		'fileRequests',
		
		'dbResources',
		'dbIdentifiers', 		
		'dbSubscriptions', 	
		'dbBatchNotifications',
		'dbStatistics',
		'dbActions',	
		'dbRequests',	

		'tabResources',
		'tabIdentifiers',
		'tabChildResources',
		'tabStructuredIDs',
		'tabSubscriptions',
		'tabBatchNotifications',
		'tabStatistics',
		'tabActions',
		'tabRequests',

		'resourceQuery',
		'identifierQuery',
		'subscriptionQuery',
		'batchNotificationQuery',
		'actionsQuery',
		'requestsQuery',
	)

	def __init__(self, path:str, postfix:str) -> None:
		self.path = path
		self._assignConfig()
		L.isInfo and L.log(f'Cache Size: {self.cacheSize:d}')

		# create transaction locks
		self.lockResources				= Lock()
		self.lockIdentifiers			= Lock()
		self.lockChildResources			= Lock()
		self.lockStructuredIDs			= Lock()
		self.lockSubscriptions			= Lock()
		self.lockBatchNotifications		= Lock()
		self.lockStatistics 			= Lock()
		self.lockActions 				= Lock()
		self.lockRequests 				= Lock()

		# file names
		self.fileResources				= f'{self.path}/{_resources}-{postfix}.json'
		self.fileIdentifiers			= f'{self.path}/{_identifiers}-{postfix}.json'
		self.fileSubscriptions			= f'{self.path}/{_subscriptions}-{postfix}.json'
		self.fileBatchNotifications		= f'{self.path}/{_batchNotifications}-{postfix}.json'
		self.fileStatistics				= f'{self.path}/{_statistics}-{postfix}.json'
		self.fileActions				= f'{self.path}/{_actions}-{postfix}.json'
		self.fileRequests				= f'{self.path}/{_requests}-{postfix}.json'

		# All databases/tables will use the smart query cache
		if Configuration.get('database.inMemory'):
			L.isInfo and L.log('DB in memory')
			self.dbResources 			= TinyDB(storage = MemoryStorage)
			self.dbIdentifiers 			= TinyDB(storage = MemoryStorage)
			self.dbSubscriptions 		= TinyDB(storage = MemoryStorage)
			self.dbBatchNotifications	= TinyDB(storage = MemoryStorage)
			self.dbStatistics			= TinyDB(storage = MemoryStorage)
			self.dbActions				= TinyDB(storage = MemoryStorage)
			self.dbRequests				= TinyDB(storage = MemoryStorage)
		else:
			L.isInfo and L.log('DB in file system')
			# self.dbResources 			= TinyDB(self.fileResources)
			# self.dbIdentifiers 			= TinyDB(self.fileIdentifiers)
			# self.dbSubscriptions 		= TinyDB(self.fileSubscriptions)
			# self.dbBatchNotifications 	= TinyDB(self.fileBatchNotifications)
			# self.dbStatistics 			= TinyDB(self.fileStatistics)
			# self.dbActions	 			= TinyDB(self.fileActions)

			# EXPERIMENTAL Using TinyDBBufferedStorage - Buffers read and writes to disk
			self.dbResources 			= TinyDB(self.fileResources, storage = TinyDBBufferedStorage, write_delay = self.writeDelay)
			self.dbIdentifiers 			= TinyDB(self.fileIdentifiers, storage = TinyDBBufferedStorage, write_delay = self.writeDelay)
			self.dbSubscriptions 		= TinyDB(self.fileSubscriptions, storage = TinyDBBufferedStorage, write_delay = self.writeDelay)
			self.dbBatchNotifications 	= TinyDB(self.fileBatchNotifications, storage = TinyDBBufferedStorage, write_delay = self.writeDelay)
			self.dbStatistics 			= TinyDB(self.fileStatistics, storage = TinyDBBufferedStorage, write_delay = self.writeDelay)
			self.dbActions	 			= TinyDB(self.fileActions, storage = TinyDBBufferedStorage, write_delay = self.writeDelay)
			self.dbRequests	 			= TinyDB(self.fileRequests, storage = TinyDBBufferedStorage, write_delay = self.writeDelay)

		
		# Open/Create tables
		self.tabResources = self.dbResources.table(_resources, cache_size = self.cacheSize)
		TinyDBBetterTable.assign(self.tabResources)
		
		self.tabIdentifiers = self.dbIdentifiers.table(_identifiers, cache_size = self.cacheSize)
		TinyDBBetterTable.assign(self.tabIdentifiers)

		self.tabChildResources = self.dbIdentifiers.table(_children, cache_size = self.cacheSize)
		TinyDBBetterTable.assign(self.tabChildResources)

		self.tabStructuredIDs = self.dbIdentifiers.table('srn', cache_size = self.cacheSize)
		TinyDBBetterTable.assign(self.tabStructuredIDs)
		
		self.tabSubscriptions = self.dbSubscriptions.table(_subscriptions, cache_size = self.cacheSize)
		TinyDBBetterTable.assign(self.tabSubscriptions)
		
		self.tabBatchNotifications = self.dbBatchNotifications.table(_batchNotifications, cache_size = self.cacheSize)
		TinyDBBetterTable.assign(self.tabBatchNotifications)
		
		self.tabStatistics = self.dbStatistics.table(_statistics, cache_size = self.cacheSize)
		TinyDBBetterTable.assign(self.tabStatistics)

		self.tabActions = self.dbActions.table(_actions, cache_size = self.cacheSize)
		TinyDBBetterTable.assign(self.tabActions)

		self.tabRequests = self.dbRequests.table(_requests, cache_size = self.cacheSize)
		TinyDBBetterTable.assign(self.tabRequests)


		# Create the Queries
		self.resourceQuery 				= Query()
		self.identifierQuery 			= Query()
		self.subscriptionQuery			= Query()
		self.batchNotificationQuery 	= Query()
		self.actionsQuery				= Query()
		self.requestsQuery				= Query()


	def _assignConfig(self) -> None:
		"""	Assign default configurations.
		"""
		self.cacheSize = Configuration.get('database.cacheSize')
		self.writeDelay = Configuration.get('database.writeDelay')
		self.maxRequests = Configuration.get('cse.operation.requests.size')


	def closeDB(self) -> None:
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


	def purgeDB(self) -> None:
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
	

	def backupDB(self, dir:str) -> bool:
		for fn in [	self.fileResources,
					self.fileIdentifiers,
					self.fileSubscriptions,
					self.fileBatchNotifications,
					self.fileStatistics,
					self.fileActions,
					self.fileRequests]:
			if Path(fn).is_file():
				shutil.copy2(fn, dir)
		return True


	#
	#	Resources
	#


	def insertResource(self, resource: Resource, ri:str) -> None:
		with self.lockResources:
			self.tabResources.insert(Document(resource.dict, ri))	# type:ignore[arg-type]
			# self.tabResources.insert(resource.dict)
	

	def upsertResource(self, resource: Resource, ri:str) -> None:
		#L.logDebug(resource)
		with self.lockResources:
			# Update existing or insert new when overwriting
			# _ri = resource.ri
			# self.tabResources.upsert(resource.dict, self.resourceQuery.ri == _ri)

			self.tabResources.upsert(Document(resource.dict, doc_id = ri))	# type:ignore[arg-type]
	

	def updateResource(self, resource: Resource, ri:str) -> Resource:
		#L.logDebug(resource)
		with self.lockResources:
			self.tabResources.update(resource.dict, doc_ids = [ri])	# type:ignore[call-arg, list-item]
			# self.tabResources.update(resource.dict, self.resourceQuery.ri == _ri)
			# remove nullified fields from db and resource
			for k in list(resource.dict):
				if resource.dict[k] is None:	# only remove the real None attributes, not those with 0
					self.tabResources.update(delete(k), doc_ids = [ri])	# type: ignore[no-untyped-call, call-arg, list-item]
					# self.tabResources.update(delete(k), self.resourceQuery.ri == ri)	# type: ignore [no-untyped-call]
					del resource.dict[k]
			return resource


	def deleteResource(self, resource:Resource) -> None:
		with self.lockResources:
			_ri = resource.ri
			self.tabResources.remove(doc_ids = [_ri])	
			# self.tabResources.remove(self.resourceQuery.ri == _ri)	
	

	def searchResources(self, ri:Optional[str] = None, 
							  csi:Optional[str] = None, 
							  srn:Optional[str] = None, 
							  pi:Optional[str] = None, 
							  ty:Optional[int] = None, 
							  aei:Optional[str] = None) -> list[Document]:
		if not srn:
			with self.lockResources:
				if ri:
					_r = self.tabResources.get(doc_id = ri)	# type:ignore[arg-type]
					return [_r] if _r else []
					# return self.tabResources.search(self.resourceQuery.ri == ri)
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
		with self.lockResources:
			return self.tabResources.search(func)	# type: ignore [arg-type]


	def hasResource(self, ri:Optional[str] = None, 
						  csi:Optional[str] = None, 
						  srn:Optional[str] = None,
						  ty:Optional[int] = None) -> bool:
		if not srn:
			with self.lockResources:
				if ri:
					return self.tabResources.contains(doc_id = ri)	# type:ignore[arg-type]
					# return self.tabResources.contains(self.resourceQuery.ri == ri)	
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
		with self.lockResources:
			return len(self.tabResources)


	def searchByFragment(self, dct:dict) -> list[Document]:
		""" Search and return all resources that match the given dictionary/document. """
		with self.lockResources:
			return self.tabResources.search(self.resourceQuery.fragment(dct))

	#
	#	Identifiers, Structured RI, Child Resources
	#

	def insertIdentifier(self, resource:Resource, ri:str, srn:str) -> None:
		# L.isDebug and L.logDebug({'ri' : ri, 'rn' : resource.rn, 'srn' : srn, 'ty' : resource.ty})		
		with self.lockIdentifiers:
			self.tabIdentifiers.upsert(Document(
				{	'ri' : ri, 
					'rn' : resource.rn, 
					'srn' : srn,
					'ty' : resource.ty 
				}, ri))	# type:ignore[arg-type]

			# self.tabIdentifiers.upsert(
			# 	{	'ri' : ri, 
			# 		'rn' : resource.rn, 
			# 		'srn' : srn,
			# 		'ty' : resource.ty 
			# 	}, 
			# 	self.identifierQuery.ri == ri)

		with self.lockStructuredIDs:
			self.tabStructuredIDs.upsert(
				Document({'srn': srn,
				  		  'ri' : ri 
						 }, srn))	# type:ignore[arg-type]


	def deleteIdentifier(self, resource:Resource) -> None:
		with self.lockIdentifiers:
			self.tabIdentifiers.remove(doc_ids = [resource.ri])
			# self.tabIdentifiers.remove(self.identifierQuery.ri == resource.ri)

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
				A list of found identifier documents (see `insertIdentifier`), or an empty list if not found.
		 """
		if srn:
			if (_r := self.tabStructuredIDs.get(doc_id = srn)):	# type:ignore[arg-type]
				ri = _r['ri'] if _r else None
			else:
				return []
			# return self.tabIdentifiers.search(self.identifierQuery.srn == srn)

		if ri:
			with self.lockIdentifiers:
				_r = self.tabIdentifiers.get(doc_id = ri)	# type:ignore[arg-type]
				return [_r] if _r else []
				# return self.tabIdentifiers.search(self.identifierQuery.ri == ri)
		return []


	def addChildResource(self, resource:Resource, ri:str) -> None:
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
				_r = self.tabChildResources.get(doc_id = pi) # type:ignore[arg-type]
				_ch = _r['ch']
				if ri not in _ch:
					_ch.append( [ri, ty] )
					_r['ch'] = _ch
					self.tabChildResources.update(_r, doc_ids = [pi])# type:ignore[arg-type, list-item]

			
	def removeChildResource(self, resource:Resource) -> None:
		ri = resource.ri
		pi = resource.pi

		# L.isDebug and L.logDebug(f'removeChildResource ri:{ri} pi:{pi}')		
		with self.lockChildResources:

			# First remove the record
			self.tabChildResources.remove(doc_ids = [ri])	# type:ignore[arg-type, list-item]

			# Remove (ri, ty) tuple from parent record
			_r = self.tabChildResources.get(doc_id = pi) # type:ignore[arg-type]
			_t = [ri, resource.ty]
			_ch = _r['ch']
			if _t in _ch:
				_ch.remove(_t)
				_r['ch'] = _ch
				# L.isDebug and L.logDebug(f'removeChildResource _r:{_r}')		
				self.tabChildResources.update(_r, doc_ids = [pi])	# type:ignore[arg-type, list-item]


	def searchChildResourcesByParentRI(self, pi:str, ty:Optional[int] = None) -> Optional[list[str]]:
		_r = self.tabChildResources.get(doc_id = pi) #type:ignore[arg-type]
		if _r:
			if ty is None:	# optimization: only check ty once for None
				return [ c[0] for c in _r['ch'] ]
			return [ c[0] for c in _r['ch'] if ty == c[1] ]	# c is a tuple (ri, ty)
		return []

	#
	#	Subscriptions
	#


	def searchSubscriptions(self, ri:Optional[str] = None, 
								  pi:Optional[str] = None) -> Optional[list[Document]]:
		with self.lockSubscriptions:
			if ri:
				_r = self.tabSubscriptions.get(doc_id =  ri)	# type:ignore[arg-type]
				return [_r] if _r else []
				# return self.tabSubscriptions.search(self.subscriptionQuery.ri == ri)
			if pi:
				return self.tabSubscriptions.search(self.subscriptionQuery.pi == pi)
			return None


	def upsertSubscription(self, subscription:Resource) -> bool:
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
						  'org'		: subscription.getOriginator(),
						  'ma' 		: fromDuration(subscription.ma) if subscription.ma else None, # EXPERIMENTAL ma = maxAge
						  'nse' 	: subscription.nse
						 }, ri)) is not None
					# self.subscriptionQuery.ri == ri) is not None


	def removeSubscription(self, subscription:Resource) -> bool:
		with self.lockSubscriptions:
			return len(self.tabSubscriptions.remove(doc_ids = [subscription.ri])) > 0
			# return len(self.tabSubscriptions.remove(self.subscriptionQuery.ri == _ri)) > 0


	#
	#	BatchNotifications
	#

	def addBatchNotification(self, ri:str, nu:str, notificationRequest:JSON) -> bool:
		with self.lockBatchNotifications:
			return self.tabBatchNotifications.insert( 
					{	'ri' 		: ri,
						'nu' 		: nu,
						'tstamp'	: utcTime(),
						'request'	: notificationRequest
					}) is not None


	def countBatchNotifications(self, ri:str, nu:str) -> int:
		with self.lockBatchNotifications:
			return self.tabBatchNotifications.count((self.batchNotificationQuery.ri == ri) & (self.batchNotificationQuery.nu == nu))


	def getBatchNotifications(self, ri:str, nu:str) -> list[Document]:
		with self.lockBatchNotifications:
			return self.tabBatchNotifications.search((self.batchNotificationQuery.ri == ri) & (self.batchNotificationQuery.nu == nu))


	def removeBatchNotifications(self, ri:str, nu:str) -> bool:
		with self.lockBatchNotifications:
			return len(self.tabBatchNotifications.remove((self.batchNotificationQuery.ri == ri) & (self.batchNotificationQuery.nu == nu))) > 0


	#
	#	Statistics
	#

	def searchStatistics(self) -> JSON:
		with self.lockStatistics:
			stats = self.tabStatistics.all()
			# stats = self.tabStatistics.get(doc_id = 1)
			# return stats if stats is not None and len(stats) > 0 else None
			return stats[0] if stats else None


	def upsertStatistics(self, stats:JSON) -> bool:
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
		with self.lockActions:
			actions = self.tabActions.all()
			return actions if actions else None
	

	def getAction(self, ri:str) -> Optional[Document]:
		with self.lockActions:
			return self.tabActions.get(doc_id = ri)	# type:ignore[arg-type]


	def searchActionsDeprsForSubject(self, ri:str) -> Sequence[JSON]:
		with self.lockActions:
			return self.tabActions.search(self.actionsQuery.subject == ri)
	

	# TODO add only?
	def upsertActionRepr(self, action:ACTR, periodTS:float, count:int) -> bool:
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
		with self.lockActions:
			return self.tabActions.update(actionRepr, doc_ids = [actionRepr['ri']]) is not None	# type:ignore[arg-type]


	def removeActionRepr(self, ri:str) -> bool:
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

				# self.tabRequests.insert(
					# Document({'ri': ri,
					# 		  'srn': srn,
					# 		  'ts': ts,
					# 		  'org': originator,
					# 		  'op': op,
					# 		  'rsc': rsc,
					# 		  'out': outgoing,
					# 		  'req': request,
					# 		  'rsp': response
					# 		 }, self.tabRequests.document_id_class(ts)))	# type:ignore[arg-type]
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