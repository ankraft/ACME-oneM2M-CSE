#
#	RemoteCSEManager.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	This entity handles the registration to remote CSEs as well as the management
#	of remotly registered CSEs in this CSE. It also handles the forwarding of
#	transit requests to remote CSEs.
#


import requests, json, urllib.parse
from typing import List, Tuple, Dict
from flask import Request
from Configuration import Configuration
from Logging import Logging
from Constants import Constants as C
from Types import ResourceTypes as T, Result, CSEType, ResponseCode as RC
import Utils, CSE
from resources import CSR, CSEBase
from resources.Resource import Resource
from helpers.BackgroundWorker import BackgroundWorker


class RemoteCSEManager(object):

	def __init__(self) -> None:
		self.csetype 							= Configuration.get('cse.type')
		self.isConnected 						= False
		self.remoteAddress						= Configuration.get('cse.registrar.address')
		self.remoteRoot 						= Configuration.get('cse.registrar.root')
		self.remoteCsi							= Configuration.get('cse.registrar.csi')
		self.remoteCseRN						= Configuration.get('cse.registrar.rn')
		self.originator							= Configuration.get('cse.csi')	# Originator is the own CSE-ID
		self.cseCsi								= Configuration.get('cse.csi')
		self.cseRI								= Configuration.get('cse.ri')
		self.worker:BackgroundWorker			= None
		self.checkInterval						= Configuration.get('cse.registrar.checkInterval')
		self.remoteCSEURL						= '%s%s/~%s/%s' % (self.remoteAddress, self.remoteRoot, self.remoteCsi, self.remoteCseRN)
		self.remoteCSRURL						= '%s%s' % (self.remoteCSEURL, self.cseCsi)
		self.ownRemoteCSR:Resource				= None 	# The own CSR at the registrar if there is one
		self.registrarCSE:Resource				= None 	# The registrar CSE if there is one
		self.descendantCSR:Dict[str, Resource]	= {}	# dict of descendantCSR's csi's


		CSE.event.addHandler(CSE.event.registeredToRemoteCSE, self.handleRegistrarRegistration)			# type: ignore
		CSE.event.addHandler(CSE.event.deregisteredFromRemoteCSE, self.handleRegistrarDeregistration)			# type: ignore
		CSE.event.addHandler(CSE.event.remoteCSEHasRegistered, self.handleRemoteCSERegistration)			# type: ignore
		CSE.event.addHandler(CSE.event.remoteCSEHasDeregistered, self.handleRemoteCSEDeregistration)			# type: ignore

		self.start()
		Logging.log('RemoteCSEManager initialized')


	def shutdown(self) -> None:
		self.stop()
		Logging.log('RemoteCSEManager shut down')


	#
	#	Connection Monitor
	#

	# Start the monitor in a thread. 
	def start(self) -> None:
		if not Configuration.get('cse.enableRemoteCSE'):
			return;
		Logging.log('Starting remote CSE connection monitor')
		self.worker = BackgroundWorker(self.checkInterval, self.connectionMonitorWorker, 'csrMonitor')
		self.worker.start()


	# Stop the monitor. Also delete the CSR resources on both sides
	def stop(self) -> None:
		if not Configuration.get('cse.enableRemoteCSE'):
			return;
		Logging.log('Stopping remote CSE connection monitor')

		# Stop the thread
		if self.worker is not None:
			self.worker.stop()

		# Remove resources
		if self.csetype in [ CSEType.ASN, CSEType.MN ]:
			self._deleteRemoteCSR()	# delete remote CSR. Ignore result
		res = self._retrieveLocalCSRs()	# retrieve local CSR
		if res.rsc == RC.OK:
			self._deleteLocalCSR(res.lst[0])		# delete local CSR


	#
	#	Check the connection, and presence and absence of CSE and CSR in a 
	#	thread periodically.
	#	
	#	It works like this for connections for an ASN or MN to the remote CSE:
	#	
	#	Is there is a local <remoteCSE> for a remote <CSEBase>?
	#		- Yes: Is there a remote <remoteCSE>?
	#			- Yes: 
	#				- Retrieve the remote <CSEBase>.
	#				- Has the remote <CSEBase> been modified?
	#					- Yes: 
	#						- Update the local <remoteCSE>
	#				- Retrieve the local <CSEBase>
	#				- Has the local <CSEBase> been modified?
	#					- Yes: 
	#						-Update the remote <remoteCSE>
	#			- No: 
	#				- Delete a potential local <remoteCSE>
	#				- Create a remote <remoteCSE>
	#					- Success:
	#						- Retrieve the remote <CSEBase>
	#						- Create a local <remoteCSE> for it
	#		- No: 
	#			- Delete a potential remote <remoteCSE>
	#			- Create a new remote <remoteCSE>
	#				- Success:
	#					- Retrieve the remote <CSEBase>
	#					- Create a local <remoteCSE> for it
	#					- Create a local <acp> for the local <remoteCSE>
	#					- Create a local <acp> for the local <CSEBase> with the remote cseID
	#		

	def connectionMonitorWorker(self) -> bool:
		Logging.logDebug('Checking connections to remote CSEs')
		try:
			# Check the current state of the connection to the "upstream" CSEs
			if self.csetype in [ CSEType.ASN, CSEType.MN ]:
				self._checkOwnConnection()

			# Check the liveliness of other CSR connections
			if self.csetype in [ CSEType.MN, CSEType.IN ]:
				self._checkCSRLiveliness()
		except Exception as e:
			Logging.logErr('Exception: %s' % e)
			import traceback
			Logging.logErr(traceback.format_exc())
			return True
		return True


	#########################################################################
	#
	#	Event Handlers
	#

	def handleRegistrarRegistration(self, registrarCSE:Resource, ownRemoteCSR:Resource) -> None:
		"""	Add the CSE/CSR CSI to the list of registered CSI. """
		self.registrarCSE = registrarCSE
		self.ownRemoteCSR = ownRemoteCSR


	def handleRegistrarDeregistration(self, remoteCSR:Resource = None) -> None:
		"""	Remove the CSE/CSR CSI from the list of registered CSI. """
		self.registrarCSE = None
		self.ownRemoteCSR = None


	def handleRemoteCSERegistration(self, remoteCSR:Resource) -> None:
		"""	Add the the remote CSE's CSR CSI to the list of registered CSI. """
		if (csi := remoteCSR.csi) is None:
			return
		if csi in self.descendantCSR:	# already registered
			return
		# don't register registrar CSE here
		if (rcse := self.registrarCSE) is not None and (rcsi := rcse.csi) is not None and rcsi == csi:
			return
		self.descendantCSR[csi] = remoteCSR

		Logging.logDebug('Descendant CSE registered %s' % csi)
		# localCSE = Utils.getCSE().resource
		# dcse = []
		# for csi in self.descendantCSR:
		# 	if self.registrarCSE is None or (self.registrarCSE is not None and csi != self.registrarCSE.csi):
		# 		dcse.append(csi)
		# localCSE['dcse'] = dcse
		# localCSE.dbUpdate()	# update in DB
		if self.csetype in [ CSEType.ASN, CSEType.MN ]:
			self._updateRemoteCSR(localCSE)



	def handleRemoteCSEDeregistration(self, remoteCSR:Resource ) -> None:
		"""	Remove the CSE/CSR CSI from the list of registered CSI. """
		if (csi := remoteCSR.csi) is not None and csi in self.descendantCSR:
			del self.descendantCSR[csi]


	#########################################################################

	# def _removeRegisteredCSE(self, resource:Resource) -> None:
	# 	if resource is None:	# If own registrar
	# 		self.registeredCSIs.remove(self.remoteCsi)
	# 	else:
	# 		if (csi := resource['csi']) in self.registeredCSIs:
	# 			self.registeredCSIs.remove(csi)
	# 	#Logging.logDebug(self.registeredCSIs)


	# def _addRegisteredCSE(self, resource:Resource) -> None:
	# 	if (csi := resource['csi']) not in self.registeredCSIs:
	# 		self.registeredCSIs.append(csi)
	# 	#Logging.logDebug(self.registeredCSIs)



	#########################################################################
	#
	#	Connection Checkers
	#

	# Check the connection for this CSE to the remote CSE.
	def _checkOwnConnection(self) -> None:
		# first check whether there is already a local CSR
		res = self._retrieveLocalCSRs()
		if res.rsc == RC.OK:
			localCSR = res.lst[0] # hopefully, there is only one registrar CSR+
			result = self._retrieveRemoteCSR()	# retrieve own from the remote CSE
			if result.rsc == RC.OK:
				self.ownRemoteCSR = result.resource
				# own CSR is still in remote CSE, so check for changes in remote CSE
				result = self._retrieveRemoteCSE() # retrieve the remote CSE
				self.registrarCSE = result.resource
				if result.rsc == RC.OK:
					if self.registrarCSE.isModifiedSince(localCSR):	# remote CSE modified
						self._updateLocalCSR(localCSR, self.registrarCSE)
						Logging.log('Local CSR updated')
				localCSE = Utils.getCSE().resource
				if localCSE.isModifiedSince(self.ownRemoteCSR):	# local CSE modified
					self._updateRemoteCSR(localCSE)
					Logging.log('Remote CSR updated')

			else:
				# Potential disconnect
				self._deleteLocalCSR(localCSR)	# ignore result
				result = self._createRemoteCSR()
				if result.rsc == RC.created:
					self.ownRemoteCSR = result.resource
					result = self._retrieveRemoteCSE()
					self.registrarCSE = result.resource
					if result.rsc == RC.OK:
						self._createLocalCSR(self.registrarCSE)		# TODO check result
						Logging.log('Remote CSE connected')
						CSE.event.registeredToRemoteCSE(self.registrarCSE, self.ownRemoteCSR)	# type: ignore
				else:
					Logging.log('Remote CSE disconnected')
					CSE.event.deregisteredFromRemoteCSE(self.ownRemoteCSR)	# type: ignore
					self.registrarCSE = None
			
		
		else:
			# No local CSR, so try to delete an optional remote one and re-create everything. 
			if self._deleteRemoteCSR().rsc in [ RC.deleted, RC.notFound ]:			# delete potential remote CSR
				result = self._createRemoteCSR()									# create remote CSR
				self.ownRemoteCSR = result.resource
				if result.rsc == RC.created:
					result = self._retrieveRemoteCSE()								# retrieve remote CSE
					self.registrarCSE = result.resource
					if result.rsc == RC.OK:
						self._createLocalCSR(self.registrarCSE) 					# TODO check result # create local CSR including ACPs to local CSR and local CSE
						Logging.log('Remote CSE connected')
						CSE.event.registeredToRemoteCSE(self.registrarCSE, self.ownRemoteCSR)	# type: ignore

						


	#	Check the liveliness of all remote CSE's that are connected to this CSE.
	#	This is done by trying to retrieve a remote CSR. If it cannot be retrieved
	#	then the related local CSR is removed.
	def _checkCSRLiveliness(self) -> None:
		for localCsr in self._retrieveLocalCSRs(own=False).lst:
			for url in (localCsr.poa or []):
				if Utils.isURL(url):
					if self._retrieveRemoteCSE(url='%s%s' % (url, localCsr.csi )).rsc != RC.OK:
						Logging.logWarn('Remote CSE unreachable. Removing CSR: %s' % localCsr.rn if localCsr is not None else '')
						self._deleteLocalCSR(localCsr)



	#
	#	Local CSR
	#

	def _retrieveLocalCSRs(self, csi:str=None, own:bool=True) -> Result:
		localCsrs = CSE.dispatcher.directChildResources(pi=self.cseRI, ty=T.CSR)
		if csi is None:
			csi = self.remoteCsi
		Logging.logDebug('Retrieving local CSR: %s' % csi)
		if own:
			for localCsr in localCsrs:
				if (c := localCsr.csi) is not None and c == csi:
					return Result(lst=[ localCsr ])
			return Result(rsc=RC.badRequest, dbg='local CSR not found')
		else:
			result = []
			for localCsr in localCsrs:
				if (c := localCsr.csi) is not None and c == csi:	# skip own
					continue
				result.append(localCsr)
			return Result(lst=result)


	def _createLocalCSR(self, remoteCSE: Resource) -> Result:
		Logging.logDebug('Creating local CSR: %s' % remoteCSE.ri)

		# copy local CSE attributes into a new CSR
		localCSE = Utils.getCSE().resource
		csr = CSR.CSR(pi=localCSE.ri, rn=remoteCSE.ri)	# remoteCSE.ri as name!
		self._copyCSE2CSR(csr, remoteCSE)
		csr['ri'] = remoteCSE.ri 						# set the ri to the remote CSE's ri
		# add local CSR and ACP's
		if (result := CSE.dispatcher.createResource(csr, localCSE)).resource is None:
			return result # Problem
		if not CSE.registration.handleCSRRegistration(csr, remoteCSE.csi):
			return Result(rsc=RC.badRequest, dbg='cannot register CSR')
		return CSE.dispatcher.updateResource(csr, doUpdateCheck=False)		# TODO dbupdate() instead?



	def _updateLocalCSR(self, localCSR:Resource, remoteCSE:Resource) -> Result:
		Logging.logDebug('Updating local CSR: %s' % localCSR.rn)
		# copy attributes
		self._copyCSE2CSR(localCSR, remoteCSE)
		return CSE.dispatcher.updateResource(localCSR)


	def _deleteLocalCSR(self, localCSR: Resource) -> Result:
		Logging.logDebug('Deleting local CSR: %s' % localCSR.ri)

		if not CSE.registration.handleCSRDeRegistration(localCSR):
			return Result(rsc=RC.badRequest, dbg='cannot deregister CSR')

		# Delete local CSR
		return CSE.dispatcher.deleteResource(localCSR)


	#
	#	Remote CSR 
	#

	def _retrieveRemoteCSR(self) -> Result:
		Logging.logDebug('Retrieving remote CSR: %s' % self.remoteCsi)
		result = CSE.httpServer.sendRetrieveRequest(self.remoteCSRURL, self.originator)
		if result.rsc not in [ RC.OK ]:
			return result.errorResult()
		return Result(resource=CSR.CSR(result.jsn, pi=''), rsc=RC.OK)


	def _createRemoteCSR(self) -> Result:
		Logging.logDebug('Creating remote CSR: %s' % self.remoteCsi)
		
		# get local CSEBase and copy relevant attributes
		localCSE = Utils.getCSE().resource
		csr = CSR.CSR(rn=localCSE.ri) # ri as name!
		self._copyCSE2CSR(csr, localCSE)
		csr['ri'] = self.cseCsi							# override ri with the own cseID
		#csr['cb'] = Utils.getIdFromOriginator(localCSE.csi)	# only the stem
		for _ in ['ty','ri', 'ct', 'lt']: csr.delAttribute(_, setNone=False)	# remove a couple of attributes
		#for _ in ['ty','ri', 'ct', 'lt']: del(csr[_])	# remove a couple of attributes
		data = json.dumps(csr.asJSON())

		# Create the <remoteCSE> in the remote CSE
		Logging.logDebug('Creating remote CSR at: %s url: %s' % (self.remoteCsi, self.remoteCSEURL))	
		res = CSE.httpServer.sendCreateRequest(self.remoteCSEURL, self.originator, ty=T.CSR, data=data)
		if res.rsc not in [ RC.created, RC.OK ]:
			if res.rsc != RC.alreadyExists:
				Logging.logDebug('Error creating remote CSR: %d' % res.rsc)
			return Result(rsc=res.rsc, dbg='cannot create remote CSR')
		Logging.logDebug('Remote CSR created: %s' % self.remoteCsi)

		return Result(resource=CSR.CSR(res.jsn, pi=''), rsc=RC.created)


	def _updateRemoteCSR(self, localCSE:Resource) -> Result:
		Logging.logDebug('Updating remote CSR: %s' % self.remoteCsi)
		csr = CSR.CSR()
		self._copyCSE2CSR(csr, localCSE)
		del csr['acpi']			# remove ACPI (don't provide ACPI in updates...a bit)
		data = json.dumps(csr.asJSON())

		res = CSE.httpServer.sendUpdateRequest(self.remoteCSRURL, self.originator, data=data)
		if res.rsc not in [ RC.updated, RC.OK ]:
			if res.rsc != RC.alreadyExists:
				Logging.logDebug('Error updating remote CSR: %d' % res.rsc)
			return Result(rsc=res.rsc, dbg='cannot update remote CSR')
		Logging.logDebug('Remote CSR updated: %s' % self.remoteCsi)

		return Result(resource=CSR.CSR(res.jsn, pi=''), rsc=RC.updated)



	def _deleteRemoteCSR(self) -> Result:
		Logging.logDebug('Deleting remote CSR: %s url: %s' % (self.remoteCsi, self.remoteCSRURL))
		res = CSE.httpServer.sendDeleteRequest(self.remoteCSRURL, self.originator)
		if res.rsc not in [ RC.deleted, RC.OK ]:
			return Result(rsc=res.rsc, dbg='cannot delete remote CSR')
		Logging.log('Remote CSR deleted: %s' % self.remoteCsi)
		return Result(rsc=RC.deleted)


	#
	#	Remote CSE
	#

	# Retrieve the remote CSE
	def _retrieveRemoteCSE(self, url:str=None) -> Result:
		url = (url or self.remoteCSEURL)
		Logging.logDebug('Retrieving remote CSE from: %s url: %s' % (self.remoteCsi, url))	
		res = CSE.httpServer.sendRetrieveRequest(url, self.originator)
		if res.rsc not in [ RC.OK ]:
			return res.errorResult()
		return Result(resource=CSEBase.CSEBase(res.jsn), rsc=RC.OK)


	def getCSRForRemoteCSE(self, remoteCSE:Resource) -> Resource:
		if self.registrarCSE is not None and self.registrarCSE.csi == remoteCSE.csi:
			return self.ownRemoteCSR

		# if self.registrarCSE is not None and self.registrarCSE.csi == remoteCSE.csi:
		# 	return self.registrarCSE
		for csi,csr in self.descendantCSR.items():	# search the list of descendant CSR
			if csr.ri == remoteCSE.ri:
				return csr
		return None


	def getAllLocalCSRs(self) -> List[Resource]:
		"""	Return all local CSR's.
		"""
		result = list(self.descendantCSR.values())
		result.append(self.ownRemoteCSR)
		return result


	#########################################################################

	#
	#	Handling of Transit requests. Forward requests to the resp. remote CSE's.
	#

	def handleTransitRetrieveRequest(self, request: Request, id: str, origin: str) -> Result:
		""" Forward a RETRIEVE request to a remote CSE """
		if (url := self._getForwardURL(id)) is None:
			return Result(rsc=RC.notFound, dbg='forward URL not found for id: %s' % id)
		if len(request.args) > 0:	# pass on other arguments, for discovery
			url += '?' + urllib.parse.urlencode(request.args)
		Logging.log('Forwarding Retrieve/Discovery request to: %s' % url)
		return CSE.httpServer.sendRetrieveRequest(url, origin)


	def handleTransitCreateRequest(self, request: Request, id: str, origin: str, ty: T) -> Result:
		""" Forward a CREATE request to a remote CSE. """
		if (url := self._getForwardURL(id)) is None:
			return Result(rsc=RC.notFound, dbg='forward URL not found for id: %s' % id)
		Logging.log('Forwarding Create request to: %s' % url)
		return CSE.httpServer.sendCreateRequest(url, origin, data=request.data, ty=ty)


	def handleTransitUpdateRequest(self, request: Request, id: str, origin: str) -> Result:
		""" Forward an UPDATE request to a remote CSE. """
		if (url := self._getForwardURL(id)) is None:
			return Result(rsc=RC.notFound, dbg='forward URL not found for id: %s' % id)
		Logging.log('Forwarding Update request to: %s' % url)
		return CSE.httpServer.sendUpdateRequest(url, origin, data=request.data)


	def handleTransitDeleteRequest(self, id:str, origin:str) -> Result:
		""" Forward a DELETE request to a remote CSE. """
		if (url := self._getForwardURL(id)) is None:
			return Result(rsc=RC.notFound, dbg='forward URL not found for id: %s' % id)
		Logging.log('Forwarding Delete request to: %s' % url)
		return CSE.httpServer.sendDeleteRequest(url, origin)


	def retrieveRemoteResource(self, id:str, originator:str=None, raw:bool=False) -> Result:
		"""	Retrieve a resource from a remote CSE. If 'raw' is True then no resource
			object is created, but the raw content from the retrieval is returned.
		"""
		if (url := self._getForwardURL(id)) is None:
			return Result(rsc=RC.notFound, dbg='URL not found for id: %s' % id)
		if originator is None:
			originator = self.cseCsi
		Logging.log('Retrieve remote resource from: %s' % url)
		res = CSE.httpServer.sendRetrieveRequest(url, originator)
		if res.rsc != RC.OK:
			return res.errorResult()
		return Utils.resourceFromJSON(res.jsn) if not raw else Result(resource=res.jsn)


	def isTransitID(self, id:str) -> bool:
		""" Check whether an ID is a targeting a remote CSE via a CSR. """
		if Utils.isSPRelative(id):
			ids = id.split("/")
			return len(ids) > 0 and ids[0] != self.cseCsi[1:]
		elif Utils.isAbsolute(id):
			ids = id.split("/")
			return len(ids) > 2 and ids[2] != self.cseCsi[1:]
		return False


	def _getForwardURL(self, path:str) -> str:
		""" Get the new target URL when forwarding. """
		r, pe = self._getCSRFromPath(path)
		if r is not None and (poas := r.poa) is not None and len(poas) > 0:
			return '%s/~/%s' % (poas[0], '/'.join(pe[1:]))	# TODO check all available poas.
		return None


	def _getCSRFromPath(self, id:str) -> Tuple[Resource, List[str]]:
		""" Try to get a CSR even from a longer path (only the first 2 path elements are relevant). """
		if id is None:
			return None, None
		ids = id.split("/")
		Logging.logDebug("CSR ids: %s" % ids)
		if Utils.isSPRelative(id):
			resource = CSE.dispatcher._retrieveResource(ri=ids[1]).resource
		elif Utils.isAbsolute(id):
			resource = CSE.dispatcher._retrieveResource(ri=ids[2]).resource
		else:
			resource = CSE.dispatcher._retrieveResource(ri=id).resource
		return resource, ids


	#########################################################################


	def _copyCSE2CSR(self, target:Resource, source:Resource, isUpdate:bool=False) -> None:
		if isUpdate:
			# rm some attributes
			if 'ri' in target:
				target.delAttribute('ri', setNone = False)
			if 'rn' in target:
				target.delAttribute('rn', setNone = False)
			if 'ct' in target:
				target.delAttribute('ct', setNone = False)
			if 'ty' in target:
				target.delAttribute('ty', setNone = False)


		if 'csb' in source:
			target['csb'] = self.remoteCSEURL
		if 'csi' in source:
			target['csi'] = source.csi
		if 'cst' in source:
			target['cst'] = source.cst
		if 'csz' in source:
			target['csz'] = source.csz
		if 'lbl' in source:
			target['lbl'] = source.lbl
		if 'nl' in source:
			target['nl'] = source.nl
		if 'poa' in source:
			target['poa'] = source.poa
		# if 'rn' in source:
		# 	target['rn'] = source.rn
		if 'rr' in source:
			target['rr'] = source.rr
		# if 'srt' in source:
		# 	target['srt'] = source.srt
		if 'srv' in source:
			target['srv'] = source.srv
		if 'st' in source:
			target['st'] = source.st
		
		target['cb'] = Utils.getIdFromOriginator(source.csi)	# only the stem
		target['dcse'] = list(self.descendantCSR.keys())
		target.delAttribute('acpi', setNone = False)	# remove ACPI (don't provide ACPI in updates...a bit)


