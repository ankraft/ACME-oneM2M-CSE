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
from tinydb import TinyDB, Query, where
from tinydb.storages import MemoryStorage
from tinydb.table import Document
from tinydb.operations import delete 
# TODO remove mypy type checking supressions above as soon as tinydb provides typing stubs

import os, json, re, time
from typing import Callable, Any, cast
from threading import Lock
from Configuration import Configuration
from Constants import Constants as C
from Types import ResourceTypes as T, Result, ResponseCode as RC, ContentSerializationType, JSON
from Logging import Logging
from resources.Resource import Resource
import resources.Factory as Factory
from resources.AnnounceableResource import AnnounceableResource
import CSE, Utils


class Storage(object):

	def __init__(self) -> None:

		# create data directory
		path = None
		if not Configuration.get('db.inMemory'):
			if Configuration.has('db.path'):
				path = Configuration.get('db.path')
				Logging.log('Using data directory: ' + path)
				os.makedirs(path, exist_ok=True)
			else:
				Logging.logErr('db.path not set')
				raise RuntimeError('db.path not set')

		
		self.db = TinyDBBinding(path)
		self.db.openDB(f'-{CSE.cseCsi[1:]}') # add CSE CSI as postfix

		# Reset dbs?
		if Configuration.get('db.resetOnStartup') is True:
			self.db.purgeDB()

		Logging.log('Storage initialized')


	def shutdown(self) -> bool:
		self.db.closeDB()
		Logging.log('Storage shut down')
		return True


	#########################################################################
	##
	##	Resources
	##


	def createResource(self, resource:Resource, overwrite:bool=True) -> Result:
		if resource is None:
			Logging.logErr('resource is None')
			raise RuntimeError('resource is None')

		ri = resource.ri

		# Logging.logDebug(f'Adding resource (ty: {resource.ty:d}, ri: {resource.ri}, rn: {resource.rn})'
		srn = resource.__srn__
		if overwrite:
			Logging.logDebug('Resource enforced overwrite')
			self.db.upsertResource(resource)
		else: 
			if not self.hasResource(ri, srn):	# Only when not resource does not exist yet
				self.db.insertResource(resource)
			else:
				Logging.logWarn(f'Resource already exists (Skipping): {resource}')
				return Result(status=False, rsc=RC.alreadyExists, dbg='resource already exists')

		# Add path to identifiers db
		self.db.insertIdentifier(resource, ri, srn)
		return Result(status=True, rsc=RC.created)


	# Check whether a resource with either the ri or the srn already exists
	def hasResource(self, ri:str=None, srn:str=None) -> bool:
		return (ri is not None and self.db.hasResource(ri=ri)) or (srn is not None and self.db.hasResource(srn=srn))


	def retrieveResource(self, ri:str=None, csi:str=None, srn:str=None, aei:str=None) -> Result:
		""" Return a resource via different addressing methods. """
		resources = []

		if ri is not None:		# get a resource by its ri
			# Logging.logDebug(f'Retrieving resource ri: {ri}')
			resources = self.db.searchResources(ri=ri)

		elif srn is not None:	# get a resource by its structured rn
			# Logging.logDebug(f'Retrieving resource srn: {srn}')
			# get the ri via the srn from the identifers table
			resources = self.db.searchResources(srn=srn)

		elif csi is not None:	# get the CSE by its csi
			# Logging.logDebug(f'Retrieving resource csi: {csi}')
			resources = self.db.searchResources(csi=csi)
		
		elif aei is not None:	# get an AE by its AE-ID
			resources = self.db.searchResources(aei=aei)

		# Logging.logDebug(resources)
		# return CSE.dispatcher.resourceFromDict(resources[0]) if len(resources) == 1 else None,
		if (l := len(resources)) == 1:
			return Factory.resourceFromDict(resources[0])
		elif l == 0:
			return Result(rsc=RC.notFound, dbg='resource not found')

		return Result(rsc=RC.internalServerError, dbg='database inconsistency')


	def retrieveResourcesByType(self, ty: T) -> list[Document]:
		""" Return all resources of a certain type. """
		# Logging.logDebug(f'Retrieving all resources ty: {ty:d}')
		return self.db.searchResources(ty=int(ty))


	def updateResource(self, resource: Resource) -> Result:
		if resource is None:
			Logging.logErr('resource is None')
			raise RuntimeError('resource is None')
		ri = resource.ri
		# Logging.logDebug(f'Updating resource (ty: {resource.ty:d}, ri: {ri}, rn: {resource.rn})')
		return Result(resource=self.db.updateResource(resource), rsc=RC.updated)


	def deleteResource(self, resource: Resource) -> Result:
		if resource is None:
			Logging.logErr('resource is None')
			raise RuntimeError('resource is None')
		# Logging.logDebug(f'Removing resource (ty: {resource.ty:d}, ri: {ri}, rn: {resource.rn})'
		self.db.deleteResource(resource)
		self.db.deleteIdentifier(resource)
		return Result(status=True, rsc=RC.deleted)



	def directChildResources(self, pi:str, ty:T=None) -> list[Resource]:
		"""	Return a list of direct child resources.
		"""
		rs = self.db.searchResources(pi=pi, ty=int(ty) if ty is not None else None)
		result = []
		for r in rs:
			res = Factory.resourceFromDict(r)
			if res.resource is not None:
				result.append(res.resource)
		return result


	def countDirectChildResources(self, pi:str, ty:T = None) -> int:
		"""	Count the direct child resources.
		"""
		return len(self.db.searchResources(pi=pi, ty=int(ty) if ty is not None else None))


	def countResources(self) -> int:
		return self.db.countResources()


	def identifier(self, ri:str) -> list[JSON] | list[Document]:
		return self.db.searchIdentifiers(ri=ri)

	def structuredPath(self, srn:str) -> list[JSON] | list[Document]:
		return self.db.searchIdentifiers(srn=srn)


	def searchByTypeFieldValue(self, ty:T, field:str, value:str) -> list[Resource]:
		"""Search and return all resources of a specific type and a value in a field,
		and return them in an array."""
		# def filterFunc(r:dict) -> bool:
		# 	if 'ty' in r and r['ty'] == ty and field in r:
		# 		f = r[field]
		# 		if isinstance(f, (list, dict)):
		# 			return value in f
		# 		return value == f
		# 	return False
		def filterFunc(r:JSON) -> bool:
			if 'ty' in r and r['ty'] == ty and field in r:
				f = r[field]
				if isinstance(f, (list, dict)):
					return value in f
				return value == f # type: ignore
			return False


		return self.searchByFilter(filterFunc)
		# return self.searchByFilter(lambda r: 'ty' in r and r['ty'] == ty and field in r and r[field] == value)


		# result = []
		# for j in self.db.searchByTypeFieldValue(int(ty), field, value):
		# 	res = CSE.dispatcher.resourceFromDict(j)
		# 	if res.resource is not None:
		# 		result.append(res.resource)
		# return result


	def searchByValueInField(self, field:str, value:str) -> list[Resource]:
		"""Search and return all resources that have a specific value in a field,
		and return them in an array."""
		result = []
		for j in self.db.searchByValueInField(field, value):
			res = Factory.resourceFromDict(j)
			if res.resource is not None:
				result.append(res.resource)
		return result


	def searchByFilter(self, filter:Callable[[JSON], bool]) -> list[Resource]:
		"""	Return a list of resouces that match the given filter, or an empty list.
		"""
		result = []
		for j in self.db.discoverResources(filter):
			res = Factory.resourceFromDict(j)
			if res.resource is not None:
				result.append(res.resource)
		return result

		

	def searchAnnounceableResourcesForCSI(self, csi:str, isAnnounced:bool) -> list[AnnounceableResource]:
		""" Search and retrieve all resources that have the provided CSI in their 
			'at' attribute.
		"""
		result = []

		mcsi = f'{csi}/'
		def _hasCSI(at:list[str]) -> bool:
			for a in at:
				if a == csi or a.startswith(mcsi):
					return True
			return False

		def _announcedFilter(r:JSON) -> bool:
			# if (at := r.get('at')) is not None and csi in at:
			if (at := r.get('at')) is not None and _hasCSI(at):
				if (isa := r.get(Resource._announcedTo)) is not None:
					found = False
					for i in isa:
						if csi == i[0]:
							found = True
							break
					return found == isAnnounced
			return False

		for j in self.db.discoverResources(_announcedFilter):
			res = Factory.resourceFromDict(j)
			if res.resource is not None:
				result.append(res.resource)
		return result



	#########################################################################
	##
	##	Subscriptions
	##

	def getSubscription(self, ri:str) -> JSON:
		# Logging.logDebug(f'Retrieving subscription: {ri}')
		subs = self.db.searchSubscriptions(ri=ri)
		if subs is None or len(subs) != 1:
			return None
		return subs[0]


	def getSubscriptionsForParent(self, pi:str) -> list[Document]:
		# Logging.logDebug(f'Retrieving subscriptions for parent: {pi}')
		return self.db.searchSubscriptions(pi=pi)


	def addSubscription(self, subscription:Resource) -> bool:
		# Logging.logDebug(f'Adding subscription: {ri}')
		return self.db.upsertSubscription(subscription)


	def removeSubscription(self, subscription:Resource) -> bool:
		# Logging.logDebug(f'Removing subscription: {subscription.ri}')
		return self.db.removeSubscription(subscription)


	def updateSubscription(self, subscription:Resource) -> bool:
		# Logging.logDebug(f'Updating subscription: {ri}')
		return self.db.upsertSubscription(subscription)




	#########################################################################
	##
	##	BatchNotifications
	##

	def addBatchNotification(self, ri:str, nu:str, request:JSON, serialization:ContentSerializationType) -> bool:
		return self.db.addBatchNotification(ri, nu, request, serialization)


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
		return self.db.searchStatistics()


	def updateStatistics(self, stats:JSON) -> bool:
		return self.db.upsertStatistics(stats)



	#########################################################################
	##
	##	App Support
	##

	def getAppData(self, id:str) -> JSON:
		return self.db.searchAppData(id)


	def updateAppData(self, data:JSON) -> bool:
		return self.db.upsertAppData(data)


	def removeAppData(self, data:JSON) -> bool:
		return self.db.removeAppData(data)


#########################################################################
#
#	DB class that implements the TinyDB binding
#
#	This class may be moved later to an own module.


class TinyDBBinding(object):

	def __init__(self, path: str = None) -> None:
		self.path = path
		self.cacheSize = Configuration.get('db.cacheSize')
		Logging.log(f'Cache Size: {self.cacheSize:d}')

		# create transaction locks
		self.lockResources = Lock()
		self.lockIdentifiers = Lock()
		self.lockSubscriptions = Lock()
		self.lockBatchNotifications = Lock()
		self.lockStatistics = Lock()
		self.lockAppData = Lock()


	def openDB(self, postfix: str) -> None:
		# All databases/tables will use the smart query cache
		if Configuration.get('db.inMemory'):
			Logging.log('DB in memory')
			self.dbResources = TinyDB(storage=MemoryStorage)										# type: ignore
			self.dbIdentifiers = TinyDB(storage=MemoryStorage)										# type: ignore
			self.dbSubscriptions = TinyDB(storage=MemoryStorage)									# type: ignore
			self.dbBatchNotifications = TinyDB(storage=MemoryStorage)								# type: ignore
			self.dbStatistics = TinyDB(storage=MemoryStorage)										# type: ignore
			self.dbAppData = TinyDB(storage=MemoryStorage)											# type: ignore
		else:
			Logging.log('DB in file system')
			self.dbResources = TinyDB(f'{self.path}/resources{postfix}.json')						# type: ignore
			self.dbIdentifiers = TinyDB(f'{self.path}/identifiers{postfix}.json')					# type: ignore
			self.dbSubscriptions = TinyDB(f'{self.path}/subscriptions{postfix}.json')				# type: ignore
			self.dbBatchNotifications = TinyDB(f'{self.path}/batchNotifications{postfix}.json')		# type: ignore
			self.dbStatistics = TinyDB(f'{self.path}/statistics{postfix}.json')						# type: ignore
			self.dbAppData = TinyDB(f'{self.path}/appdata{postfix}.json')							# type: ignore
		self.tabResources = self.dbResources.table('resources', cache_size=self.cacheSize)
		self.tabIdentifiers = self.dbIdentifiers.table('identifiers', cache_size=self.cacheSize)
		self.tabSubscriptions = self.dbSubscriptions.table('subsriptions', cache_size=self.cacheSize)
		self.tabBatchNotifications = self.dbBatchNotifications.table('batchNotifications', cache_size=self.cacheSize)
		self.tabStatistics = self.dbStatistics.table('statistics', cache_size=self.cacheSize)
		self.tabAppData = self.dbAppData.table('appdata', cache_size=self.cacheSize)


	def closeDB(self) -> None:
		Logging.log('Closing DBs')
		self.dbResources.close()
		self.dbIdentifiers.close()
		self.dbSubscriptions.close()
		self.dbBatchNotifications.close()
		self.dbStatistics.close()
		self.dbAppData.close()


	def purgeDB(self) -> None:
		Logging.log('Purging DBs')
		self.tabResources.truncate()
		self.tabIdentifiers.truncate()
		self.tabSubscriptions.truncate()
		self.tabBatchNotifications.truncate()
		self.tabStatistics.truncate()
		self.tabAppData.truncate()


	#
	#	Resources
	#


	def insertResource(self, resource: Resource) -> None:
		with self.lockResources:
			self.tabResources.insert(resource.dict)
	

	def upsertResource(self, resource: Resource) -> None:
		#Logging.logDebug(resource)
		with self.lockResources:
			# Update existing or insert new when overwriting
			self.tabResources.upsert(resource.dict, Query().ri == resource.ri)		# type: ignore
	

	def updateResource(self, resource: Resource) -> Resource:
		#Logging.logDebug(resource)
		with self.lockResources:
			ri = resource.ri
			self.tabResources.update(resource.dict, Query().ri == ri)	# type: ignore
			# remove nullified fields from db and resource
			# TODO remove Null values recursively
			for k in list(resource.dict):
				if resource.dict[k] is None:
					self.tabResources.update(delete(k), Query().ri == ri)	# type: ignore
					del resource.dict[k]
			return resource


	def deleteResource(self, resource: Resource) -> None:
		with self.lockResources:
			self.tabResources.remove(Query().ri == resource.ri)		# type: ignore
	

	def searchResources(self, ri:str=None, csi:str=None, srn:str=None, pi:str=None, ty:int=None, aei:str=None) -> list[Document]:

		# find the ri first and then try again recursively
		if srn is not None:
			if len((identifiers := self.searchIdentifiers(srn=srn))) == 1:
				return self.searchResources(ri=identifiers[0]['ri'])
			return []

		with self.lockResources:
			if ri is not None:
				return self.tabResources.search(Query().ri == ri)	# type: ignore
			elif csi is not None:
				return self.tabResources.search(Query().csi == csi)	# type: ignore
			elif pi is not None and ty is not None:
				return self.tabResources.search((Query().pi == pi) & (Query().ty == ty))	# type: ignore
			elif pi is not None:
				return self.tabResources.search(Query().pi == pi)	# type: ignore
			elif ty is not None:
				return self.tabResources.search(Query().ty == ty)	# type: ignore
			elif aei is not None:
				return self.tabResources.search(Query().aei == aei)	# type: ignore
			return []


	def discoverResources(self, func:Callable[[JSON], bool]) -> list[Document]:
		with self.lockResources:
			return self.tabResources.search(func)	# type: ignore


	def hasResource(self, ri: str = None, csi: str = None, srn: str = None, ty: int = None) -> bool:

		# find the ri first and then try again recursively
		if srn is not None:
			if len((identifiers := self.searchIdentifiers(srn=srn))) == 1:
				return self.hasResource(ri=identifiers[0]['ri'])
		with self.lockResources:
			if ri is not None:
				return self.tabResources.contains(Query().ri == ri)		# type: ignore
			elif csi is not None:
				return self.tabResources.contains(Query().csi == csi)	# type: ignore
			elif ty is not None:
				return self.tabResources.contains(Query().ty == ty)		# type: ignore
			else:
				return False


	def countResources(self) -> int:
		with self.lockResources:
			return len(self.tabResources)


	# def  searchByTypeFieldValue(self, ty: int, field: str, value: Any) -> list[dict]:
	# 	"""Search and return all resources of a specific type and a value in a field,
	# 	and return them in an array."""
	# 	with self.lockResources:
	# 		# Q = Query()
	# 		# return self.tabResources.search((Q.ty == ty) & (Q[field].any(value)))
	# 		return self.tabResources.search(where[field].test(lambda s: value in s))


	def  searchByValueInField(self, field: str, value: Any) -> list[Document]:
		"""Search and return all resources of a value in a field,
		and return them in an array."""
		with self.lockResources:
			#return self.tabResources.search(where(field).any(value))
			return self.tabResources.search(where(field).test(lambda s: value in s))	# type: ignore


	#
	#	Identifiers
	#


	def insertIdentifier(self, resource: Resource, ri: str, srn: str) -> None:
		with self.lockIdentifiers:
			self.tabIdentifiers.upsert(
				# ri, rn, srn 
				{'ri' : ri, 'rn' : resource.rn, 'srn' : srn, 'ty' : resource.ty}, 
				Query().ri == ri)	# type: ignore


	def deleteIdentifier(self, resource: Resource) -> None:
		with self.lockIdentifiers:
			self.tabIdentifiers.remove(Query().ri == resource.ri)	# type: ignore


	def searchIdentifiers(self, ri: str = None, srn: str = None) -> list[Document]:
		with self.lockIdentifiers:
			if srn is not None:
				return self.tabIdentifiers.search(Query().srn == srn)		# type: ignore
			elif ri is not None:
				return self.tabIdentifiers.search(Query().ri == ri) 		# type: ignore
			return []


	#
	#	Subscriptions
	#


	def searchSubscriptions(self, ri : str = None, pi : str = None) -> list[Document]:
		with self.lockSubscriptions:
			if ri is not None:
				return self.tabSubscriptions.search(Query().ri == ri)		# type: ignore
			if pi is not None:
				return self.tabSubscriptions.search(Query().pi == pi)		# type: ignore
			return None


	def upsertSubscription(self, subscription:Resource) -> bool:
		with self.lockSubscriptions:
			ri = subscription.ri
			result = self.tabSubscriptions.upsert(
									{	'ri'  : ri, 
										'pi'  : subscription.pi,
										'nct' : subscription.nct,
										'net' : subscription['enc/net'],
										'atr' : subscription['enc/atr'],
										'chty': subscription['enc/chty'],
										'exc' : subscription.exc,
										'ln'  : subscription.ln,
										'nus' : subscription.nu,
										'bn'  : subscription.bn,
										'exc' : subscription.exc,
									}, 
									Query().ri == ri)	# type: ignore
			return result is not None


	def removeSubscription(self, subscription:Resource) -> bool:
		with self.lockSubscriptions:
			return len(self.tabSubscriptions.remove(Query().ri == subscription.ri)) > 0		# type: ignore


	#
	#	BatchNotifications
	#

	def addBatchNotification(self, ri:str, nu:str, notificationRequest:JSON, serialization:ContentSerializationType) -> bool:
		with self.lockBatchNotifications:
			result = self.tabBatchNotifications.insert(
									{	'ri' 		: ri,
										'nu' 		: nu,
										'csz'		: serialization.value,
										'tstamp'	: time.time(),
										'request'	: notificationRequest
									})
			return result is not None


	def countBatchNotifications(self, ri:str, nu:str) -> int:
		with self.lockBatchNotifications:
			q = Query()	# type: ignore
			return self.tabBatchNotifications.count((q.ri == ri) & (q.nu == nu))


	def getBatchNotifications(self, ri:str, nu:str) -> list[Document]:
		with self.lockBatchNotifications:
			q = Query()	# type: ignore
			return self.tabBatchNotifications.search((q.ri == ri) & (q.nu == nu))


	def removeBatchNotifications(self, ri:str, nu:str) -> bool:
		with self.lockBatchNotifications:
			q = Query()	# type: ignore
			return len(self.tabBatchNotifications.remove((q.ri == ri) & (q.nu == nu))) > 0

	#
	#	Statistics
	#

	def searchStatistics(self) -> JSON:
		with self.lockStatistics:
			stats = self.tabStatistics.get(doc_id=1)
			return stats if stats is not None and len(stats) > 0 else None


	def upsertStatistics(self, stats:JSON) -> bool:
		with self.lockStatistics:
			if len(self.tabStatistics) > 0:
				return self.tabStatistics.update(stats, doc_ids=[1]) is not None
			else:
				return self.tabStatistics.insert(stats) is not None


	#
	#	App Data
	#

	def searchAppData(self, id:str) -> JSON:
		with self.lockAppData:
			data = self.tabAppData.get(Query().id == id)	# type: ignore
			return data if data is not None and len(data) > 0 else None


	def upsertAppData(self, data:JSON) -> bool:
		with self.lockAppData:
			if 'id' not in data:
				return None
			if len(self.tabAppData) > 0:
				return self.tabAppData.update(data, Query().id == data['id']) is not None 	# type: ignore
			else:
				return self.tabAppData.insert(data) is not None


	def removeAppData(self, data:JSON) -> bool:
		with self.lockAppData:
			if 'id' not in data:
				return False	
			return len(self.tabAppData.remove(Query().id == data['id'])) > 0 # type: ignore
