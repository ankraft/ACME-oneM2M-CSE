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

import os
from configparser import ConfigParser

from ..etc.Types import ResourceTypes, JSON, Operation, ResponseStatusCode
from ..etc.ResponseStatusCodes import NOT_FOUND, INTERNAL_SERVER_ERROR, CONFLICT
from ..etc.DateUtils import utcTime, fromDuration
from ..etc.Constants import RuntimeConstants as RC
from .Configuration import Configuration, ConfigurationError
from ..resources.Resource import Resource
from ..resources.ACTR import ACTR
from ..resources.SCH import SCH
from ..resources.Factory import resourceFromDict
from .Logging import Logging as L

from ..databases.DBBinding import DBBinding
from ..databases.TinyDBBinding import TinyDBBinding

if 'ACME_NO_PGSQL' not in os.environ:
	from ..databases.PostgreSQLBinding import PostgreSQLBinding
	_disablePostgreSQL = False
else:
	_disablePostgreSQL = True


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
		'db',
	)
	""" Define slots for instance variables. """

	def __init__(self) -> None:
		"""	Initialization of the storage manager.

			Raises:
				RuntimeError: In case of an error during initialization.
		"""

		self.db:DBBinding = None
		""" The database object. """
	
		if _disablePostgreSQL:
			L.isDebug and L.logDebug('PostgreSQL is disabled by environment variable')

		# Create the database object and connect to the database
		try:
			match Configuration.database_type:
				case 'tinydb':
					# create tinyDB object and open DB for file handling
					self.db = TinyDBBinding(Configuration.database_tinydb_path, 		
											RC.cseCsi[1:], # add CSE CSI as postfix
											Configuration.database_tinydb_cacheSize,
											Configuration.database_tinydb_writeDelay
										) 
				case 'memory':
					# create tinyDB object and open DB for in-memory handling
					self.db = TinyDBBinding(None,
											RC.cseCsi[1:], # add CSE CSI as postfix
											Configuration.database_tinydb_cacheSize,
											Configuration.database_tinydb_writeDelay
										)
				case 'postgresql':
					# create PostgreSQL object and connect to the DB
					if _disablePostgreSQL:
						raise RuntimeError('Configuration conflict: Use of PostgreSQL is disabled in the environment, but enabled in the configuration.')
					self.db = PostgreSQLBinding(Configuration.database_postgresql_host,	
												Configuration.database_postgresql_port,	
												Configuration.database_postgresql_role,	
												Configuration.database_postgresql_password,
												Configuration.database_postgresql_database,
												Configuration.database_postgresql_schema
											)
				case _:
					L.logErr('Unknown database type')
					quit()
		except Exception as e:
			raise INTERNAL_SERVER_ERROR(f'Database error: {e}')

		dbReset = Configuration.database_resetOnStartup # Indicator that the database should be reset or cleared during start-up. """
		

		# Reset dbs?
		if dbReset:
			self.backupDB()	# In this case do a backup *before* removing everything.
			self.purge()

		else:
		
			# Check validity
			if not self._validateDB():
				raise RuntimeError('DB error. Please check or remove database files.')
		
			# Make backup *after* validation, only when *not* reset
			if not self.backupDB():
				self.db.closeDB()
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
			self.getAllActionReprs()
			dbFile = _schedules
			self.getSchedules()

			# TODO requests

		except Exception as e:
			L.logErr(f'Error validating data files. Error in {dbFile} database.', exc = e)
			return False
		return True
	

	def backupDB(self) -> bool:
		"""	Creating a backup from the DB to a sub directory.

			Return:
				Boolean indicating the success of the backup operation.
		"""
		return self.db.backupDB(Configuration.database_backupPath)
		

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
		_ri  = resource.ri
		_pi = resource.pi
		_ty = resource.ty
		_srn = resource.getSrn()
		
		if overwrite:
			L.isDebug and L.logDebug('Resource enforced overwrite')
			self.db.upsertResource(resource.dict, _ri)
		else: 
			if not self.hasResource(_ri, _srn):	# Only when resource with same ri or srn does not exist yet
				self.db.insertResource(resource.dict, _ri)
			else:
				raise CONFLICT(L.logWarn(f'Resource already exists (Skipping): {resource} ri: {_ri} srn:{_srn}'))

		# Add path to identifiers db
		self.db.upsertIdentifier(
			# identifier mapping
			{ 'ri' : _ri, 
			  'rn' : resource.rn, 
			  'srn' : _srn,
			  'ty' : _ty
			}, 
			{ 'srn': _srn,
			  'ri' : _ri 
			}, 
			_ri, _srn)	# type:ignore[arg-type]

		# Add record to childResources db
		self.db.upsertChildResource(
			{ 'ri' : _ri,
			  'pi' : _pi,
			  'ty' : _ty,
			  'ch' : [] 
			}, _ri)


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


	def retrieveResourcesByType(self, ty:ResourceTypes) -> list[JSON]:
		""" Return all resources of a certain type. 

			Args:
				ty: resource type to retrieve.

			Returns:
				List of resource *JSON* objects, not *Resource* objects.
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
		# ri = resource.ri
		# L.logDebug(f'Updating resource (ty: {resource.ty}, ri: {ri}, rn: {resource.rn})')
		# L.logDebug(str(resource.dict))
		try:
			resource.dict = self.db.updateResource(resource.dict, resource.ri)
		except KeyError:
			raise NOT_FOUND(L.logDebug(f'Cannot update: {resource.ri} (NOT_FOUND). Could be an expected error.'))
		# L.logDebug(str(resource.dict))
		return resource


	def deleteResource(self, resource:Resource) -> None:
		"""	Delete a resource from the database.

			Args:
				resource: Resource to delete.
			
			Raises:
				NOT_FOUND: In case the resource does not exist.
		"""
		# L.logDebug(f'Removing resource (ty: {resource.ty}, ri: {resource.ri}, rn: {resource.rn})')
		try:
			_ri = resource.ri
			_pi = resource.pi
			self.db.deleteResource(_ri)
			self.db.deleteIdentifier(_ri, resource.getSrn())
			self.db.removeChildResource(_ri, _pi)
		except KeyError:
			raise NOT_FOUND(L.logDebug(f'Cannot remove: {resource.ri} (NOT_FOUND). Could be an expected error.'))


	# TODO split this into two methods (one for resources, one for raw resources)
		
	def directChildResources(self, pi:str, 
								   ty:Optional[ResourceTypes|list[ResourceTypes]] = None, 
								   raw:Optional[bool] = False) -> list[JSON]|list[Resource]:
		"""	Return a list of direct child resources, or an empty list

			Args:
				pi: The parent resource's Resource ID.
				ty: Optional resource type or list of resource types to filter the result.
				raw: When "True" then return the child resources as resource dictionary instead of resources.

			Returns:
				Return a list of resources, or a list of raw resource dictionaries.
		"""
		if (_ris := self.db.searchChildResourceIDsByParentRIAndType(pi, ty)):
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
		return self.db.searchChildResourceIDsByParentRIAndType(pi, ty)


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


	def identifier(self, ri:str) -> list[JSON]:
		"""	Search for the resource identifer mapping with the given unstructured resource ID.

			Args:
				ri: Unstructured resource ID for the mapping to look for.

			Return:
				List of found resources identifier mappings, or an empty list.
		"""
		return self.db.searchIdentifiers(ri = ri)


	def structuredIdentifier(self, srn:str) -> list[JSON]:
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

	def getSubscription(self, ri:str) -> Optional[JSON]:
		"""	Retrieve a subscription representation (not a oneM2M `Resource` object) from the DB.

			Args:
				ri: The subscription's resource ID.

			Return:
				The subscription as a JSON dictionary, or None.
		"""
		# L.logDebug(f'Retrieving subscription: {ri}')
		subs = self.db.searchSubscriptionReprs(ri = ri)
		if not subs or len(subs) != 1:
			return None
		return subs[0]


	def getSubscriptionsForParent(self, pi:str) -> list[JSON]:
		"""	Retrieve all subscriptions representations (not oneM2M `Resource` objects) for a parent resource.

			Args:
				pi: The parent resource's resource ID.

			Return:
				List of subscriptions. This is not the oneM2M Subscription resource, but the internal subscription representation.
		"""
		return self.db.searchSubscriptionReprs(pi = pi)


	def upsertSubscription(self, subscription:Resource) -> bool:
		"""	Add or update a subscription to the DB.
		
			Args:
				subscription: The subscription `Resource` to add.
				
			Return:	
				Boolean value to indicate success or failure.
		"""
		# L.logDebug(f'Adding subscription: {ri}')
		ri = subscription.ri
		return self.db.upsertSubscriptionRepr(
			{ 'ri'  	: ri, 
			  'pi'  	: subscription.pi,
			  'nct' 	: subscription.nct,
			  'net' 	: subscription.attribute('enc/net'),	# TODO perhaps store enc as a whole?
			  'atr' 	: subscription.attribute('enc/atr'),
			  'chty'	: subscription.attribute('enc/chty'),
			  'om'		: subscription.attribute('enc/om'),
			  'exc' 	: subscription.exc,
			  'ln'  	: subscription.ln,
			  'nus' 	: subscription.nu,
			  'bn'  	: subscription.bn,
			  'cr'  	: subscription.cr,
			  'nec'  	: subscription.nec,
			  'org'		: subscription.getOriginator(),
			  'ma' 		: fromDuration(subscription.ma) if subscription.ma else None, # EXPERIMENTAL ma = maxAge
			  'nse' 	: subscription.nse,
			  'eeno' 	: subscription.eeno,
			 }, ri) is not None


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
			return self.db.removeSubscriptionRepr(subscription.ri)
		except KeyError as e:
			raise NOT_FOUND(L.logDebug(f'Cannot subscription data for: {subscription.ri} (NOT_FOUND). Could be an expected error.'))


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
		return self.db.addBatchNotification(
			{	'ri' 		: ri,
				'nu' 		: nu,
				'tstamp'	: utcTime(),
				'request'	: request
			})
	

	def countBatchNotifications(self, ri:str, nu:str) -> int:
		"""	Count the number of batch notifications for a target resource and a notification URI.
		
			Args:
				ri: The resource ID of the target resource.
				nu: The notification URI.
				
			Return:
				The number of matching batch notifications.
		"""
		return self.db.countBatchNotifications(ri, nu)


	def getBatchNotifications(self, ri:str, nu:str) -> list[JSON]:
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

	def getAllActionReprs(self) -> list[JSON]:
		"""	Retrieve all action representations from the DB.

			Return:
				List of *Documents*. May be empty.
		"""
		return self.db.getAllActionReprs()
	

	def getActionRepr(self, ri:str) -> Optional[JSON]:
		"""	Retrieve an action representation from the DB.

			Args:
				ri: The action's resource ID.

			Return:
				The action's data as a *Document*, or None.
		"""
		return self.db.getActionRep(ri)

	
	def searchActionReprsForSubject(self, subjectRi:str) -> Sequence[JSON]:
		"""	Search for action representation for a subject resource.
		
			Args:
				subjectRi: The subject resource's resource ID.
			
			Return:
				List of matching action representations.
		"""
		return self.db.searchActionsReprsForSubject(subjectRi)


	def upsertAction(self, action:ACTR, periodTS:float, count:int) -> bool:
		"""	Update or add an action as an action representation in the DB.
		
			Args:
				action: The action to update or insert.
				periodTS: The period for the action.
				count: The run count for the action.

			Return:
				Boolean value to indicate success or failure.
		"""
		ri = action.ri
		sri = action.sri

		return self.db.upsertActionRepr(
			{	'ri':		ri,
				'subject':	sri if sri else action.pi,
				'dep':		action.dep,
				'apy':		action.apy,
				'evm':		action.evm,
				'evc':		action.evc,	
				'ecp':		action.ecp,
				'periodTS': periodTS,
				'count':	count,
			},
			ri) is not None


	def updateActionRepr(self, actionRepr:JSON) -> bool:
		"""	Update an action representation (not an actual action) in the DB.
		
			Args:
				actionRepr: The action representation to update.

			Return:
				Boolean value to indicate success or failure.
		"""
		return self.db.updateActionRepr(actionRepr)


	def removeActionRepr(self, ri:str) -> bool:
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
		# return self.db.insertRequest(op, ri, srn, originator, outgoing, ot, request, response)

		# Remove old requests first up to the maximum number of requests
		self.db.removeOldRequests(Configuration.cse_operation_requests_size)

		# Store the request
		_ts = utcTime()
		_doc =	{ 'ri': ri,
	  			  'srn': srn,
				  'ts': _ts,
				  'org': originator,
				  'op': op,
				  'rsc': response.get('rsc', ResponseStatusCode.UNKNOWN),
				  'out': outgoing,
				  'ot': ot,
				  'req': { k: v for k, v in request.items() if v is not None }, # Remove None values
				  'rsp': { k: v for k, v in response.items() if v is not None }	# Remove None values
				}
		_doc = { k: v for k, v in _doc.items() if v is not None }	# Remove remaining None values
		return self.db.insertRequest(_doc, _ts)


	def getRequests(self, ri:Optional[str] = None, sortedByOt:bool = False) -> list[JSON]:
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

	def getSchedules(self) -> list[JSON]:
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
		for s in self.db.searchSchedulesForParent(pi):
			result.extend(s['sce'])
		return result


	def upsertSchedule(self, schedule:SCH) -> bool:
		"""	Add or update a schedule in the DB.

			Args:
				schedule: The schedule to add or update.

			Return:
				Boolean value to indicate success or failure.
		"""
		# return self.db.upsertSchedule(schedule.ri, schedule.pi, schedule.attribute('se/sce'))
		return self.db.upsertSchedule(
					{ 'ri': schedule.ri,
						'pi': schedule.pi,
						'sce': schedule.attribute('se/sce') 
					}, schedule.ri) is not None	


	def removeSchedule(self, schedule:SCH) -> bool:
		"""	Remove a schedule from the DB.

			Args:
				schedule: The schedule to remove.
			
			Return:
				Boolean value to indicate success or failure.
		"""
		return self.db.removeSchedule(schedule.ri)

