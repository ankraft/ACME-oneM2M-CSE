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


from typing import List, Tuple, Dict, cast
from ..etc.Types import CSEStatus, ResourceTypes as T, Result, CSEType, ResponseStatusCode as RC, JSON
from ..etc import Utils as Utils
from ..resources import CSR, CSEBase
from ..resources.Resource import Resource
from ..resources import Factory as Factory
from ..services.Configuration import Configuration
from ..services.Logging import Logging as L
from ..services import CSE
from ..helpers.BackgroundWorker import BackgroundWorker, BackgroundWorkerPool


class RemoteCSEManager(object):

	def __init__(self) -> None:
		self.remoteAddress						= Configuration.get('cse.registrar.address')
		self.remoteRoot 						= Configuration.get('cse.registrar.root')
		self.checkInterval						= Configuration.get('cse.registrar.checkInterval')
		self.registrarSerialization				= Configuration.get('cse.registrar.serialization')
		self.checkLiveliness					= Configuration.get('cse.registration.checkLiveliness')
		self.registrarCSI						= Configuration.get('cse.registrar.csi')
		self.registrarCseRN						= Configuration.get('cse.registrar.rn')
		self.registrarCSEURL					= f'{self.remoteAddress}{self.remoteRoot}/{self.registrarCSI}/{self.registrarCseRN}'
		self.registrarCSRURL					= f'{self.registrarCSEURL}{CSE.cseCsi}'
		self.excludeCSRAttributes				= Configuration.get('cse.registrar.excludeCSRAttributes')
		self.ownCSRonRegistrar:Resource			= None 	# The own CSR at the registrar if there is one
		self.registrarCSE:Resource				= None 	# The registrar CSE if there is one
		self.descendantCSR:Dict[str, Tuple[Resource, str]]	= {}	# dict of descendantCSR's - "csi : (CSR, registeredATcsi)". CSR is None for CSEs further down 
		self.enableRemoteCSE				 	= Configuration.get('cse.enableRemoteCSE')

		self.connectionMonitor:BackgroundWorker	= None	# BackgroundWorker

		CSE.event.addHandler(CSE.event.registeredToRemoteCSE, self.handleRegistrarRegistration)				# type: ignore
		CSE.event.addHandler(CSE.event.deregisteredFromRemoteCSE, self.handleRegistrarDeregistration)		# type: ignore
		CSE.event.addHandler(CSE.event.remoteCSEHasRegistered, self.handleRemoteCSERegistration)			# type: ignore
		CSE.event.addHandler(CSE.event.remoteCSEHasDeregistered, self.handleRemoteCSEDeregistration)		# type: ignore
		CSE.event.addHandler(CSE.event.remoteCSEUpdate, self.handleRemoteCSEUpdate)							# type: ignore

		# Add a handler when the CSE is started
		CSE.event.addHandler(CSE.event.cseStartup, self.start)	# type: ignore
		L.isInfo and L.log('RemoteCSEManager initialized')


	def shutdown(self) -> bool:
		self.stop()
		L.isInfo and L.log('RemoteCSEManager shut down')
		return True


	def restart(self) -> None:
		"""	Restart the remote service.
		"""
		if self.connectionMonitor:
			self.connectionMonitor.workNow()
		L.isDebug and L.logDebug('RemoteManager restarted')


	#
	#	Connection Monitor
	#

	# Start the monitor in a thread. 
	def start(self) -> None:
		if not self.enableRemoteCSE:
			return
		
		L.isDebug and L.logDebug('Rebuild internal descendants list')
		self.descendantCSR.clear()
		for csr in CSE.dispatcher.retrieveResourcesByType(T.CSR):
			if (csi := csr.csi) != self.registrarCSI:			# Skipping the own registrar csr
				L.isDebug and L.logDebug(f'Addind remote CSE: {csi}')
				self.descendantCSR[csi] = (csr, CSE.cseCsi)		# Add the direct child CSR
				if csr.dcse:
					for dcse in csr.dcse:							# Add the descendant CSE's
						L.isDebug and L.logDebug(f'Adding descendant CSE: {csi} -> {dcse}')
						self.descendantCSR[dcse] = (None, csi)


		L.isInfo and L.log('Starting remote CSE connection monitor')
		self.connectionMonitor = BackgroundWorkerPool.newWorker(self.checkInterval, self.connectionMonitorWorker, 'csrMonitor').start()


	# Stop the monitor. Also delete the CSR resources on both sides
	def stop(self) -> None:
		if not self.enableRemoteCSE:
			return
		L.isInfo and L.log('Stopping remote CSE connection monitor')

		# Stop the worker
		if self.connectionMonitor:
			self.connectionMonitor.stop()
			self.connectionMonitor = None

		# Remove resources
		if CSE.cseType in [ CSEType.ASN, CSEType.MN ]:
			self._deleteOwnCSRonRegistrarCSE()	# delete remote CSR. Ignore result
		res = self._retrieveLocalCSRs()	# retrieve local CSR of the registrar
		if res.rsc == RC.OK:
			L.isDebug and L.logDebug('Deleting local registrar CSR ')
			self._deleteLocalCSR(cast(List, res.data)[0])		# delete local CSR of the registrar


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
		if CSE.cseStatus != CSEStatus.RUNNING:
			return True
		try:

			# Check the current state of the connection to the "upstream" CSEs
			if CSE.cseType in [ CSEType.ASN, CSEType.MN ]:

				# when validateRegistrations == False then only check when there is no connection
				if not self.checkLiveliness:
					if (r := self._retrieveLocalCSRs(onlyOwn = True)).data and len(r.data) == 1:
						return True
			
				# Check the connection to the registrar CSE and establish one if necessary
				L.isDebug and L.logDebug('Checking connection to registrar CSE')

				self._checkConnectionToRegistrarCSE()

			# Check the liveliness of other CSR connections
			# Only when we validate the registrations
			if CSE.cseType in [ CSEType.MN, CSEType.IN ]:
				if  self.checkLiveliness:	
					self._checkCSRLiveliness()

		except Exception as e:
			L.logErr(f'Exception: {e}')
			import traceback
			L.logErr(traceback.format_exc())
			return True
		return True


	#########################################################################
	#
	#	Event Handlers
	#

	def handleRegistrarRegistration(self, registrarCSE:Resource, ownRegistrarCSR:Resource) -> None:
		""" Event handler for adding a CSE/CSR CSI to the list
			of registered CSI. 
		"""
		self.registrarCSE = registrarCSE
		self.ownCSRonRegistrar = ownRegistrarCSR


	def handleRegistrarDeregistration(self, remoteCSR:Resource = None) -> None:
		"""	Event handler for removing the CSE/CSR CSI from the list
			of registered CSI.
		"""
		self.registrarCSE = None
		self.ownCSRonRegistrar = None


	def handleRemoteCSERegistration(self, remoteCSR:Resource) -> None:
		"""	Event handler for adding a remote CSE's CSR CSI to the
			list of registered CSI. 
		"""
		if not (csi := remoteCSR.csi):
			return
		if csi in self.descendantCSR:	# already registered
			return
		# don't register registrar CSE here
		if (rcse := self.registrarCSE) and (rcsi := rcse.csi) and rcsi == csi:
			return

		# Add the descendants
		self.descendantCSR[csi] = (remoteCSR, CSE.cseCsi)
		if remoteCSR.dcse:			# add also this csi from the dcse attribute
			for dcsecsi in remoteCSR.dcse:
				if dcsecsi in self.descendantCSR:	# don't overwrite existing ones
					continue
				self.descendantCSR[dcsecsi] = (None, csi)

		L.isDebug and L.logDebug(f'Descendant CSE registered {csi}')
		if CSE.cseType in [ CSEType.ASN, CSEType.MN ]:
			self._updateCSRonRegistrarCSE()


	def handleRemoteCSEDeregistration(self, remoteCSR:Resource ) -> None:
		"""	Event handler for removals of the CSE/CSR CSI
			from the list of registered CSI. 
		"""
		L.isDebug and L.logDebug(f'Handling de-registration of remote CSE: {remoteCSR.csi}')
		# Remove the deregistering CSE from the descendant list
		if (csi := remoteCSR.csi) and csi in self.descendantCSR:
			del self.descendantCSR[csi]
		# Also remove all descendants that are refer to that remote CSE
		for key in list(self.descendantCSR):	# List might change in the loop
			dcse = self.descendantCSR[key]
			if dcse[1] == csi:	# registered to deregistering remote CSE?
				del self.descendantCSR[key]
		
		if CSE.cseType in [ CSEType.ASN, CSEType.MN ] and remoteCSR.csi != self.registrarCSI:	# No need to update the own CSR on the registrar when deregistering anyway
			self._updateCSRonRegistrarCSE()


	def handleRemoteCSEUpdate(self, remoteCSR:Resource, updateDict:JSON) -> None:
		"""	Event handler for updates of the remote CSE.
		"""
		L.isDebug and L.logDebug(f'Handle remote CSE update: {remoteCSR}\nupdate: {updateDict}')

		# handle update of dcse in remoteCSR
		remoteCsi = remoteCSR.csi
		L.isDebug and L.logDebug(f'DescendantCSRs: {self.descendantCSR}')
		# remove all descendant tuples that are from this CSR
		for key in list(self.descendantCSR.keys()):	# !!! make a copy of the keys bc the list changes in this loop
			if key in self.descendantCSR:	# Entry could have been deleted, nevertheless
				(_, registeredATcsi) = self.descendantCSR[key]
				if registeredATcsi == remoteCsi :	# remove all descedants EXCEPT the ones hosted on THIS CSE
					L.isDebug and L.logDebug(f'Removing from internal dcse list: {key}')
					del self.descendantCSR[key]

		# add new/updated values from remoteCSR
		if dcse := Utils.findXPath(updateDict, 'm2m:csr/dcse'):		# TODO same as above. Function?
			for dcsecsi in dcse:
				if dcsecsi in self.descendantCSR:	# don't overwrite existing ones
					continue
				self.descendantCSR[dcsecsi] = (None, remoteCsi)	# don't have the CSR for further descendants available

		if CSE.cseType in [ CSEType.ASN, CSEType.MN ]:	# update own registrar CSR
			self._updateCSRonRegistrarCSE()



	#########################################################################
	#
	#	Connection Checkers
	#

	# Check the connection for this CSE to the remote CSE.
	def _checkConnectionToRegistrarCSE(self) -> None:
		L.isDebug and L.logDebug('Checking connection to Registrar CSE')
		# first check whether there is already a local CSR
		res = self._retrieveLocalCSRs()
		if res.status:
			localCSR = cast(List, res.data)[0] # hopefully, there is only one registrar CSR
			result = self._retrieveCSRfromRegistrarCSE()	# retrieve own CSR from the remote CSE
			if result.status:
				L.isDebug and L.logDebug('CSR found on registrar CSE')
				self.ownCSRonRegistrar = result.resource
				# own CSR is still in remote CSE, so check for changes in remote CSE
				result = self._retrieveRegistrarCSE() # retrieve the remote CSE
				self.registrarCSE = result.resource
				if result.rsc == RC.OK:
					if self.registrarCSE.isModifiedAfter(localCSR):	# remote CSE modified
						self._updateLocalCSR(localCSR, self.registrarCSE)
						L.isInfo and L.log('Local CSR updated')
				localCSE = Utils.getCSE().resource
				if localCSE.isModifiedAfter(self.ownCSRonRegistrar):	# local CSE modified
					self._updateCSRonRegistrarCSE(localCSE)
					L.isInfo and L.log('Remote CSR updated')

			else:
				L.isDebug and L.logDebug('CSR not found on registrar CSE')
				# Potential disconnect
				self._deleteLocalCSR(localCSR)	# ignore result
				result = self._createCSRonRegistrarCSE()
				if result.rsc == RC.created:
					self.ownCSRonRegistrar = result.resource
					result = self._retrieveRegistrarCSE()
					self.registrarCSE = result.resource
					if result.rsc == RC.OK:
						self._createLocalCSR(self.registrarCSE)		# TODO check result
						L.isInfo and L.log('Remote CSE connected')
						CSE.event.registeredToRemoteCSE(self.registrarCSE, self.ownCSRonRegistrar)	# type: ignore
				else:
					L.isInfo and L.log('Remote CSE disconnected')
					CSE.event.deregisteredFromRemoteCSE(self.ownCSRonRegistrar)	# type: ignore
					self.registrarCSE = None
			
		
		else:
			# No local CSR, so try to delete an optional remote one and re-create everything. 
			if self._deleteOwnCSRonRegistrarCSE().rsc in [ RC.deleted, RC.notFound ]:			# delete potential remote CSR
				result = self._createCSRonRegistrarCSE()									# create remote CSR
				self.ownCSRonRegistrar = result.resource
				if result.rsc == RC.created:
					result = self._retrieveRegistrarCSE()								# retrieve remote CSE
					self.registrarCSE = result.resource
					if result.rsc == RC.OK:
						self._createLocalCSR(self.registrarCSE) 					# TODO check result # create local CSR including ACPs to local CSR and local CSE
						L.isInfo and L.log('Remote CSE connected')
						CSE.event.registeredToRemoteCSE(self.registrarCSE, self.ownCSRonRegistrar)	# type: ignore
						



	def _checkCSRLiveliness(self) -> None:
		"""	Check the liveliness of all remote CSE's that are connected to this CSE.
			This is done by trying to retrieve a remote CSR. If it cannot be retrieved
			then the related local CSR is removed.
		"""
		for localCsr in cast(List, self._retrieveLocalCSRs(onlyOwn = False).data):
			L.isDebug and L.logDebug(f'Checking connection to registree CSE: {localCsr.ri}')
			if CSE.request.sendRetrieveRequest(localCsr.ri, originator = CSE.cseCsi, appendID = localCsr.csi).rsc != RC.OK:
				L.isWarn and L.logWarn(f'Remote CSE unreachable. Removing CSR: {localCsr.rn if localCsr else ""}')
				self._deleteLocalCSR(localCsr)


	#
	#	Local CSR
	#

	def _retrieveLocalCSRs(self, csi:str = None, onlyOwn:bool = True) -> Result:
		"""	Retrieve all local CSR's that match the given `csi` and return
			them in a list in *Result.data* .
		"""
		localCsrs = CSE.dispatcher.directChildResources(pi = CSE.cseRi, ty = T.CSR)
		if not csi:
			csi = self.registrarCSI
		# Logging.logDebug(f'Retrieving local CSR: {csi}')
		if onlyOwn:
			for localCsr in localCsrs:
				if (c := localCsr.csi) and c == csi:
					return Result(status = True, data = [ localCsr ])
			return Result.errorResult(rsc = RC.badRequest, dbg = 'local CSR not found')
		else:
			localCsrList = []
			for localCsr in localCsrs:
				if (c := localCsr.csi) and c == csi:	# skip own
					continue
				localCsrList.append(localCsr)
			return Result(status = True, data = localCsrList)	# hopefully only one


	def _createLocalCSR(self, remoteCSE: Resource) -> Result:
		L.isDebug and L.logDebug(f'Creating local CSR: {remoteCSE.ri}')

		# copy local CSE attributes into a new CSR
		localCSE = Utils.getCSE().resource
		csr = CSR.CSR(pi = localCSE.ri, rn = remoteCSE.csi[1:])	# remoteCSE.csi as name!
		self._copyCSE2CSR(csr, remoteCSE)
		#csr['ri'] = remoteCSE.ri 						# set the ri to the remote CSE's ri
		csr['ri'] = remoteCSE.csi[1:] 						# set the ri to the remote CSE's ri
		# add local CSR and ACP's
		if not (result := CSE.dispatcher.createResource(csr, localCSE)).resource:
			return result # Problem
		if not (res := CSE.registration.handleCSRRegistration(csr, remoteCSE.csi)).status:
			return Result.errorResult(rsc = RC.badRequest, dbg = f'cannot register CSR: {res.dbg}')
		return CSE.dispatcher.updateResource(csr, doUpdateCheck = False)		# TODO dbupdate() instead?



	def _updateLocalCSR(self, localCSR:Resource, remoteCSE:Resource) -> Result:
		L.isDebug and L.logDebug(f'Updating local CSR: {localCSR.rn}')
		# copy attributes
		self._copyCSE2CSR(localCSR, remoteCSE)
		return CSE.dispatcher.updateResource(localCSR)


	def _deleteLocalCSR(self, localCSR: Resource) -> Result:
		L.isDebug and L.logDebug(f'Deleting local CSR: {localCSR.ri}')

		if not CSE.registration.handleCSRDeRegistration(localCSR):
			return Result.errorResult(rsc = RC.badRequest, dbg = 'cannot deregister CSR')

		# Delete local CSR
		return CSE.dispatcher.deleteResource(localCSR)


	#
	#	Remote Registrar CSR 
	#

	def _retrieveCSRfromRegistrarCSE(self) -> Result:
		L.isDebug and L.logDebug(f'Retrieving CSR from registrar CSE: {self.registrarCSI}')
		result = CSE.request.sendRetrieveRequest(self.registrarCSRURL, CSE.cseCsi, ct=self.registrarSerialization)	# own CSE.csi is the originator
		if not result.rsc == RC.OK:
			result.status = False	# The request returns OK, but for the procedure it is false
			return result
		return Result(status = True, resource = CSR.CSR(cast(JSON, result.data), pi=''), rsc = RC.OK)


	def _createCSRonRegistrarCSE(self) -> Result:
		L.isDebug and L.logDebug(f'Creating registrar CSR: {self.registrarCSI}')		
		# get local CSEBase and copy relevant attributes
		localCSE = Utils.getCSE().resource
		csr = CSR.CSR(rn=localCSE.ri) # ri as name!
		self._copyCSE2CSR(csr, localCSE)
		#csr['ri'] = CSE.cseCsi							# override ri with the own cseID
		#csr['cb'] = Utils.getIdFromOriginator(localCSE.csi)	# only the stem
		for _ in ['ty','ri', 'ct', 'lt']: csr.delAttribute(_, setNone = False)	# remove a couple of attributes

		# Create the <remoteCSE> in the remote CSE
		L.isDebug and L.logDebug(f'Creating registrar CSR at: {self.registrarCSI} url: {self.registrarCSEURL}')	
		res = CSE.request.sendCreateRequest(self.registrarCSEURL, CSE.cseCsi, ty = T.CSR, data = csr.asDict(), ct = self.registrarSerialization) # own CSE.csi is the originator
		if res.rsc not in [ RC.created, RC.OK ]:
			if res.rsc != RC.conflict:
				L.isDebug and L.logDebug(f'Error creating registrar CSR: {int(res.rsc)}')
			return Result.errorResult(rsc = res.rsc, dbg = 'cannot create remote CSR')
		L.isDebug and L.logDebug(f'Registrar CSR created: {self.registrarCSI}')
		return Result(status = True, resource = CSR.CSR(cast(JSON, res.data), pi = ''), rsc = RC.created)


	def _updateCSRonRegistrarCSE(self, localCSE:Resource = None) -> Result:
		"""	Update the <remoteCSE> resource on the registrar CSE.

			Args:
				localCSE: Optional CSE resource to use for the update, otherwise take the normal CSE resource.
			Return:
				Result object
		"""
		L.isDebug and L.logDebug(f'Updating registrar CSR in CSE: {self.registrarCSI}')
		if not localCSE:
			localCSE = Utils.getCSE().resource
		csr = CSR.CSR()
		self._copyCSE2CSR(csr, localCSE, isUpdate = True)
		del csr['acpi']			# remove ACPI (don't provide ACPI in updates...a bit)

		res = CSE.request.sendUpdateRequest(self.registrarCSRURL, CSE.cseCsi, data = csr.asDict(), ct = self.registrarSerialization) 	# own CSE.csi is the originator
		if res.rsc not in [ RC.updated, RC.OK ]:
			if res.rsc != RC.conflict:
				L.isDebug and L.logDebug(f'Error updating registrar CSR in CSE: {int(res.rsc)}')
			return Result.errorResult(rsc = res.rsc, dbg = 'cannot update remote CSR')
		L.isDebug and L.logDebug(f'Registrar CSR updated in CSE: {self.registrarCSI}')
		return Result(status = True, resource = CSR.CSR(cast(JSON, res.data), pi = ''), rsc = RC.updated)



	def _deleteOwnCSRonRegistrarCSE(self) -> Result:
		L.isDebug and L.logDebug(f'Deleting registrar CSR: {self.registrarCSI} url: {self.registrarCSRURL}')
		res = CSE.request.sendDeleteRequest(self.registrarCSRURL, CSE.cseCsi, ct = self.registrarSerialization,)	# own CSE.csi is the originator
		if res.rsc not in [ RC.deleted, RC.OK ]:
			return Result.errorResult(rsc = res.rsc, dbg = 'cannot delete registrar CSR')
		L.isInfo and L.log(f'Registrar CSR deleted: {self.registrarCSI}')
		return Result(status = True, rsc = RC.deleted)


	#
	#	Remote Registrar CSE
	#

	def _retrieveRegistrarCSE(self) -> Result:
		"""	Retrieve the remote registrar CSE
		"""

		L.isDebug and L.logDebug(f'Retrieving registrar CSE from: {self.registrarCSI} url: {self.registrarCSEURL}')	
		res = CSE.request.sendRetrieveRequest(self.registrarCSEURL, CSE.cseCsi, ct = self.registrarSerialization)	# own CSE.csi is the originator
		if res.rsc not in [ RC.OK ]:
			return res.errorResultCopy()
		if (csi := Utils.findXPath(cast(JSON, res.data), 'm2m:cb/csi')) == None:
			L.logErr(dbg := 'csi not found in remote CSE resource', showStackTrace = False)
			return Result.errorResult(dbg = dbg)
		if not csi.startswith('/'):
			L.isDebug and L.logWarn('Remote CSE.csi doesn\'t start with /. Correcting.')	# TODO Decide whether correcting this is actually correct. Also in validator.validateCSICB()
			Utils.setXPath(cast(JSON, res.data), 'm2m:cb/csi', f'/{csi}')

		return Result(status = True, resource = CSEBase.CSEBase(cast(JSON, res.data)), rsc = RC.OK)


	def getAllLocalCSRs(self) -> List[Resource]:
		"""	Return all local CSR's. This includes the CSR of the registrar CSE.
			This function builds the list from a temporary internal list, but not from the database.
		"""
		result = [ csr for (csr, _) in self.descendantCSR.values() if csr ]
		result.append(self.ownCSRonRegistrar)
		return result


	#########################################################################


	def retrieveRemoteResource(self, id:str, originator:str = None) -> Result:
		"""	Retrieve a resource from a remote CSE.
		"""
		if not (url := CSE.request._getForwardURL(id)):
			return Result.errorResult(rsc = RC.notFound, dbg = f'URL not found for id: {id}')
		if not originator:
			originator = CSE.cseCsi
		L.isDebug and L.logDebug(f'Retrieve remote resource id: {id} url: {url}')
		res = CSE.request.sendRetrieveRequest(url, originator)	## todo
		if not res.status or res.rsc != RC.OK:
			return res.errorResultCopy()
		
		# assign the remote ID to the resource's dictionary
		_, tpe = Utils.pureResource(cast(JSON, res.data))
		Utils.setXPath(cast(JSON, res.data), f'{tpe}/{Resource._remoteID}', id)

		# Instantiate
		# return Factory.resourceFromDict(res.dict, isRemote=True) if not raw else Result(resource=res.dict)
		return Factory.resourceFromDict(cast(JSON, res.data))


	def getCSRFromPath(self, id:str) -> Tuple[Resource, List[str]]:
		"""	Try to get a CSR even from a longer path (only the first 2 path elements are relevant). 

			If no direct CSR could be found then that CSR is returned where the addressed csi is a descendant.

			Returns a tuple (csr resource, list of path elements), or (None, None) in case of an error).
		"""

		def getCSRWithDescendant(csi:str) -> Resource:
			# L.logWarn(self.descendantCSR)
			t = self.descendantCSR.get(csi)
			
			if t and t[0]:
				return t[0]		# already a CSR resource
			if t and t[1]:
				return getCSRWithDescendant(t[1]) # indirect, need further step
			return None

		if not id:
			return None, None
		ids = id.split('/')
		# L.isDebug and L.logDebug(f'CSR ids: {ids}')
		if Utils.isSPRelative(id):
			ri = ids[1]
		elif Utils.isAbsolute(id):
			ri = ids[2]
		else:
			ri = id

		if not (res := CSE.dispatcher.retrieveLocalResource(ri=ri)).status:
			csr = getCSRWithDescendant(f'/{ri}')
		else:
			csr = res.resource
		# L.logWarn(csr)
		return csr, ids


	#########################################################################


	def _copyCSE2CSR(self, target:Resource, source:Resource, isUpdate:bool = False) -> None:

		def _copyAttribute(attr:str) -> None:
			if attr in source and attr not in self.excludeCSRAttributes:
				target[attr] = source[attr]

		if 'csb' in source and 'csb' not in self.excludeCSRAttributes:
			target['csb'] = self.registrarCSEURL
		_copyAttribute('csi')
		_copyAttribute('cst')
		_copyAttribute('csz')
		_copyAttribute('lbl')
		_copyAttribute('nl')
		_copyAttribute('poa')
		_copyAttribute('rr')
		_copyAttribute('srv')
		_copyAttribute('st')
		
		if 'cb' not in self.excludeCSRAttributes:
			target['cb'] = f'{source.csi}/{source.rn}'
		if 'dcse' not in self.excludeCSRAttributes:
			target['dcse'] = list(self.descendantCSR.keys())		# Always do this bc it might be different, even empty for an update
		

		# Always remove some attributes
		for attr in [ 'acpi' ]:
			if attr in target:
				target.delAttribute(attr, setNone = False)
		
		# Remove attributes in updates
		if isUpdate:
			# rm some attributes
			for attr in [ 'ri', 'rn', 'ct', 'lt', 'ty', 'cst', 'cb', 'csi']:
				if attr in target:
					target.delAttribute(attr, setNone = False)

