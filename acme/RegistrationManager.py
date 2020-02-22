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


# TODO: create/delete each resource to count! resourceCreate(ty)

# TODO move event creations from here to the resp modules.


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

		if resource.ty in [ C.tAE ]:
			if (originator := self.handleAERegistration(resource, originator, parentResource)) is None:
				return (False, originator)

		# Test and set creator attribute.
		# TODO: not for all resource types
		if resource['cr'] is not None:	# must not be set in resource when creating
			return (False, originator)
		resource['cr'] = originator

		return (True, originator)


	#########################################################################

	#
	#	Handle AE registration
	#

	def handleAERegistration(self, ae, originator, parentResource):
		if originator == 'C':
			originator = Utils.uniqueAEI('C')
		elif originator == 'S':
			originator = Utils.uniqueAEI('S')
		elif originator is None or len(originator) == 0:
			originator = Utils.uniqueAEI('S')

		# set the aei to the originator
		ae['aei'] = originator

		# Verify that parent is the CSEBase, else this is an error
		if parentResource is None or  parentResource.ty != C.tCSEBase:
			return None

		# Create an ACP for this AE-ID if there is none set
		if Configuration.get("cse.ae.createACP"):
			if ae.acpi is None or len(ae.acpi) == 0:
				cseOriginator = Configuration.get('cse.originator')
				acp = ACP.ACP(pi=parentResource.ri)
				acp.addPermissionOriginator(originator)
				acp.addPermissionOriginator(cseOriginator)
				acp.setPermissionOperation(Configuration.get('cse.acp.pv.acop'))
				acp.addSelfPermissionOriginator(cseOriginator)
				acp.setSelfPermissionOperation(Configuration.get('cse.acp.pvs.acop'))
				if not (res := self.checkResourceCreation(acp, originator, parentResource))[0]:
					return None
				CSE.dispatcher.createResource(acp, parentResource=parentResource, originator=originator)

				# Set ACPI (anew)
				ae['acpi'] = [ acp.ri ]
		else:
			ae['acpi'] = [ Configuration.get('cse.defaultACPRI') ]



		return originator
