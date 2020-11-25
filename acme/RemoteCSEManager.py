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
from Configuration import Configuration
from Logging import Logging
from Constants import Constants as C
from Types import ResourceTypes as T, Result, CSEType, ResponseCode as RC, CSERequest
import Utils, CSE
from resources import CSR, CSEBase
from resources.Resource import Resource
from helpers.BackgroundWorker import BackgroundWorkerPool


class RemoteCSEManager(object):

	def __init__(self) -> None:
		self.csetype 							= Configuration.get('cse.type')
		self.isConnected 						= False
		self.remoteAddress						= Configuration.get('cse.registrar.address')
		self.remoteRoot 						= Configuration.get('cse.registrar.root')
		self.registrarCSI						= Configuration.get('cse.registrar.csi')
		self.registrarCseRN						= Configuration.get('cse.registrar.rn')
		self.originator							= Configuration.get('cse.csi')	# Originator is the own CSE-ID
		self.cseCsi								= Configuration.get('cse.csi')
		self.cseRI								= Configuration.get('cse.ri')
		self.checkInterval						= Configuration.get('cse.registrar.checkInterval')
		self.checkLiveliness					= Configuration.get('cse.registration.checkLiveliness')
		self.registrarCSEURL					= f'{self.remoteAddress}{self.remoteRoot}/~{self.registrarCSI}/{self.registrarCseRN}'
		self.registrarCSRURL					= f'{self.registrarCSEURL}{self.cseCsi}'
		self.ownRegistrarCSR:Resource			= None 	# The own CSR at the registrar if there is one
		self.registrarCSE:Resource				= None 	# The registrar CSE if there is one
		self.descendantCSR:Dict[str, Tuple[Resource, str]]	= {}	# dict of descendantCSR's . csi : (CSR, registeredATcsi)


		CSE.event.addHandler(CSE.event.registeredToRemoteCSE, self.handleRegistrarRegistration)				# type: ignore
		CSE.event.addHandler(CSE.event.deregisteredFromRemoteCSE, self.handleRegistrarDeregistration)		# type: ignore
		CSE.event.addHandler(CSE.event.remoteCSEHasRegistered, self.handleRemoteCSERegistration)			# type: ignore
		CSE.event.addHandler(CSE.event.remoteCSEHasDeregistered, self.handleRemoteCSEDeregistration)		# type: ignore
		CSE.event.addHandler(CSE.event.remoteCSEUpdate, self.handleRemoteCSEUpdate)							# type: ignore

		self.start()
		Logging.log('RemoteCSEManager initialized')


	def shutdown(self) -> bool:
		self.stop()
		Logging.log('RemoteCSEManager shut down')
		return True


	#
	#	Connection Monitor
	#

	# Start the monitor in a thread. 
	def start(self) -> None:
		if not Configuration.get('cse.enableRemoteCSE'):
			return
		Logging.log('Starting remote CSE connection monitor')
		BackgroundWorkerPool.newWorker(self.checkInterval, self.connectionMonitorWorker, 'csrMonitor').start()


	# Stop the monitor. Also delete the CSR resources on both sides
	def stop(self) -> None:
		if not Configuration.get('cse.enableRemoteCSE'):
			return
		Logging.log('Stopping remote CSE connection monitor')

		# Stop the worker
		BackgroundWorkerPool.stopWorkers('csrMonitor')

		# Remove resources
		if self.csetype in [ CSEType.ASN, CSEType.MN ]:
			self._deleteCSRonRegistrarCSE()	# delete remote CSR. Ignore result
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
		try:

			# Check the current state of the connection to the "upstream" CSEs
			if self.csetype in [ CSEType.ASN, CSEType.MN ]:

				# when validateRegistrations == False then only check when there is no connection
				if not self.checkLiveliness:
					if (r := self._retrieveLocalCSRs(own=True)).lst is not None and len(r.lst) == 1:
						return True
			
				# Check the connection to the registrar CSE and establish one if necessary
				Logging.logDebug('Checking connection to registrar CSE')

				self._checkOwnConnection()

			# Check the liveliness of other CSR connections
			# Only when we validate the registrations
			if self.csetype in [ CSEType.MN, CSEType.IN ]:
				if  self.checkLiveliness:	
					Logging.logDebug('Checking connections to registree CSEs')
					self._checkCSRLiveliness()

		except Exception as e:
			Logging.logErr(f'Exception: {e}')
			import traceback
			Logging.logErr(traceback.format_exc())
			return True
		return True


	#########################################################################
	#
	#	Event Handlers
	#

	def handleRegistrarRegistration(self, registrarCSE:Resource, ownRegistrarCSR:Resource) -> None:
		"""	Add the CSE/CSR CSI to the list of registered CSI. """
		self.registrarCSE = registrarCSE
		self.ownRegistrarCSR = ownRegistrarCSR


	def handleRegistrarDeregistration(self, remoteCSR:Resource = None) -> None:
		"""	Remove the CSE/CSR CSI from the list of registered CSI. """
		self.registrarCSE = None
		self.ownRegistrarCSR = None


	def handleRemoteCSERegistration(self, remoteCSR:Resource) -> None:
		"""	Add the the remote CSE's CSR CSI to the list of registered CSI. """
		if (csi := remoteCSR.csi) is None:
			return
		if csi in self.descendantCSR:	# already registered
			return
		# don't register registrar CSE here
		if (rcse := self.registrarCSE) is not None and (rcsi := rcse.csi) is not None and rcsi == csi:
			return

		# Add the descendants
		self.descendantCSR[csi] = (remoteCSR, csi)
		if remoteCSR.dcse is not None:			# add also this csi from the dcse attribute
			for dcsecsi in remoteCSR.dcse:
				if dcsecsi in self.descendantCSR:	# don't overwrite existing ones
					continue
				self.descendantCSR[dcsecsi] = (None, csi)

		Logging.logDebug(f'Descendant CSE registered {csi}')
		# localCSE = Utils.getCSE().resource
		# dcse = []
		# for csi in self.descendantCSR:
		# 	if self.registrarCSE is None or (self.registrarCSE is not None and csi != self.registrarCSE.csi):
		# 		dcse.append(csi)
		# localCSE['dcse'] = dcse
		# localCSE.dbUpdate()	# update in DB
		if self.csetype in [ CSEType.ASN, CSEType.MN ]:
			self._updateCSRonRegistrarCSE()


	def handleRemoteCSEDeregistration(self, remoteCSR:Resource ) -> None:
		"""	Remove the CSE/CSR CSI from the list of registered CSI. """
		if (csi := remoteCSR.csi) is not None and csi in self.descendantCSR:
			del self.descendantCSR[csi]
		if self.csetype in [ CSEType.ASN, CSEType.MN ]:
			self._updateCSRonRegistrarCSE()


	def handleRemoteCSEUpdate(self, remoteCSR:Resource) -> None:
		# handle update of dcse in remoteCSR
		csi = remoteCSR.csi
		# remove all descendant tuples that are from this CSR
		for key in self.descendantCSR.keys():
			(_, hostedcsi) = self.descendantCSR[key]
			if hostedcsi == csi:
				del self.descendantCSR[hostedcsi]

		# add new/updated values from remoteCSR
		if remoteCSR.dcse is not None:		# TODO same as above. Function?
			for dcsecsi in remoteCSR.dcse:
				if dcsecsi in self.descendantCSR:	# don't overwrite existing ones
					continue
				self.descendantCSR[dcsecsi] = (None, csi)


		if self.csetype in [ CSEType.ASN, CSEType.MN ]:	# update own registrar CSR
			self._updateCSRonRegistrarCSE()



	#########################################################################

	# def _removeRegisteredCSE(self, resource:Resource) -> None:
	# 	if resource is None:	# If own registrar
	# 		self.registeredCSIs.remove(self.registrarCSI)	# 	else:
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
			localCSR = res.lst[0] # hopefully, there is only one registrar CSR
			result = self._retrieveCSRfromRegistrarCSE()	# retrieve own from the remote CSE
			if result.rsc == RC.OK:
				self.ownRegistrarCSR = result.resource
				# own CSR is still in remote CSE, so check for changes in remote CSE
				result = self._retrieveRemoteCSE() # retrieve the remote CSE
				self.registrarCSE = result.resource
				if result.rsc == RC.OK:
					if self.registrarCSE.isModifiedSince(localCSR):	# remote CSE modified
						self._updateLocalCSR(localCSR, self.registrarCSE)
						Logging.log('Local CSR updated')
				localCSE = Utils.getCSE().resource
				if localCSE.isModifiedSince(self.ownRegistrarCSR):	# local CSE modified
					self._updateCSRonRegistrarCSE(localCSE)
					Logging.log('Remote CSR updated')

			else:
				# Potential disconnect
				self._deleteLocalCSR(localCSR)	# ignore result
				result = self._createCSRonRegistrarCSE()
				if result.rsc == RC.created:
					self.ownRegistrarCSR = result.resource
					result = self._retrieveRemoteCSE()
					self.registrarCSE = result.resource
					if result.rsc == RC.OK:
						self._createLocalCSR(self.registrarCSE)		# TODO check result
						Logging.log('Remote CSE connected')
						CSE.event.registeredToRemoteCSE(self.registrarCSE, self.ownRegistrarCSR)	# type: ignore
				else:
					Logging.log('Remote CSE disconnected')
					CSE.event.deregisteredFromRemoteCSE(self.ownRegistrarCSR)	# type: ignore
					self.registrarCSE = None
			
		
		else:
			# No local CSR, so try to delete an optional remote one and re-create everything. 
			if self._deleteCSRonRegistrarCSE().rsc in [ RC.deleted, RC.notFound ]:			# delete potential remote CSR
				result = self._createCSRonRegistrarCSE()									# create remote CSR
				self.ownRegistrarCSR = result.resource
				if result.rsc == RC.created:
					result = self._retrieveRemoteCSE()								# retrieve remote CSE
					self.registrarCSE = result.resource
					if result.rsc == RC.OK:
						self._createLocalCSR(self.registrarCSE) 					# TODO check result # create local CSR including ACPs to local CSR and local CSE
						Logging.log('Remote CSE connected')
						CSE.event.registeredToRemoteCSE(self.registrarCSE, self.ownRegistrarCSR)	# type: ignore

						


	#	Check the liveliness of all remote CSE's that are connected to this CSE.
	#	This is done by trying to retrieve a remote CSR. If it cannot be retrieved
	#	then the related local CSR is removed.
	def _checkCSRLiveliness(self) -> None:
		for localCsr in self._retrieveLocalCSRs(own=False).lst:
			for url in (localCsr.poa or []):
				if Utils.isURL(url):
					if self._retrieveRemoteCSE(url=f'{url}{localCsr.csi}').rsc != RC.OK:
						Logging.logWarn(f'Remote CSE unreachable. Removing CSR: {localCsr.rn if localCsr is not None else ""}')
						self._deleteLocalCSR(localCsr)



	#
	#	Local CSR
	#

	def _retrieveLocalCSRs(self, csi:str=None, own:bool=True) -> Result:
		localCsrs = CSE.dispatcher.directChildResources(pi=self.cseRI, ty=T.CSR)
		if csi is None:
			csi = self.registrarCSI
		# Logging.logDebug(f'Retrieving local CSR: {csi}')
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
		Logging.logDebug('Creating local CSR: {remoteCSE.ri}')

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
		Logging.logDebug(f'Updating local CSR: {localCSR.rn}')
		# copy attributes
		self._copyCSE2CSR(localCSR, remoteCSE)
		return CSE.dispatcher.updateResource(localCSR)


	def _deleteLocalCSR(self, localCSR: Resource) -> Result:
		Logging.logDebug(f'Deleting local CSR: {localCSR.ri}')

		if not CSE.registration.handleCSRDeRegistration(localCSR):
			return Result(rsc=RC.badRequest, dbg='cannot deregister CSR')

		# Delete local CSR
		return CSE.dispatcher.deleteResource(localCSR)


	#
	#	Remote Registrar CSR 
	#

	def _retrieveCSRfromRegistrarCSE(self) -> Result:
		Logging.logDebug(f'Retrieving remote CSR: {self.registrarCSI}')
		result = CSE.httpServer.sendRetrieveRequest(self.registrarCSRURL, self.originator)
		if result.rsc not in [ RC.OK ]:
			return result.errorResult()
		return Result(resource=CSR.CSR(result.jsn, pi=''), rsc=RC.OK)


	def _createCSRonRegistrarCSE(self) -> Result:
		Logging.logDebug(f'Creating registrar CSR: {self.registrarCSI}')		
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
		Logging.logDebug(f'Creating registrar CSR at: {self.registrarCSI} url: {self.registrarCSEURL}')	
		res = CSE.httpServer.sendCreateRequest(self.registrarCSEURL, self.originator, ty=T.CSR, data=data)
		if res.rsc not in [ RC.created, RC.OK ]:
			if res.rsc != RC.alreadyExists:
				Logging.logDebug(f'Error creating registrar CSR: {res.rsc:d}')
			return Result(rsc=res.rsc, dbg='cannot create remote CSR')
		Logging.logDebug(f'Registrar CSR created: {self.registrarCSI}')
		return Result(resource=CSR.CSR(res.jsn, pi=''), rsc=RC.created)


	def _updateCSRonRegistrarCSE(self, localCSE:Resource=None) -> Result:
		Logging.logDebug(f'Updating registrar CSR in CSE: {self.registrarCSI}')
		if localCSE is None:
			localCSE = Utils.getCSE().resource
		csr = CSR.CSR()
		self._copyCSE2CSR(csr, localCSE, isUpdate=True)
		del csr['acpi']			# remove ACPI (don't provide ACPI in updates...a bit)
		data = json.dumps(csr.asJSON())

		res = CSE.httpServer.sendUpdateRequest(self.registrarCSRURL, self.originator, data=data)
		if res.rsc not in [ RC.updated, RC.OK ]:
			if res.rsc != RC.alreadyExists:
				Logging.logDebug(f'Error updating registrar CSR in CSE: {res.rsc:d}')
			return Result(rsc=res.rsc, dbg='cannot update remote CSR')
		Logging.logDebug(f'Registrar CSR updated in CSE: {self.registrarCSI}')
		return Result(resource=CSR.CSR(res.jsn, pi=''), rsc=RC.updated)



	def _deleteCSRonRegistrarCSE(self) -> Result:
		Logging.logDebug(f'Deleting registrar CSR: {self.registrarCSI} url: {self.registrarCSRURL}')
		res = CSE.httpServer.sendDeleteRequest(self.registrarCSRURL, self.originator)
		if res.rsc not in [ RC.deleted, RC.OK ]:
			return Result(rsc=res.rsc, dbg='cannot delete registrar CSR')
		Logging.log(f'Registrar CSR deleted: {self.registrarCSI}')
		return Result(rsc=RC.deleted)


	#
	#	Remote CSE
	#

	# Retrieve the remote CSE
	def _retrieveRemoteCSE(self, url:str=None) -> Result:
		url = (url or self.registrarCSEURL)
		Logging.logDebug(f'Retrieving remote CSE from: {self.registrarCSI} url: {url}')	
		res = CSE.httpServer.sendRetrieveRequest(url, self.originator)
		if res.rsc not in [ RC.OK ]:
			return res.errorResult()
		return Result(resource=CSEBase.CSEBase(res.jsn), rsc=RC.OK)


	def getCSRForRemoteCSE(self, remoteCSE:Resource) -> Resource:
		if self.registrarCSE is not None and self.registrarCSE.csi == remoteCSE.csi:
			return self.ownRegistrarCSR

		# if self.registrarCSE is not None and self.registrarCSE.csi == remoteCSE.csi:
		# 	return self.registrarCSE
		for csi,tup in self.descendantCSR.items():	# search the list of descendant CSR
			(csr, _) = tup
			if csr.ri == remoteCSE.ri:
				return csr
		return None


	def getAllLocalCSRs(self) -> List[Resource]:
		"""	Return all local CSR's.
		"""
		result = [ csr for (csr, _) in self.descendantCSR.values() if csr is not None ]
		#result = list(self.descendantCSR.values())
		result.append(self.ownRegistrarCSR)
		return result


	#########################################################################

	#
	#	Handling of Transit requests. Forward requests to the resp. remote CSE's.
	#

	def handleTransitRetrieveRequest(self, request:CSERequest) -> Result:
		""" Forward a RETRIEVE request to a remote CSE """
		if (url := self._getForwardURL(request.id)) is None:
			return Result(rsc=RC.notFound, dbg=f'forward URL not found for id: {id}')
		if len(request.originalArgs) > 0:	# pass on other arguments, for discovery
			url += '?' + urllib.parse.urlencode(request.originalArgs)
		Logging.log(f'Forwarding Retrieve/Discovery request to: {url}')
		return CSE.httpServer.sendRetrieveRequest(url, request.headers.originator)


	def handleTransitCreateRequest(self, request:CSERequest) -> Result:
		""" Forward a CREATE request to a remote CSE. """
		if (url := self._getForwardURL(request.id)) is None:
			return Result(rsc=RC.notFound, dbg=f'forward URL not found for id: {id}')
		if len(request.originalArgs) > 0:	# pass on other arguments, for discovery
			url += '?' + urllib.parse.urlencode(request.originalArgs)
		Logging.log(f'Forwarding Create request to: {url}')
		return CSE.httpServer.sendCreateRequest(url, request.headers.originator, data=request.data, ty=request.headers.resourceType)


	def handleTransitUpdateRequest(self, request:CSERequest) -> Result:
		""" Forward an UPDATE request to a remote CSE. """
		if (url := self._getForwardURL(request.id)) is None:
			return Result(rsc=RC.notFound, dbg=f'forward URL not found for id: {id}')
		if len(request.originalArgs) > 0:	# pass on other arguments, for discovery
			url += '?' + urllib.parse.urlencode(request.originalArgs)
		Logging.log(f'Forwarding Update request to: {url}')
		return CSE.httpServer.sendUpdateRequest(url, request.headers.originator, data=request.data)


	def handleTransitDeleteRequest(self, request:CSERequest) -> Result:
		""" Forward a DELETE request to a remote CSE. """
		if (url := self._getForwardURL(request.id)) is None:
			return Result(rsc=RC.notFound, dbg=f'forward URL not found for id: {id}')
		if len(request.originalArgs) > 0:	# pass on other arguments, for discovery
			url += '?' + urllib.parse.urlencode(request.originalArgs)
		Logging.log(f'Forwarding Delete request to: {url}')
		return CSE.httpServer.sendDeleteRequest(url, request.headers.originator)


	def retrieveRemoteResource(self, id:str, originator:str=None, raw:bool=False) -> Result:
		"""	Retrieve a resource from a remote CSE. If 'raw' is True then no resource
			object is created, but the raw content from the retrieval is returned.
		"""
		if (url := self._getForwardURL(id)) is None:
			return Result(rsc=RC.notFound, dbg=f'URL not found for id: {id}')
		if originator is None:
			originator = self.cseCsi
		Logging.log('Retrieve remote resource from: {url}')
		res = CSE.httpServer.sendRetrieveRequest(url, originator)
		if res.rsc != RC.OK:
			return res.errorResult()
		return Utils.resourceFromJSON(res.jsn) if not raw else Result(resource=res.jsn)


	def isTransitID(self, id:str) -> bool:
		""" Check whether an ID is a targeting a remote CSE via a CSR. """
		if Utils.isSPRelative(id):
			ids = id.split('/')
			return len(ids) > 0 and ids[0] != self.cseCsi[1:]
		elif Utils.isAbsolute(id):
			ids = id.split('/')
			return len(ids) > 2 and ids[2] != self.cseCsi[1:]
		return False


	def _getForwardURL(self, path:str) -> str:
		""" Get the new target URL when forwarding. """
		r, pe = self._getCSRFromPath(path)
		if r is not None and (poas := r.poa) is not None and len(poas) > 0:
			return f'{poas[0]}/~/{"/".join(pe[1:])}'	# TODO check all available poas.
		return None


	def _getCSRFromPath(self, id:str) -> Tuple[Resource, List[str]]:
		""" Try to get a CSR even from a longer path (only the first 2 path elements are relevant). """
		if id is None:
			return None, None
		ids = id.split('/')
		Logging.logDebug(f'CSR ids: {ids}')
		if Utils.isSPRelative(id):
			resource = CSE.dispatcher.retrieveLocalResource(ri=ids[1]).resource
		elif Utils.isAbsolute(id):
			resource = CSE.dispatcher.retrieveLocalResource(ri=ids[2]).resource
		else:
			resource = CSE.dispatcher.retrieveLocalResource(ri=id).resource
		return resource, ids


	#########################################################################


	def _copyCSE2CSR(self, target:Resource, source:Resource, isUpdate:bool=False) -> None:



		if 'csb' in source:
			target['csb'] = self.registrarCSEURL
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
		

		target['cb'] = f'{source.csi}/{source.rn}'
		target['dcse'] = list(self.descendantCSR.keys())		# Always do this bc it might be different, even empty for an update
		target.delAttribute('acpi', setNone = False)	# remove ACPI (don't provide ACPI in updates...a bit)

		if isUpdate:
			# rm some attributes
			for attr in [ 'ri', 'rn', 'ct', 'lt', 'ty', 'cst', 'cb', 'csi']:
				if attr in target:
					target.delAttribute(attr, setNone = False)

