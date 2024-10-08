#
#	TinyDBBinding.py
#
#	(c) 2024 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Database Binding for TinyDB.
#
"""	This module implements the TinyDB binding to the database. It is used by the Storage class.
"""

from __future__ import annotations
from typing import Optional, Callable, Sequence, cast

import shutil, os
from threading import Lock
from pathlib import Path

from .DBBinding import DBBinding
from ..etc.Types import JSON, ResourceTypes

from ..runtime.Logging import Logging as L

from tinydb import TinyDB, Query
from tinydb.table import Document
from tinydb.storages import MemoryStorage
from tinydb.operations import delete 

from ..helpers.TinyDBBufferedStorage import TinyDBBufferedStorage
from ..helpers.TinyDBBetterTable import TinyDBBetterTable


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


class TinyDBBinding(DBBinding):
	"""	This class implements the TinyDB binding to the database. It is used by the Storage class.
	"""

	__slots__ = (
		'path',
		'cacheSize',
		'writeDelay',
		
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

	def __init__(self, path:str, 
			  		   postfix:str, 
					   cacheSize:int,
					   writeDelay:int) -> None:
		"""	Initialize the TinyDB binding.
		
			Args:
				path: Path to the database directory. If None, the database will be in memory.
				postfix: Postfix for the database file names.
				cacheSize: Size of the cache for the TinyDB tables.
				writeDelay: Delay for writing to the database (in full seconds).
		"""
		
		self.path = path
		""" Path to the database directory. """

		self.cacheSize = cacheSize
		""" Size of the cache for the TinyDB tables. """

		self.writeDelay = writeDelay
		""" Delay for writing to the database. """

		L.isInfo and L.log(f'Cache Size: {self.cacheSize:d}')

		#
		#	Create transaction locks
		#

		self.lockResources = Lock()
		""" Lock for the resources table."""

		self.lockIdentifiers = Lock()
		""" Lock for the identifiers table."""

		self.lockChildResources = Lock()
		""" Lock for the childResources table."""

		self.lockStructuredIDs = Lock()
		""" Lock for the structuredIDs table."""

		self.lockSubscriptions = Lock()
		""" Lock for the subscriptions table."""

		self.lockBatchNotifications	= Lock()
		""" Lock for the batchNotifications table."""

		self.lockStatistics = Lock()
		""" Lock for the statistics table."""

		self.lockActions = Lock()
		""" Lock for the actions table."""

		self.lockRequests = Lock()
		""" Lock for the requests table."""

		self.lockSchedules = Lock()
		""" Lock for the schedules table."""


		# All databases/tables will use the smart query cache
		if not self.path:
			L.isInfo and L.log('DB in memory')

			self.dbResources = TinyDB(storage = MemoryStorage)
			""" The TinyDB database for the resources table."""

			self.dbIdentifiers = TinyDB(storage = MemoryStorage)
			""" The TinyDB database for the identifiers table."""

			self.dbSubscriptions = TinyDB(storage = MemoryStorage)
			""" The TinyDB database for the subscriptions table."""

			self.dbBatchNotifications = TinyDB(storage = MemoryStorage)
			""" The TinyDB database for the batchNotifications table."""

			self.dbStatistics = TinyDB(storage = MemoryStorage)
			""" The TinyDB database for the statistics table."""

			self.dbActions = TinyDB(storage = MemoryStorage)
			""" The TinyDB database for the actions table."""

			self.dbRequests = TinyDB(storage = MemoryStorage)
			""" The TinyDB database for the requests table."""
			#
			self.dbSchedules = TinyDB(storage = MemoryStorage)
			""" The TinyDB database for the schedules table."""

		else:	# path is set

			L.isInfo and L.log('DB in file system. Data directory: ' + self.path)
			os.makedirs(self.path, exist_ok = True)
			
			#
			#	Assign file names
			#

			self.fileResources = f'{self.path}/{_resources}-{postfix}.json'
			""" Filename for the resources table."""

			self.fileIdentifiers = f'{self.path}/{_identifiers}-{postfix}.json'
			""" Filename for the identifiers table."""

			self.fileSubscriptions = f'{self.path}/{_subscriptions}-{postfix}.json'
			""" Filename for the subscriptions table."""

			self.fileBatchNotifications = f'{self.path}/{_batchNotifications}-{postfix}.json'
			""" Filename for the batchNotifications table."""

			self.fileStatistics = f'{self.path}/{_statistics}-{postfix}.json'
			""" Filename for the statistics table."""

			self.fileActions = f'{self.path}/{_actions}-{postfix}.json'
			""" Filename for the actions table."""

			self.fileRequests = f'{self.path}/{_requests}-{postfix}.json'
			""" Filename for the requests table."""

			self.fileSchedules = f'{self.path}/{_schedules}-{postfix}.json'
			""" Filename for the schedules table."""

			#
			#	Open/Create databases
			#

			self.dbResources = TinyDB(self.fileResources, storage = TinyDBBufferedStorage, write_delay = self.writeDelay)
			""" The TinyDB database for the resources table."""

			self.dbIdentifiers = TinyDB(self.fileIdentifiers, storage = TinyDBBufferedStorage, write_delay = self.writeDelay)
			""" The TinyDB database for the identifiers table."""

			self.dbSubscriptions = TinyDB(self.fileSubscriptions, storage = TinyDBBufferedStorage, write_delay = self.writeDelay)
			""" The TinyDB database for the subscriptions table."""

			self.dbBatchNotifications = TinyDB(self.fileBatchNotifications, storage = TinyDBBufferedStorage, write_delay = self.writeDelay)
			""" The TinyDB database for the batchNotifications table."""

			self.dbStatistics = TinyDB(self.fileStatistics, storage = TinyDBBufferedStorage, write_delay = self.writeDelay)
			""" The TinyDB database for the statistics table."""

			self.dbActions = TinyDB(self.fileActions, storage = TinyDBBufferedStorage, write_delay = self.writeDelay)
			""" The TinyDB database for the actions table."""

			self.dbRequests = TinyDB(self.fileRequests, storage = TinyDBBufferedStorage, write_delay = self.writeDelay)
			""" The TinyDB database for the requests table."""

			self.dbSchedules = TinyDB(self.fileSchedules, storage = TinyDBBufferedStorage, write_delay = self.writeDelay)
			""" The TinyDB database for the schedules table."""

		
		#
		#	Open/Create tables
		#
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

		#
		#	Create the Queries
		#

		self.resourceQuery = Query()
		""" The TinyDB query object for the resources table."""

		self.identifierQuery = Query()
		""" The TinyDB query object for the identifiers table."""

		self.subscriptionQuery = Query()
		""" The TinyDB query object for the subscriptions table."""

		self.batchNotificationQuery = Query()
		""" The TinyDB query object for the batchNotifications table."""

		self.actionsQuery = Query()
		""" The TinyDB query object for the actions table."""
		
		self.requestsQuery = Query()
		""" The TinyDB query object for the requests table."""

		self.schedulesQuery = Query()
		""" The TinyDB query object for the schedules table."""


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
		with self.lockSchedules:
			self.dbSchedules.close()


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
		self.tabSchedules.truncate()
	

	def backupDB(self, dir:str) -> bool:
		if not self.path:
			L.isDebug and L.logDebug('In-memory database backup is not supported. Skipping.')
			return True
		
		L.isDebug and L.logDebug(f'Creating DB backup in directory: {dir}')
		# Create the directory if it does not exist
		os.makedirs(dir, exist_ok = True)

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
		L.isDebug and L.logDebug('DB backup done')
		return True


	#
	#	Resources
	#

	def insertResource(self, resource:JSON, ri:str) -> None:
		with self.lockResources:
			self.tabResources.insert(Document(resource, ri))	# type:ignore[arg-type]
	

	def upsertResource(self, resource:JSON, ri:str) -> None:
		#L.logDebug(resource)
		with self.lockResources:
			# Update existing or insert new when overwriting
			self.tabResources.upsert(Document(resource, doc_id = ri))	# type:ignore[arg-type]
	

	def updateResource(self, resource:JSON, ri:str) -> JSON:
		#L.logDebug(resource)
		with self.lockResources:

			# TinyDB update() updates the record, but does not remove fields that are None. It also
			# updates the fields and doesnot update the whole document.
			self.tabResources.update(resource, doc_ids = [ri])	# type:ignore[call-arg, list-item]

			# remove nullified fields from db and resource
			for k in list(resource):
				if resource[k] is None:	# only remove the real None attributes, not those with 0 or zero length
					# The delete() method removes a field from the document
					self.tabResources.update(delete(k), doc_ids = [ri])	# type: ignore[no-untyped-call, call-arg, list-item]
					del resource[k]
			return resource


	def deleteResource(self, ri:str) -> None:
		with self.lockResources:
			self.tabResources.remove(doc_ids = [ri])	# type:ignore[arg-type, list-item]
	

	def searchResources(self, ri:Optional[str] = None, 
							  csi:Optional[str] = None, 
							  srn:Optional[str] = None, 
							  pi:Optional[str] = None, 
							  ty:Optional[int] = None, 
							  aei:Optional[str] = None) -> list[JSON]:

		if not srn:
			with self.lockResources:
				if ri:
					_r = self.tabResources.get(doc_id = ri)	# type:ignore[arg-type]
					return [_r] if _r else [] 	# type:ignore[list-item]
				elif csi:
					return cast(list[JSON], self.tabResources.search(self.resourceQuery.csi == csi))
				elif pi:
					if ty is not None:	# ty is an int
						return cast(list[JSON], self.tabResources.search((self.resourceQuery.pi == pi) & (self.resourceQuery.ty == ty)))
					return cast(list[JSON], self.tabResources.search(self.resourceQuery.pi == pi))
				elif ty is not None:	# ty is an int
					return cast(list[JSON], self.tabResources.search(self.resourceQuery.ty == ty))
				elif aei:
					return cast(list[JSON], self.tabResources.search(self.resourceQuery.aei == aei))
		
		else:
			# for SRN find the ri first and then try again recursively (outside the lock!!)
			if len((identifiers := self.searchIdentifiers(srn = srn))) == 1:
				return self.searchResources(ri = identifiers[0]['ri'])

		return []


	def discoverResourcesByFilter(self, func:Callable[[JSON], bool]) -> list[JSON]:
		with self.lockResources:
			return cast(list[JSON], self.tabResources.search(func))	# type: ignore [arg-type]


	def hasResource(self, ri:Optional[str] = None, 
						  srn:Optional[str] = None,
						  ty:Optional[int] = None) -> bool:
		if not srn:
			with self.lockResources:
				if ri:
					return self.tabResources.contains(doc_id = ri)	# type: ignore [arg-type]
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


	def searchByFragment(self, dct:dict) -> list[JSON]:
		with self.lockResources:
			return cast(list[JSON], self.tabResources.search(self.resourceQuery.fragment(dct)))

	#
	#	Identifiers, Structured RI, Child Resources
	#

	def upsertIdentifier(self, identifierMapping:JSON, structuredPathMapping:JSON, ri:str, srn:str) -> None:
		with self.lockIdentifiers:
			self.tabIdentifiers.upsert(Document(identifierMapping, ri))	# type:ignore[arg-type]
		with self.lockStructuredIDs:
			self.tabStructuredIDs.upsert(Document(structuredPathMapping, srn))	# type:ignore[arg-type]


	def deleteIdentifier(self, ri:str, srn:str) -> None:
		with self.lockIdentifiers:
			self.tabIdentifiers.remove(doc_ids = [ri])		# type:ignore[arg-type,list-item]
		with self.lockStructuredIDs:
			self.tabStructuredIDs.remove(doc_ids = [srn])	# type:ignore[arg-type,list-item]


	def searchIdentifiers(self, ri:Optional[str] = None, 
								srn:Optional[str] = None) -> list[JSON]:
		_r:Document

		# First, find the ri for the srn if one is given. This overrides the ri parameter.
		if srn:
			if (_r := self.tabStructuredIDs.get(doc_id = srn)):	# type:ignore[arg-type, assignment]
				ri = _r['ri'] if _r else None 
			else:
				return []
		if ri:
			with self.lockIdentifiers:
				_r = self.tabIdentifiers.get(doc_id = ri)	# type:ignore[arg-type, assignment]
				return cast(list[JSON], [_r]) if _r else []
		return []


	def upsertChildResource(self, childResource:JSON, ri:str) -> None:
		# L.isDebug and L.logDebug(f'insertChildResource ri:{ri}')

		with self.lockChildResources:

			# First add a new record
			self.tabChildResources.upsert(Document(childResource, ri))	# type:ignore[arg-type]

			# Then add the child ri to the parent's record
			_pi = childResource['pi']
			if _pi:	# ATN: CSE has no parent
				_r:Document
				_r = self.tabChildResources.get(doc_id = _pi) # type:ignore[arg-type, assignment]
				_ch = _r['ch']
				if not any(ri == _slist[0] for _slist in _ch):
					_ch.append( [ri, childResource['ty']] )
					_r['ch'] = _ch
					self.tabChildResources.update(_r, doc_ids = [_pi])	# type:ignore[arg-type, list-item]

			
	def removeChildResource(self, ri:str, pi:str) -> None:

		# L.isDebug and L.logDebug(f'removeChildResource ri:{ri} pi:{pi}')		
		with self.lockChildResources:

			# First remove the record
			self.tabChildResources.remove(doc_ids = [ri])	# type:ignore[arg-type, list-item]

			# Remove (ri, ty) tuple from parent record, for the given ri
			_r:Document = self.tabChildResources.get(doc_id = pi) # type:ignore[arg-type, assignment]
			_ch = _r['ch']
			for _slist in _ch:
				if _slist[0] == ri:
					_ch.remove(_slist)
					_r['ch'] = _ch
					# L.isDebug and L.logDebug(f'removeChildResource _r:{_r}')		
					self.tabChildResources.update(_r, doc_ids = [pi])	# type:ignore[arg-type, list-item]
					break


	def searchChildResourceIDsByParentRIAndType(self, pi:str, ty:Optional[ResourceTypes|list[ResourceTypes]] = None) -> list[str]:
		# First convert ty to a list if it is just an int
		if isinstance(ty, int):
			ty = [ty]
		_r:Document = self.tabChildResources.get(doc_id = pi) #type:ignore[arg-type, assignment]
		if _r:
			if ty is None:	# optimization: only check ty once for None (meaining all types are valid)
				return [ c[0] for c in _r['ch'] ]
			return [ c[0] for c in _r['ch'] if c[1] in ty]	# c is a tuple (ri, ty)
		return []

	#
	#	Subscriptions
	#

	def searchSubscriptionReprs(self, ri:Optional[str] = None, 
								  pi:Optional[str] = None) -> Optional[list[JSON]]:
		with self.lockSubscriptions:
			if ri:
				_r:Document = self.tabSubscriptions.get(doc_id =  ri)	# type:ignore[arg-type, assignment]
				return cast(list[JSON], [_r]) if _r else []
			if pi:
				return cast(list[JSON], self.tabSubscriptions.search(self.subscriptionQuery.pi == pi))
			return None


	def upsertSubscriptionRepr(self, subscription:JSON, ri:str) -> bool:
		with self.lockSubscriptions:
			return self.tabSubscriptions.upsert(Document(subscription, ri)) is not None 	# type:ignore[arg-type]


	def removeSubscriptionRepr(self, ri:str) -> bool:
		with self.lockSubscriptions:
			return len(self.tabSubscriptions.remove(doc_ids = [ri])) > 0	# type:ignore[arg-type, list-item]


	#
	#	BatchNotifications
	#

	def addBatchNotification(self, batchRecord:JSON) -> bool:
	# def addBatchNotification(self, ri:str, nu:str, notificationRequest:JSON) -> bool:
		with self.lockBatchNotifications:
			return self.tabBatchNotifications.insert(batchRecord) is not None


	def countBatchNotifications(self, ri:str, nu:str) -> int:
		with self.lockBatchNotifications:
			return self.tabBatchNotifications.count((self.batchNotificationQuery.ri == ri) & (self.batchNotificationQuery.nu == nu))


	def getBatchNotifications(self, ri:str, nu:str) -> list[JSON]:
		with self.lockBatchNotifications:
			return cast(list[JSON], self.tabBatchNotifications.search((self.batchNotificationQuery.ri == ri) & (self.batchNotificationQuery.nu == nu)))


	def removeBatchNotifications(self, ri:str, nu:str) -> bool:
		with self.lockBatchNotifications:
			return len(self.tabBatchNotifications.remove((self.batchNotificationQuery.ri == ri) & (self.batchNotificationQuery.nu == nu))) > 0


	#
	#	Statistics
	#

	def searchStatistics(self) -> JSON:
		with self.lockStatistics:
			stats = self.tabStatistics.all()
			return stats[0] if stats else None


	def upsertStatistics(self, stats:JSON) -> bool:
		with self.lockStatistics:
			if len(self.tabStatistics) > 0:
				doc_id = self.tabStatistics.all()[0].doc_id
				return self.tabStatistics.update(stats, doc_ids = [doc_id]) is not None
			else:
				return self.tabStatistics.insert(stats) is not None


	def purgeStatistics(self) -> None:
		with self.lockStatistics:
			self.tabStatistics.truncate()


	#
	#	Actions
	#

	def getAllActionReprs(self) -> list[JSON]:
		with self.lockActions:
			actions = self.tabActions.all()
			return cast(list[JSON], actions) if actions else None
	

	def getActionRep(self, ri:str) -> Optional[JSON]:
		with self.lockActions:
			return cast(list[JSON], self.tabActions.get(doc_id = ri))	# type:ignore[arg-type, return-value]


	def searchActionsReprsForSubject(self, subjectRi:str) -> Sequence[JSON]:
		with self.lockActions:
			return self.tabActions.search(self.actionsQuery.subject == subjectRi)
	

	def upsertActionRepr(self, actionRepr:JSON, ri:str) -> bool:
		with self.lockActions:
			return self.tabActions.upsert(Document(actionRepr, ri)) is not None	# type:ignore[arg-type]


	def updateActionRepr(self, actionRepr:JSON) -> bool:
		with self.lockActions:
			return self.tabActions.update(actionRepr, doc_ids = [actionRepr['ri']]) is not None	# type:ignore[arg-type]


	def removeActionRepr(self, ri:str) -> bool:
		with self.lockActions:
			if self.tabActions.get(doc_id = ri):	# type:ignore[arg-type]
				return len(self.tabActions.remove(doc_ids = [ri])) > 0	# type:ignore[arg-type, list-item]
			return False


	#
	#	Requests
	#

	def insertRequest(self, req:JSON, ts:float) -> bool:
		with self.lockRequests:
			try:
				# Insert the request, using the timestamp as the document id
				self.tabRequests.insert(Document(req, self.tabRequests.document_id_class(ts)))	# type:ignore[arg-type]

			except Exception as e:
				L.logErr(f'Exception inserting request/response for ts: {ts}', exc = e)
				return False
		return True
	

	def removeOldRequests(self, maxRequests:int) -> None:
		with self.lockRequests:
			# Remove the oldest requests if we have more than maxRequests
			# We could use the len() function instead of retrieving all requests, but 
			# this would actually create a small overhead because most of the time we have 
			# to retrieve all requests anyway.
			if (_a := self.tabRequests.all()):
				if len(_a) >= maxRequests:
					self.tabRequests.remove(doc_ids = [_a[0].doc_id])
	

	def getRequests(self, ri:Optional[str] = None) -> list[JSON]:
		with self.lockRequests:
			if not ri:
				return cast(list[JSON], self.tabRequests.all())
			return cast(list[JSON], self.tabRequests.search(self.requestsQuery.ri == ri))


	def deleteRequests(self, ri:Optional[str] = None) -> None:
		if ri:
			with self.lockRequests:
				self.tabRequests.remove(self.requestsQuery.ri == ri)
		else:
			with self.lockRequests:
				self.tabRequests.truncate()

	#
	#	Schedules
	#

	def getSchedules(self) -> list[JSON]:
		with self.lockSchedules:
			return cast(list[JSON], self.tabSchedules.all())


	def getSchedule(self, ri:str) -> Optional[JSON]:
		with self.lockSchedules:
			return cast(list[JSON], self.tabSchedules.get(doc_id = ri))	# type:ignore[arg-type, return-value]
	

	def searchSchedulesForParent(self, pi:str) -> list[JSON]:
		with self.lockSchedules:
			return cast(list[JSON], self.tabSchedules.search(self.schedulesQuery.pi == pi))
	

	def upsertSchedule(self, schedule:JSON, ri:str) -> bool:
		with self.lockSchedules:
			return self.tabSchedules.upsert(Document(schedule, ri)) is not None	# type:ignore[arg-type]


	def removeSchedule(self, ri:str) -> bool:
		with self.lockSchedules:
			return len(self.tabSchedules.remove(doc_ids = [ri])) > 0	# type:ignore[arg-type, list-item]
		


