#
#	ACPAnnc.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
""" AccessControlPolicy announced (ACP)  resource type """

from __future__ import annotations
from ..helpers.TextTools import simpleMatch
from ..etc.Types import AttributePolicyDict, ResourceTypes as T, Permission, JSON
from ..resources.AnnouncedResource import AnnouncedResource
from ..resources.Resource import *


class ACPAnnc(AnnouncedResource):
	""" AccessControlPolicy announced (ACPA) resource type """

	_allowedChildResourceTypes:list[T] = [ T.SUB ]
	""" The allowed child-resource types. """

	# Assigned during startup in the Importer
	_attributes:AttributePolicyDict = {	
			# Common and universal attributes for announced resources
			'rn': None,
		 	'ty': None,
			'ri': None,
			'pi': None,
			'ct': None,
			'lt': None,
			'et': None,
			'lbl': None,
			'acpi':None,
			'daci': None,
			'lnk': None,
			'ast': None,

			# Resource attributes
			'pv': None,
			'pvs': None,
			'adri': None,
			'apri': None,
			'airi': None
	}
	"""	Attributes and `AttributePolicy' for this resource type. """


	def __init__(self, dct:JSON, pi:str = None, create:bool = False) -> None:
		super().__init__(T.ACPAnnc, dct, pi = pi, create = create)


	#########################################################################
	#
	#	Resource specific
	#
	
	def checkSelfPermission(self, originator:str, requestedPermission:Permission) -> bool:
		"""	Check whether an *originator* has the requested permissions to the `ACP` resource itself.

			Args:
				originator: The originator to test the permissions for.
				requestedPermission: The permissions to test.
			Return:
				If any of the configured *accessControlRules* of the ACP resource matches, then the originatorhas access, and *True* is returned, or *False* otherwise.
		"""
		# TODO this is the same function as in ACP.py. Move it to SecurityManager?
		
		for p in self['pvs/acr']:
			if requestedPermission & p['acop'] == 0:	# permission not fitting at all
				continue
			# TODO check acod in pvs
			if 'all' in p['acor'] or originator in p['acor']:
				return True
			if any([ simpleMatch(originator, a) for a in p['acor'] ]):	# check whether there is a wildcard match
				return True
		return False