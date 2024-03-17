#
#	DBBinding.py
#
#	(c) 2024 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Abstract class for database bindings.
#

from __future__ import annotations
from typing import Optional, Callable, Sequence
from abc import ABC, abstractmethod

from ...etc.Types import JSON, ResourceTypes, Operation
from ...resources.Resource import Resource

from ...resources.ACTR import ACTR


class DBBinding(ABC):
	"""	This abstract class defines the interface for database bindings.
	"""

	#
	#	General database operations
	#

	@abstractmethod
	def closeDB(self) -> None:
		"""	Close the database.
		"""
		pass


	@abstractmethod
	def purgeDB(self) -> None:
		"""	Purge the database. Remove all data
		"""
		pass
	

	@abstractmethod
	def backupDB(self, dir:str) -> bool:
		"""	Backup the database to a directory.
		
			Args:
				dir: The directory to backup to.

			Return:
				Boolean value to indicate success or failure.
		"""
		pass


	#
	#	Resource operations
	#

	@abstractmethod
	def insertResource(self, resource: Resource, ri:str) -> None:
		"""	Insert a resource into the database.
		
			Args:
				resource: The resource to insert.
				ri: The resource ID of the resource.
		"""
		pass


	@abstractmethod
	def upsertResource(self, resource: Resource, ri:str) -> None:
		"""	Update or insert a resource into the database.
		
			Args:
				resource: The resource to upate or insert.
				ri: The resource ID of the resource.
		"""
		pass
	

	@abstractmethod
	def updateResource(self, resource: Resource, ri:str) -> Resource:
		"""	Update a resource in the database. Only the fields that are not None will be updated.
		
			Args:
				resource: The resource to update.
				ri: The resource ID of the resource.

			Return:
				The updated resource.
		"""
		pass
	
	@abstractmethod
	def deleteResource(self, resource:Resource) -> None:
		"""	Delete a resource from the database.

			Args:
				resource: The resource to delete.
		"""
		pass
	

	@abstractmethod
	def searchResources(self, ri:Optional[str] = None, 
							  csi:Optional[str] = None, 
							  srn:Optional[str] = None, 
							  pi:Optional[str] = None, 
							  ty:Optional[int] = None, 
							  aei:Optional[str] = None) -> list[JSON]:
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
				A list of found resource documents, or an empty list.
		"""
		pass
	

	@abstractmethod
	def discoverResourcesByFilter(self, func:Callable[[JSON], bool]) -> list[JSON]:
		"""	Search for resources by a filter function.

			Args:
				func: The filter function to use.

			Return:
				A list of found resource documents, or an empty list.
		"""
		pass


	@abstractmethod
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
		pass


	@abstractmethod
	def countResources(self) -> int:
		"""	Return the number of resources in the database.
		
			Return:
				The number of resources in the database.
		"""
		pass


	@abstractmethod
	def searchByFragment(self, dct:dict) -> list[JSON]:
		""" Search and return all resources that match the given dictionary/document. 
		
			Args:
				dct: The dictionary/document to search for.
				
			Return:
				A list of found resources, or an empty list.
		"""
		pass


	#
	#	Identifiers, Structured RI, Child Resources operations
	#

	@abstractmethod
	def upsertIdentifier(self, resource:Resource, ri:str, srn:str) -> None:
		"""	Insert or update an identifier into the identifiers DB.

			Args:
				resource: The resource to insert.
				ri: The resource ID of the resource.
				srn: The structured resource name of the resource.
		"""
		pass


	@abstractmethod
	def deleteIdentifier(self, resource:Resource) -> None:
		"""	Delete an identifier from the identifiers DB.

			Args:
				resource: The resource for which to delete the identifier.
		"""
		pass


	@abstractmethod
	def searchIdentifiers(self, ri:Optional[str] = None, 
								srn:Optional[str] = None) -> list[JSON]:
		"""	Search for an resource ID OR for a structured name in the identifiers DB.

			Either *ri* or *srn* shall be given. If both are given then *srn*
			is taken.
		
			Args:
				ri: Resource ID to search for.
				srn: Structured path to search for.
			Return:
				A list of found identifier documents (see `upsertIdentifier`), or an empty list if not found.
		 """
		pass


	@abstractmethod
	def upsertChildResource(self, resource:Resource, ri:str) -> None:
		"""	Add a child resource to the childResources DB.

			Args:
				resource: The resource to add as a child.
				ri: The resource ID of the resource.
		"""
		pass

			
	@abstractmethod
	def removeChildResource(self, resource:Resource) -> None:
		"""	Remove a child resource from the childResources DB.

			Args:
				resource: The resource to remove as a child.
		"""
		pass


	@abstractmethod
	def searchChildResourcesByParentRI(self, pi:str, ty:Optional[ResourceTypes|list[ResourceTypes]] = None) -> list[str]:
		"""	Search for child resources by parent resource ID.

			Args:
				pi: The parent resource ID.
				ty: The resource type of the child resources to search for, or a list of resource types.

			Return:
				A list of child resource IDs, or an empty list if not found.
		"""
		pass


	#
	#	Subscription operations
	#

	@abstractmethod
	def searchSubscriptions(self, ri:Optional[str] = None, 
								  pi:Optional[str] = None) -> Optional[list[JSON]]:
		"""	Search for subscription representations by resource ID or parent resource ID.

			Only one of the parameters may be used at a time. The order of precedence is: resource ID, parent resource ID.

			Args:
				ri: A resource ID.
				pi: A parent resource ID.

			Return:
				A list of found subscription representations, or None.
		"""
		pass


	@abstractmethod
	def upsertSubscription(self, subscription:Resource) -> bool:
		"""	Update or insert a subscription representation into the database.

			Args:
				subscription: The `SUB` (subscription) to update or insert.

			Return:
				True if the subscription representation was updated or inserted, False otherwise.
		"""
		pass


	@abstractmethod
	def removeSubscription(self, subscription:Resource) -> bool:
		"""	Remove a subscription representation from the database.

			Args:
				subscription: The `SUB` (subscription) to remove.

			Return:
				True if the subscription representation was removed, False otherwise.
		"""
		pass


	#
	#	BatchNotification operations
	#

	@abstractmethod
	def addBatchNotification(self, batchRecord:JSON) -> bool:
		"""	Add a batch notification to the database.

			Args:
				ri: The resource ID of the resource.
				nu: The notification URI.
				notificationRequest: The notification request.

			Return:
				True if the batch notification was added, False otherwise.
		"""
		pass


	@abstractmethod
	def countBatchNotifications(self, ri:str, nu:str) -> int:
		"""	Return the number of batch notifications for a resource and notification URI.

			Args:
				ri: The resource ID of the resource.
				nu: The notification URI.

			Return:
				The number of batch notifications for the resource and notification URI.
		"""
		pass


	@abstractmethod
	def getBatchNotifications(self, ri:str, nu:str) -> list[JSON]:
		"""	Return the batch notifications for a resource and notification URI.

			Args:
				ri: The resource ID of the resource.
				nu: The notification URI.

			Return:
				A list of batch notifications for the resource and notification URI.
		"""
		pass


	@abstractmethod
	def removeBatchNotifications(self, ri:str, nu:str) -> bool:
		"""	Remove the batch notifications for a resource and notification URI.

			Args:
				ri: The resource ID of the resource.
				nu: The notification URI.

			Return:
				True if the batch notifications were removed, False otherwise.
		"""
		pass


	#
	#	Statistic operations
	#

	@abstractmethod
	def searchStatistics(self) -> JSON:
		"""	Search for statistics.

			Return:
				The statistics, or None if not found.
		"""
		pass


	@abstractmethod
	def upsertStatistics(self, stats:JSON) -> bool:
		"""	Update or insert statistics.

			Args:
				stats: The statistics to update or insert.

			Return:
				True if the statistics were updated or inserted, False otherwise.
		"""
		pass


	@abstractmethod
	def purgeStatistics(self) -> None:
		"""	Purge the statistics DB.
		"""
		pass


	#
	#	Action operations
	#

	@abstractmethod
	def getAllActionReprs(self) -> list[JSON]:
		"""	Return all action representations.
		
			Return:
				A list of action representations, or None if not found.
		"""
		pass
	

	@abstractmethod
	def getActionRep(self, ri:str) -> Optional[JSON]:
		"""	Get an action representation by resource ID.
		
			Args:
				ri: The resource ID of the action representation.
			
			Return:
				The action representation, or None if not found.
		"""
		pass


	@abstractmethod
	def searchActionsReprsForSubject(self, ri:str) -> Sequence[JSON]:
		"""	Search for action representations by subject.
		
			Args:
				ri: The resource ID of the action representation's subject.
			
			Return:
				A list of action representations, or None if not found.
		"""
		pass
	

	# TODO Move resource handling to Storage module. This is too detailed here
	@abstractmethod
	def upsertActionRepr(self, actionRepr:JSON, ri:str) -> bool:
		"""	Update or insert an action representation.
		
			Args:
				action: The action representation to update or insert.
				ri: The resource ID of the action representation.
			
			Return:
				True if the action representation was updated or inserted, False otherwise.
		"""
		pass


	@abstractmethod
	def updateActionRepr(self, actionRepr:JSON) -> bool:
		"""	Update an action representation.
		
			Args:
				actionRepr: The action representation to update.
			
			Return:
				True if the action representation was updated, False otherwise.
		"""
		pass


	@abstractmethod
	def removeActionRepr(self, ri:str) -> bool:
		"""	Remove an action representation.

			Args:
				ri: The action's resource ID.
			
			Return:
				True if the action representation was removed, False otherwise.
		"""
		pass


	#
	#	Request operations
	#

	# TODO Move request handling to Storage module. This is too detailed here

	@abstractmethod
	def insertRequest(self, req:JSON, ts:float) -> bool:
		"""	Add a request to the *requests* database.

			Args:
				req: The request to store.
				ts: The timestamp of the request.

			Return:
				Boolean value to indicate success or failure.
		"""
		pass
	
	
	@abstractmethod
	def removeOldRequests(self, maxRequests:int) -> None:
		"""	Remove old requests from the database.

			Args:
				maxRequests: The maximum number of requests to keep.
		"""
		pass
	

	@abstractmethod
	def getRequests(self, ri:Optional[str] = None) -> list[JSON]:
		"""	Get requests for a resource ID, or all requests.
		
			Args:
				ri: The target resource's resource ID. If *None* or empty, then all requests are returned
			
			Return:
				List of *Documents*. May be empty.
		"""
		pass


	@abstractmethod
	def deleteRequests(self, ri:Optional[str] = None) -> None:
		"""	Remnove all stord requests from the database.

			Args:
				ri: Optional resouce ID. Only requests for this resource ID will be deleted.
		"""
		pass


	#
	#	Schedule operations
	#

	@abstractmethod
	def getSchedules(self) -> list[JSON]:
		"""	Get all schedules from the database.
		
			Return:
				List of *Documents*. May be empty.
		"""
		pass


	@abstractmethod
	def getSchedule(self, ri:str) -> Optional[JSON]:
		"""	Get a schedule from the database.
		
			Args:
				ri: The resource ID of the schedule.

			Return:
				The schedule, or *None* if not found.
		"""
		pass
	

	@abstractmethod
	def searchSchedules(self, pi:str) -> list[JSON]:
		"""	Search for schedules in the database.
		
			Args:
				pi: The resource ID of the parent resource.
			
			Return:
				List of *Documents*. May be empty.
		"""
		pass
	

	@abstractmethod
	def upsertSchedule(self, schedule:JSON, ri:str) -> bool:
		"""	Add or update a schedule in the database.
		
			Args:
				schedule: The schedule to store.
				ri: The resource ID of the schedule.
			
			Return:
				True if the schedule was added or updated, False otherwise.
		"""
		pass


	@abstractmethod
	def removeSchedule(self, ri:str) -> bool:
		"""	Remove a schedule from the database.
		
			Args:
				ri: The resource ID of the schedule to remove.

			Return:
				True if the schedule was removed, False otherwise.
		"""
		pass