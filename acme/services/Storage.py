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

from __future__ import annotations

import os, shutil
from threading import Lock
from typing import Callable, cast, List
from tinydb import TinyDB, Query
from tinydb.storages import MemoryStorage
from tinydb.table import Document
from tinydb.operations import delete 

from ..etc.Types import ResourceTypes as T, Result, ResponseStatusCode as RC, JSON
from ..etc import DateUtils as DateUtils
from ..services.Configuration import Configuration
from ..services.Logging import Logging as L
from ..services import CSE as CSE
from ..resources.Resource import Resource
from ..resources import Factory


class Storage(object):

	def __init__(self) -> None:

		# create data directory
		self.inMemory 	= Configuration.get('db.inMemory')
		self.dbPath 	= Configuration.get('db.path')
		self.dbReset 	= Configuration.get('db.resetOnStartup') 

		if not self.inMemory:
			if self.dbPath:
				L.isInfo and L.log('Using data directory: ' + self.dbPath)
				os.makedirs(self.dbPath, exist_ok=True)
			else:
				L.logErr('db.path not set')
				raise RuntimeError('db.path not set')

		# create DB object and open DB
		self.db = TinyDBBinding(self.dbPath, postfix = f'-{CSE.cseCsi[1:]}') # add CSE CSI as postfix

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
		self.db.closeDB()
		self.db = None
		L.isInfo and L.log('Storage shut down')
		return True


	def purge(self) -> None:
		"""	Empty the databases.
		"""
		try:
			self.db.purgeDB()
		except Exception as e:
			L.logErr(f'Exception during purge: {e}', exc=e)
			quit()


	def _validateDB(self) -> bool:
		"""	Trying to validate the database files by reading from them.
		"""
		L.isDebug and L.logDebug('Validating database files')
		dbFile = ''
		try:
			dbFile = 'resources'
			self.hasResource('_')
			dbFile = 'identifiers'
			self.structuredIdentifier('_')
			dbFile = 'subscription'
			self.getSubscription('_')
			dbFile = 'batch notification'
			self.countBatchNotifications('_', '_')
			dbFile = 'statistics'
			self.getStatistics()
		except Exception as e:
			L.logErr(f'Error validating data files. Error in {dbFile} database.', exc = e)
			return False
		return True
	

	def _backupDB(self) -> bool:
		"""	Creating a backup from the DB to a sub directory.
		"""
		dir = f'{self.dbPath}/backup'
		L.isDebug and L.logDebug(f'Creating DB backup in directory: {dir}')
		os.makedirs(dir, exist_ok = True)
		return self.db.backupDB(dir)
		

	#########################################################################
	##
	##	Resources
	##


	def createResource(self, resource:Resource, overwrite:bool = True) -> Result:
		ri  = resource.ri
		srn = resource.__srn__
		# L.logDebug(f'Adding resource (ty: {resource.ty}, ri: {resource.ri}, rn: {resource.rn}, srn: {srn}')
		if overwrite:
			L.isDebug and L.logDebug('Resource enforced overwrite')
			self.db.upsertResource(resource)
		else: 
			if not self.hasResource(ri, srn):	# Only when not resource does not exist yet
				self.db.insertResource(resource)
			else:
				L.isWarn and L.logWarn(f'Resource already exists (Skipping): {resource} ri: {ri} srn:{srn}')
				return Result.errorResult(rsc = RC.conflict, dbg = 'resource already exists')

		# Add path to identifiers db
		self.db.insertIdentifier(resource, ri, srn)
		return Result(status = True, rsc = RC.created)


	def hasResource(self, ri:str = None, srn:str = None) -> bool:
		"""	Check whether a resource with either the ri or the srn already exists.
		"""
		return (ri is not None and self.db.hasResource(ri = ri)) or (srn is not None and self.db.hasResource(srn = srn))


	def retrieveResource(self, ri:str = None, csi:str = None, srn:str = None, aei:str = None, raw:bool = False) -> Result:
		""" Return a resource via different addressing methods. 
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

		# L.logDebug(resources)
		# return CSE.dispatcher.resourceFromDict(resources[0]) if len(resources) == 1 else None,
		if (l := len(resources)) == 1:
			return Result(status = True, resource = resources[0]) if raw else Factory.resourceFromDict(resources[0])
		elif l == 0:
			return Result.errorResult(rsc = RC.notFound, dbg = 'resource not found')

		return Result.errorResult(rsc = RC.internalServerError, dbg = 'database inconsistency')


	def retrieveResourcesByType(self, ty:T) -> list[Document]:
		""" Return all resources of a certain type. 
		"""
		# L.logDebug(f'Retrieving all resources ty: {ty}')
		return self.db.searchResources(ty = int(ty))


	def updateResource(self, resource:Resource) -> Result:
		# ri = resource.ri
		# L.logDebug(f'Updating resource (ty: {resource.ty}, ri: {ri}, rn: {resource.rn})')
		return Result(status = True, resource = self.db.updateResource(resource), rsc = RC.updated)


	def deleteResource(self, resource:Resource) -> Result:
		# L.logDebug(f'Removing resource (ty: {resource.ty}, ri: {ri}, rn: {resource.rn})'
		self.db.deleteResource(resource)
		self.db.deleteIdentifier(resource)
		return Result(status = True, rsc = RC.deleted)


	def directChildResources(self, pi:str, ty:T = None, raw:bool = False) -> list[Document]|list[Resource]:
		"""	Return a list of direct child resources, or an empty list
		"""
		docs = [ each for each in self.db.searchResources(pi = pi, ty = int(ty) if ty is not None else None)]
		return docs if raw else cast(List[Resource], list(map(lambda x: Factory.resourceFromDict(x).resource, docs)))
		
		# return 	[ res	for each in self.db.searchResources(pi = pi, ty = int(ty) if ty is not None else None)
		# 				if (res := Factory.resourceFromDict(each).resource)
		# 		]


	def countDirectChildResources(self, pi:str, ty:T = None) -> int:
		"""	Count the direct child resources.
		"""
		return len(self.db.searchResources(pi = pi, ty = int(ty) if ty is not None else None))


	def countResources(self) -> int:
		return self.db.countResources()


	def identifier(self, ri:str) -> list[Document]:
		"""	Search for the resource with the given resource ID,

			Args:
				ri: Resource ID for the resource to look for
			Return:
				List of found resources, or an empty list
		"""
		return self.db.searchIdentifiers(ri = ri)


	def structuredIdentifier(self, srn:str) -> list[Document]:
		return self.db.searchIdentifiers(srn = srn)


	def searchByFragment(self, dct:dict, filter:Callable[[JSON], bool] = None) -> list[Resource]:
		""" Search and return all resources that match the given fragment dictionary/document.
		"""
		return	[ res	for each in self.db.searchByFragment(dct) 
						if (not filter or filter(each)) and (res := Factory.resourceFromDict(each).resource) # either there is no filter or the filter is called to test the resource
				] 


	def searchByFilter(self, filter:Callable[[JSON], bool]) -> list[Resource]:
		"""	Return a list of resouces that match the given filter, or an empty list.
		"""
		return	[ res	for each in self.db.discoverResourcesByFilter(filter)
						if (res := Factory.resourceFromDict(each).resource)
				]


	#########################################################################
	##
	##	Subscriptions
	##

	def getSubscription(self, ri:str) -> JSON:
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
#
#	DB class that implements the TinyDB binding
#
#	This class may be moved later to an own module.


class TinyDBBinding(object):

	def __init__(self, path:str = None, postfix:str = '') -> None:
		self.path = path
		self.cacheSize = Configuration.get('db.cacheSize')
		L.isInfo and L.log(f'Cache Size: {self.cacheSize:d}')

		# create transaction locks
		self.lockResources				= Lock()
		self.lockIdentifiers			= Lock()
		self.lockSubscriptions			= Lock()
		self.lockBatchNotifications		= Lock()
		self.lockStatistics 			= Lock()

		# file names
		self.fileResources				= f'{self.path}/resources{postfix}.json'
		self.fileIdentifiers			= f'{self.path}/identifiers{postfix}.json'
		self.fileSubscriptions			= f'{self.path}/subscriptions{postfix}.json'
		self.fileBatchNotifications		= f'{self.path}/batchNotifications{postfix}.json'
		self.fileStatistics				= f'{self.path}/statistics{postfix}.json'

		# All databases/tables will use the smart query cache
		if Configuration.get('db.inMemory'):
			L.isInfo and L.log('DB in memory')
			self.dbResources 			= TinyDB(storage = MemoryStorage)
			self.dbIdentifiers 			= TinyDB(storage = MemoryStorage)
			self.dbSubscriptions 		= TinyDB(storage = MemoryStorage)
			self.dbBatchNotifications	= TinyDB(storage = MemoryStorage)
			self.dbStatistics			= TinyDB(storage = MemoryStorage)
		else:
			L.isInfo and L.log('DB in file system')
			self.dbResources 			= TinyDB(self.fileResources)
			self.dbIdentifiers 			= TinyDB(self.fileIdentifiers)
			self.dbSubscriptions 		= TinyDB(self.fileSubscriptions)
			self.dbBatchNotifications 	= TinyDB(self.fileBatchNotifications)
			self.dbStatistics 			= TinyDB(self.fileStatistics)
		
		# Open/Create tables
		self.tabResources 				= self.dbResources.table('resources', cache_size = self.cacheSize)
		self.tabIdentifiers 			= self.dbIdentifiers.table('identifiers', cache_size = self.cacheSize)
		self.tabSubscriptions 			= self.dbSubscriptions.table('subsriptions', cache_size = self.cacheSize)
		self.tabBatchNotifications 		= self.dbBatchNotifications.table('batchNotifications', cache_size = self.cacheSize)
		self.tabStatistics 				= self.dbStatistics.table('statistics', cache_size = self.cacheSize)

		# Create the Queries
		self.resourceQuery 				= Query()
		self.identifierQuery 			= Query()
		self.subscriptionQuery			= Query()
		self.batchNotificationQuery 	= Query()


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


	def purgeDB(self) -> None:
		L.isInfo and L.log('Purging DBs')
		self.tabResources.truncate()
		self.tabIdentifiers.truncate()
		self.tabSubscriptions.truncate()
		self.tabBatchNotifications.truncate()
		self.tabStatistics.truncate()
	

	def backupDB(self, dir:str) -> bool:
		shutil.copy2(self.fileResources, dir)
		shutil.copy2(self.fileIdentifiers, dir)
		shutil.copy2(self.fileSubscriptions, dir)
		shutil.copy2(self.fileBatchNotifications, dir)
		shutil.copy2(self.fileStatistics, dir)
		return True


	#
	#	Resources
	#


	def insertResource(self, resource: Resource) -> None:
		with self.lockResources:
			self.tabResources.insert(resource.dict)
	

	def upsertResource(self, resource: Resource) -> None:
		#L.logDebug(resource)
		with self.lockResources:
			# Update existing or insert new when overwriting
			self.tabResources.upsert(resource.dict, self.resourceQuery.ri == resource.ri)
	

	def updateResource(self, resource: Resource) -> Resource:
		#L.logDebug(resource)
		with self.lockResources:
			ri = resource.ri
			self.tabResources.update(resource.dict, self.resourceQuery.ri == ri)
			# remove nullified fields from db and resource
			for k in list(resource.dict):
				if resource.dict[k] is None:	# only remove the real None attributes, not those with 0
					self.tabResources.update(delete(k), self.resourceQuery.ri == ri)	# type: ignore [no-untyped-call]
					del resource.dict[k]
			return resource


	def deleteResource(self, resource: Resource) -> None:
		with self.lockResources:
			self.tabResources.remove(self.resourceQuery.ri == resource.ri)	
	

	def searchResources(self, ri:str = None, csi:str = None, srn:str = None, pi:str = None, ty:int = None, aei:str = None) -> list[Document]:
		if not srn:
			with self.lockResources:
				if ri:
					return self.tabResources.search(self.resourceQuery.ri == ri)
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
			if len((identifiers := self.searchIdentifiers(srn=srn))) == 1:
				return self.searchResources(ri=identifiers[0]['ri'])

		return []


	def discoverResourcesByFilter(self, func:Callable[[JSON], bool]) -> list[Document]:
		with self.lockResources:
			return self.tabResources.search(func)	# type: ignore [arg-type]


	def hasResource(self, ri: str = None, csi: str = None, srn: str = None, ty: int = None) -> bool:
		if not srn:
			with self.lockResources:
				if ri:
					return self.tabResources.contains(self.resourceQuery.ri == ri)	
				elif csi :
					return self.tabResources.contains(self.resourceQuery.csi == csi)
				elif ty is not None:	# ty is an int
					return self.tabResources.contains(self.resourceQuery.ty == ty)
		else:
			# find the ri first and then try again recursively
			if len((identifiers := self.searchIdentifiers(srn=srn))) == 1:
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
	#	Identifiers
	#


	def insertIdentifier(self, resource:Resource, ri:str, srn:str) -> None:
		# L.isDebug and L.logDebug({'ri' : ri, 'rn' : resource.rn, 'srn' : srn, 'ty' : resource.ty})		
		with self.lockIdentifiers:
			self.tabIdentifiers.upsert(
				{	'ri' : ri, 
					'rn' : resource.rn, 
					'srn' : srn,
					'ty' : resource.ty 
				}, 
				self.identifierQuery.ri == ri)


	def deleteIdentifier(self, resource:Resource) -> None:
		with self.lockIdentifiers:
			self.tabIdentifiers.remove(self.identifierQuery.ri == resource.ri)


	def searchIdentifiers(self, ri:str = None, srn:str = None) -> list[Document]:
		"""	Search for an resource ID OR for a structured name in the identifiers DB.

			Either *ri* or *srn* shall be given. If both are given then *srn*
			is taken.
		
			Args:
				ri: Resource ID to search for.
				srn: Structured path to search for.
			Return:
				A list of found identifier documents (see `insertIdentifier`), or an empty list if not found.
		 """
		with self.lockIdentifiers:
			if srn:
				return self.tabIdentifiers.search(self.identifierQuery.srn == srn)
			elif ri:
				return self.tabIdentifiers.search(self.identifierQuery.ri == ri)
			return []


	#
	#	Subscriptions
	#


	def searchSubscriptions(self, ri:str=None, pi:str=None) -> list[Document]:
		with self.lockSubscriptions:
			if ri:
				return self.tabSubscriptions.search(self.subscriptionQuery.ri == ri)
			if pi:
				return self.tabSubscriptions.search(self.subscriptionQuery.pi == pi)
			return None


	def upsertSubscription(self, subscription:Resource) -> bool:
		with self.lockSubscriptions:
			ri = subscription.ri
			return self.tabSubscriptions.upsert(
					{	'ri'  : ri, 
						'pi'  : subscription.pi,
						'nct' : subscription.nct,
						'net' : subscription['enc/net'],	# TODO perhaps store enc as a whole?
						'atr' : subscription['enc/atr'],
						'chty': subscription['enc/chty'],
						'exc' : subscription.exc,
						'ln'  : subscription.ln,
						'nus' : subscription.nu,
						'bn'  : subscription.bn,
						'cr'  : subscription.cr,
						'ma'  : subscription.ma, # EXPERIMENTAL ma = maxAge
					}, 
					self.subscriptionQuery.ri == ri) is not None


	def removeSubscription(self, subscription:Resource) -> bool:
		with self.lockSubscriptions:
			return len(self.tabSubscriptions.remove(self.subscriptionQuery.ri == subscription.ri)) > 0


	#
	#	BatchNotifications
	#

	def addBatchNotification(self, ri:str, nu:str, notificationRequest:JSON) -> bool:
		with self.lockBatchNotifications:
			return self.tabBatchNotifications.insert(
					{	'ri' 		: ri,
						'nu' 		: nu,
						'tstamp'	: DateUtils.utcTime(),
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
			stats = self.tabStatistics.get(doc_id = 1)
			# return stats if stats is not None and len(stats) > 0 else None
			return stats if stats else None


	def upsertStatistics(self, stats:JSON) -> bool:
		with self.lockStatistics:
			if len(self.tabStatistics) > 0:
				return self.tabStatistics.update(stats, doc_ids = [1]) is not None
			else:
				return self.tabStatistics.insert(stats) is not None


	def purgeStatistics(self) -> None:
		"""	Purge the statistics DB.
		"""
		with self.lockStatistics:
			self.tabStatistics.truncate()

