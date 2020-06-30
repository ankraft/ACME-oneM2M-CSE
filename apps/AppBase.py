#
#	AppBase.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	This base class should be used to create applications. It provides
#	many utility methods like registering with the CSE etc.
#

import json, os
from typing import Optional, Tuple, Dict, Any, Callable
from Configuration import Configuration
from resources.Resource import Resource
from Logging import Logging
from Constants import Constants as C
import CSE, Utils
from helpers.BackgroundWorker import BackgroundWorker


class AppBase(object):
				

	def __init__(self, rn: str, originator: str) -> None:
		self.rn:str 					= rn
		self.originator:str				= originator
		self.cseri:str					= Configuration.get('cse.ri')
		self.csern:str					= Configuration.get('cse.rn')
		self.srn:str 					= self.csern + '/' + self.rn
		self.url:str					= Configuration.get('http.address') + Configuration.get('http.root')
		self.worker:BackgroundWorker	= None
		

	def shutdown(self) -> None:
		self.stopWorker()


	#########################################################################
	#
	#	Requests
	#

	def retrieveResource(self, ri: str = None, srn:str = None) -> Tuple[dict, int, str]:
		return CSE.httpServer.sendRetrieveRequest(self._id(ri, srn), self.originator)


	def createResource(self, ri:str = None, srn:str = None, ty:int = None, jsn:Dict[str, Any] = None) -> Tuple[dict, int, str]:
		return CSE.httpServer.sendCreateRequest(self._id(ri, srn), self.originator, ty, json.dumps(jsn))


	def updateResource(self, ri: str = None, srn: str = None, jsn: dict = None) -> Tuple[dict, int, str]:
		return CSE.httpServer.sendUpdateRequest(self._id(ri, srn), self.originator, json.dumps(jsn))


	def deleteResource(self, ri: str = None, srn: str = None) -> Tuple[dict, int, str]:
		return CSE.httpServer.sendDeleteRequest(self._id(ri, srn), self.originator)


	def _id(self, ri: str, srn: str) -> str:
		if ri is not None:
			return self.url + '/' + ri
			# return self.url + self.cseri + '/' + ri
		elif srn is not None:
			return self.url + '/' + srn
		return None


	def retrieveCreate(self, srn : str = None, jsn: dict = None, ty:int = C.tMGMTOBJ) -> Resource:
		# First check whether node exists and create it if necessary
		if (result := self.retrieveResource(srn=srn))[1] != C.rcOK:

			# No, so create mgmtObj specialization
			srn = os.path.split(srn)[0] if srn.count('/') >= 0 else ''
			n, rc, msg = self.createResource(srn=srn, ty=ty, jsn=jsn)
			if n is not None:
				return Utils.resourceFromJSON(n)[0]
		else: # just retrieve
			return Utils.resourceFromJSON(result[0])[0]
		return None


	#########################################################################

	def startWorker(self, updateInterval: float, worker: Callable, name: str = None) -> None:
		self.stopWorker()
		self.worker = BackgroundWorker(updateInterval, worker, name)
		self.worker.start()


	def stopWorker(self) -> None:
		if self.worker is not None:
			self.worker.stop()
			self.worker = None
