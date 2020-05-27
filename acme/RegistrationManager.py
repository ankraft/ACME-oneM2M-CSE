#
#	RegistrationManager.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Managing resource / AE registrations
#

from Logging import Logging
from Constants import Constants as C
from Configuration import Configuration
import CSE, Utils
from resources import ACP

acpPrefix = 'acp_'


class RegistrationManager(object):

	def __init__(self):
		Logging.log('RegistrationManager initialized')


	def shutdown(self):
		Logging.log('RegistrationManager shut down')


	#########################################################################

	#
	#	Handle new resources in general
	#

	def checkResourceCreation(self, resource, originator, parentResource=None):
		if resource.ty == C.tAE:
			if (originator := self.handleAERegistration(resource, originator, parentResource)) is None:
				return (None, C.rcBadRequest)
		if resource.ty == C.tCSR:
			if (originator := self.handleCSRRegistration(resource, originator, parentResource)) is None:
				return (None, C.rcBadRequest)

		# Test and set creator attribute.
		if (rc := self.handleCreator(resource, originator)) != C.rcOK:
			return (None, rc)

		return (originator, C.rcOK)


	# Check for (wrongly) set creator attribute as well as assign it to allowed resources.
	def handleCreator(self, resource, originator):
		# Check whether cr is set. This is wrong
		if resource.cr is not None:
			Logging.logWarn('Setting "creator" attribute is not allowed.')
			return C.rcBadRequest
		# Set cr for some of the resource types
		if resource.ty in C.tCreatorAllowed:
			resource['cr'] = Configuration.get('cse.originator') if originator in ['C', 'S', '', None ] else originator
		return C.rcOK


	def checkResourceDeletion(self, resource, originator):
		if resource.ty == C.tAE:
			if not self.handleAEDeRegistration(resource):
				return (False, originator)
		if resource.ty == C.tCSR:
			if not self.handleCSRDeRegistration(resource):
				return (False, originator)
		return (True, originator)



	#########################################################################

	#
	#	Handle AE registration
	#

	def handleAERegistration(self, ae, originator, parentResource):

		# check for empty originator and assign something
		if originator is None or len(originator) == 0:
			originator = 'C'

		# Check for allowed orginator
		# TODO also allow when there is an ACP?
		if not Utils.isAllowedOriginator(originator, Configuration.get('cse.registration.allowedAEOriginators')):
			Logging.logDebug('Originator not allowed')
			return None


		# Assign originator for the AE
		if originator == 'C':
			originator = Utils.uniqueAEI('C')
		elif originator == 'S':
			originator = Utils.uniqueAEI('S')
		# elif originator is None or len(originator) == 0:
		# 	originator = Utils.uniqueAEI('S')
		Logging.logDebug('Registering AE. aei: %s ' % originator)

		# set the aei to the originator
		ae['aei'] = originator

		# set the ri of the ae to the aei (TS-0001, 10.2.2.2)
		ae['ri'] = originator

		# Verify that parent is the CSEBase, else this is an error
		if parentResource is None or parentResource.ty != C.tCSEBase:
			return None

		# Create an ACP for this AE-ID if there is none set
		if Configuration.get("cse.ae.createACP"):
			if ae.acpi is None or len(ae.acpi) == 0:
				Logging.logDebug('Adding ACP for AE')
				cseOriginator = Configuration.get('cse.originator')
				acp = ACP.ACP(pi=parentResource.ri, rn=acpPrefix + ae.rn, createdByAE=ae.ri)
				acp.addPermission([originator, cseOriginator], Configuration.get('cse.acp.pv.acop'))
				acp.addSelfPermission([cseOriginator], Configuration.get('cse.acp.pvs.acop'))
				# acp.addPermissionOriginator(originator)
				# acp.addPermissionOriginator(cseOriginator)
				# acp.setPermissionOperation(Configuration.get('cse.acp.pv.acop'))
				# acp.addSelfPermissionOriginator(cseOriginator)
				# acp.setSelfPermissionOperation(Configuration.get('cse.acp.pvs.acop'))
				if not (res := self.checkResourceCreation(acp, originator, parentResource))[0]:
					return None
				if CSE.dispatcher.createResource(acp, parentResource=parentResource, originator=originator)[0] is None:
					return None

				# Set ACPI (anew)
				ae['acpi'] = [ acp.ri ]
		else:
			ae['acpi'] = [ Configuration.get('cse.defaultACPI') ]

		return originator


	#
	#	Handle AE deregistration
	#

	def handleAEDeRegistration(self, resource):
		# remove the before created ACP, if it exist
		Logging.logDebug('DeRegisterung AE. aei: %s ' % resource.aei)
		if Configuration.get("cse.ae.removeACP"):
			Logging.logDebug('Removing ACP for AE')
			acpi = '%s/%s%s' % (Configuration.get("cse.rn"), acpPrefix, resource.rn)
			if (res := CSE.dispatcher.retrieveResource(acpi))[1] != C.rcOK:
				Logging.logWarn('Could not find ACP: %s' % acpi) # ACP not found, either not created or already deleted
			else:
				acp = res[0]
				# only delete the ACP when it was created in the course of AE registration
				if  (aeRI := acp.createdByAE()) is not None and resource.ri == aeRI:	
					CSE.dispatcher.deleteResource(acp)
		return True


	#########################################################################

	#
	#	Handle CSR registration
	#

	def handleCSRRegistration(self, csr, originator, parentResource):
		Logging.logDebug('Registering CSR. csi: %s ' % csr['csi'])

		# Create an ACP for this CSR if there is none set
		if Configuration.get("cse.ae.createACP"): # TODO
			if csr.acpi is None or len(csr.acpi) == 0:
				Logging.logDebug('Adding ACP for CSR')

				# Add ACP for remote CSE to access the own CSE
				cseOriginator = Configuration.get('cse.originator')
				acp = ACP.ACP(pi=parentResource.ri, rn=acpPrefix + csr.rn, createdByAE=csr.ri) # TODO name of parameter may be confusing
				acp.addPermission([originator, cseOriginator], Configuration.get('cse.acp.pv.acop'))
				acp.addSelfPermission([cseOriginator], Configuration.get('cse.acp.pvs.acop'))
				if not (res := self.checkResourceCreation(acp, originator, parentResource))[0]:
					return None
				if CSE.dispatcher.createResource(acp, parentResource=parentResource, originator=originator)[0] is None:
					return None

				# Add another ACP for rempte CSE to access the CSE, at least to read
				cseAcp = ACP.ACP(pi=parentResource.ri, rn=acpPrefix + csr.rn + '_CSE', createdByAE=csr.ri) # TODO name of parameter may be confusing
				cseAcp.addPermission([originator, cseOriginator], C.permRETRIEVE)
				cseAcp.addSelfPermission([cseOriginator], Configuration.get('cse.acp.pvs.acop'))
				if not (res := self.checkResourceCreation(cseAcp, originator, parentResource))[0]:
					return None
				if CSE.dispatcher.createResource(cseAcp, parentResource=parentResource, originator=originator)[0] is None:
					return None

				# retrieve the CSEBase and assign the new ACP
				if (res := CSE.dispatcher.retrieveResource(Configuration.get('cse.csi')))[0] is not None:
					res[0].acpi.append(cseAcp.ri)
					CSE.dispatcher.updateResource(res[0], doUpdateCheck=False)


				# Set ACPI (anew)
				csr['acpi'] = [ acp.ri ]
		else:
			csr['acpi'] = [ Configuration.get('cse.defaultACPI') ]

		return originator


	#
	#	Handle CSR deregistration
	#

	def handleCSRDeRegistration(self, csr):
		# remove the before created ACP, if it exist
		Logging.logDebug('DeRegisterung CSR. csi: %s ' % csr['csi'])
		if Configuration.get("cse.ae.removeACP"): # TODO
			Logging.logDebug('Removing ACPs for CSR')

			# Retrieve CSR ACP
			acpi = '%s/%s%s' % (Configuration.get("cse.rn"), acpPrefix, csr.rn)
			if (res := CSE.dispatcher.retrieveResource(acpi))[1] != C.rcOK:
				Logging.logWarn('Could not find ACP: %s' % acpi)	# ACP not found, either not created or already deleted
			else:
				acp = res[0]
				# only delete the ACP when it was created in the course of AE registration
				if  (aeRI := acp.createdByAE()) is not None and csr.ri == aeRI:	# TODO Name
					CSE.dispatcher.deleteResource(acp)

			# Retrieve CSE ACP
			acpi = acpi + '_CSE'
			if (res := CSE.dispatcher.retrieveResource(acpi))[1] != C.rcOK:
				Logging.logWarn('Could not find ACP: %s' % acpi)	# ACP not found, either not created or already deleted
			else:
				acp = res[0]
				# First remove it from the CSE
				if (res := CSE.dispatcher.retrieveResource(Configuration.get('cse.csi')))[0] is not None:
					res[0].acpi.remove(acp.ri)
					CSE.dispatcher.updateResource(res[0], doUpdateCheck=False)

				# only delete the ACP when it was created in the course of AE registration
				if  (aeRI := acp.createdByAE()) is not None and csr.ri == aeRI:	# TODO Name
					CSE.dispatcher.deleteResource(acp)

		return True


