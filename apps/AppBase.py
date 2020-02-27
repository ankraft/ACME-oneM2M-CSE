#
#	AppBase.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	This base class should be used to create applications. It provides
#	many utility methods like registering with the CSE etc.
#

from Configuration import Configuration
from Logging import Logging
from Constants import Constants as C
import CSE, Utils
from helpers import BackgroundWorker
import json, os


class AppBase(object):
				

	def __init__(self, rn, originator):
		self.rn 					= rn
		self.originator 			= originator
		self.cseri 					= Configuration.get('cse.ri')
		self.csern 					= Configuration.get('cse.rn')
		self.srn 					= self.csern + '/' + self.rn
		self.url 					= Configuration.get('http.address') + Configuration.get('http.root')
		self.worker 				= None
		

	def shutdown(self):
		self.stopWorker()


	#########################################################################
	#
	#	Requests
	#

	def retrieveResource(self, ri=None, srn=None):
		return CSE.httpServer.sendRetrieveRequest(self._id(ri, srn), self.originator)


	def createResource(self, ri=None, srn=None, ty=None, jsn=None):
		return CSE.httpServer.sendCreateRequest(self._id(ri, srn), self.originator, ty, json.dumps(jsn))


	def updateResource(self, ri=None, srn=None, jsn=None):
		return CSE.httpServer.sendUpdateRequest(self._id(ri, srn), self.originator, json.dumps(jsn))


	def deleteResource(self, ri=None, srn=None):
		return CSE.httpServer.sendDeleteRequest(self._id(ri, srn), self.originator)


	def _id(self, ri, srn):
		if ri is not None:
			return self.url + self.cseri + '/' + ri
		elif srn is not None:
			return self.url + srn
		return None


	def retrieveCreate(self, srn=None, jsn=None, ty=C.tMGMTOBJ):
		# First check whether node exists and create it if necessary
		if (result := self.retrieveResource(srn=srn))[1] != C.rcOK:

			# No, so create mgmtObj specialization
			srn = os.path.split(srn)[0] if srn.count('/') >= 0 else ''
			(n, rc) = self.createResource(srn=srn, ty=ty, jsn=jsn)
			if n is not None:
				return Utils.resourceFromJSON(n)
		else: # just retrieve
			return Utils.resourceFromJSON(result[0])
		return None


	#########################################################################

	def startWorker(self, updateInterval, worker):
		self.stopWorker()
		self.worker = BackgroundWorker.BackgroundWorker(updateInterval, worker)
		self.worker.start()


	def stopWorker(self):
		if self.worker is not None:
			self.worker.stop()
			self.worker = None

