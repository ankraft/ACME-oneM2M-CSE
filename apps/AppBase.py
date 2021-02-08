#
#	AppBase.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	This base class should be used to create applications. It provides
#	many utility methods like registering with the CSE etc.
#

import os
from typing import Dict, Any, Callable
from Configuration import Configuration
from resources.Resource import Resource
from Logging import Logging
from Constants import Constants as C
from Types import ResourceTypes as T, Result, ResponseCode as RC, JSON
import CSE
from helpers.BackgroundWorker import BackgroundWorkerPool, BackgroundWorker
import resources.Factory as Factory


class AppBase(object):
				

	def __init__(self, rn: str, originator: str) -> None:
		self.rn:str 					= rn
		self.originator:str				= originator
		self.cseCsi						= CSE.cseCsi
		self.csern:str					= CSE.cseRn
		self.srn:str 					= self.csern + '/' + self.rn
		self.url:str					= Configuration.get('http.address') + Configuration.get('http.root')
		self.worker:BackgroundWorker 	= None
		

	def shutdown(self) -> None:
		self.stopWorker()


	#########################################################################
	#
	#	Requests
	#

	def retrieveResource(self, ri:str=None, srn:str=None) -> Result:
		return CSE.request.sendRetrieveRequest(self._id(ri, srn), self.originator)


	def createResource(self, ri:str=None, srn:str=None, ty:T=None, data:Dict[str, Any]=None) -> Result:
		return CSE.request.sendCreateRequest(self._id(ri, srn), self.originator, ty, data)


	def updateResource(self, ri:str=None, srn:str=None, data:JSON=None) -> Result:
		return CSE.request.sendUpdateRequest(self._id(ri, srn), self.originator, data)


	def deleteResource(self, ri:str=None, srn:str=None) -> Result:
		return CSE.request.sendDeleteRequest(self._id(ri, srn), self.originator)


	def _id(self, ri: str, srn: str) -> str:
		if ri is not None:
			return self.url + '/' + ri
		elif srn is not None:
			return self.url + '/' + srn
		return None


	def retrieveCreate(self, srn:str=None, data:JSON=None, ty:T=T.MGMTOBJ) -> Resource:
		# First check whether node exists and create it if necessary
		if (result := self.retrieveResource(srn=srn)).rsc != RC.OK:

			# No, so create mgmtObj specialization
			srn = os.path.split(srn)[0] if srn.count('/') >= 0 else ''
			result = self.createResource(srn=srn, ty=ty, data=data)
			if result.rsc == RC.created:
				return Factory.resourceFromDict(result.dict).resource	# type:ignore[no-any-return]
			else:
				#Logging.logErr(n)
				pass
		else: # just retrieve
			return Factory.resourceFromDict(result.dict).resource		# type:ignore[no-any-return]
		return None


	#########################################################################

	def startWorker(self, updateInterval:float, worker:Callable, name:str=None) -> None:	# type:ignore[type-arg]
		self.stopWorker()
		self.worker = BackgroundWorkerPool.newWorker(updateInterval, worker, name).start()


	def stopWorker(self) -> None:
		if self.worker is not None:
			self.worker.stop()
			self.worker = None
