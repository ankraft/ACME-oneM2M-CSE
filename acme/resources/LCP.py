 #
#	LCP.py
#
#	(c) 2023 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: LocationPolicy
#

""" LocationPolicy (LCP) resource type. """

from __future__ import annotations
from typing import Optional

from ..etc.Types import AttributePolicyDict, ResourceTypes, JSON, LocationSource
from ..etc.Constants import Constants
from ..runtime.Logging import Logging as L
from ..runtime import CSE
from ..runtime.Configuration import Configuration
from ..resources.Resource import Resource, addToInternalAttributes
from ..resources.AnnounceableResource import AnnounceableResource
from ..resources import Factory 
from ..etc.ResponseStatusCodes import BAD_REQUEST, NOT_IMPLEMENTED
from ..etc.GeoTools import getGeoPolygon


# Add to internal attributes
addToInternalAttributes(Constants.attrGTA)


# TODO add annc
# TODO add to supported resources of CSE

class LCP(AnnounceableResource):
	""" LocationPolicy (LCP) resource type. """

	resourceType = ResourceTypes.LCP
	""" The resource type """

	typeShortname = resourceType.typeShortname()
	"""	The resource's domain and type name. """

	# Specify the allowed child-resource types
	_allowedChildResourceTypes:list[ResourceTypes] = [ ResourceTypes.SUB ]
	""" The allowed child-resource types. """

	# Attributes and Attribute policies for this Resource Class
	# Assigned during startup in the Importer
	_attributes:AttributePolicyDict = {		
		# Common and universal attributes
		'rn': None,
		'ty': None,
		'ri': None,
		'pi': None,
		'ct': None,
		'lt': None,
		'lbl': None,
		'acpi':None,
		'et': None,
		'daci': None,
		'cstn': None,
		'at': None,
		'aa': None,
		'ast': None,

		# Resource attributes
		'los': None,
		'lit': None,
		'lou': None,
		'lot': None,
		'lor': None,
		'loi': None,
		'lon': None,
		'lost': None,
		'gta': None,
		'gec': None,
		'aid': None,
		'rlkl': None,
		'luec': None
	}
	"""	Attributes and `AttributePolicy` for this resource type. """


	def activate(self, parentResource: Resource, originator: str) -> None:
		super().activate(parentResource, originator)

		# Creating extra <container> resource
		# Set the li attribute to the LCP's ri afterwards
		_cnt:JSON = {
			'mni': Configuration.resource_lcp_mni,
			'mbs': Configuration.resource_lcp_mbs,
		}
		if self.lon is not None:	# add container's resourcename if provided
			_cnt['rn'] = self.lon

		container = Factory.resourceFromDict(_cnt,
											 pi = parentResource.ri, 
											 ty = ResourceTypes.CNT,
											 create = True,
											 originator = originator)
		try:
			container = CSE.dispatcher.createLocalResource(container, parentResource, originator)
		except Exception as e:
			L.isWarn and L.logWarn(f'Could not create container for LCP: {e}')
			raise BAD_REQUEST(f'Could not create container for LCP. Resource name: {self.lon} already exists?')
		# set internal attributes afterwards (after validation)
		container.setLCPLink(self.ri)

		# Set backlink to container in LCP
		self.setAttribute('loi', container.ri)


		# Register the LCP for periodic positioning procedure
		CSE.location.addLocationPolicy(self)



		# If the value of locationUpdatePeriod attribute is updated to 0 or NULL, 
		# the Hosting CSE shall stop periodical positioning procedure and perform the procedure when
		# Originator retrieves the <latest> resource of the linked <container> resource. See clause 10.2.9.6 and clause 10.2.9.7 for more detail.

		# TODO add event for latest + location retrieval

		# If the value of locationUpdatePeriod attribute is updated to bigger than 0 (e.g. 1 hour) from 0 or NULL,
		# the Hosting CSE shall start periodical positioning procedure.


	def updated(self, dct: JSON | None = None, originator: str | None = None) -> None:
		super().updated(dct, originator)

		# update the location policy handling
		CSE.location.updateLocationPolicy(self)


	def deactivate(self, originator:str, parentResource:Resource) -> None:
		# Delete the extra <container> resource
		if self.loi is not None:
			CSE.dispatcher.deleteResource(self.loi, originator)
		CSE.location.removeLocationPolicy(self)
		super().deactivate(originator, parentResource)


	def validate(self, originator: str | None = None, dct: JSON | None = None, parentResource: Resource | None = None) -> None:

		def validateNetworkBasedAttributes() -> None:
			""" Validate the Network_based attributes. """

			if self.getFinalResourceAttribute('lot', dct) is not None: # locationTargetID
				raise BAD_REQUEST(f'Attribute lot is only allowed if los is Network_based.')
			if self.getFinalResourceAttribute('aid', dct) is not None: # authID
				raise BAD_REQUEST(f'Attribute aid is only allowed if los is Network_based.')
			if self.getFinalResourceAttribute('lor', dct) is not None:	# locationServer
				raise BAD_REQUEST(f'Attribute aid is only allowed if los is Network_based.')
			if self.getFinalResourceAttribute('rlkl', dct) is not None:	# retrieveLastKnownLocation
				raise BAD_REQUEST(f'Attribute rlkl is only allowed if los is Network_based.')
			if self.getFinalResourceAttribute('luec', dct) is not None:	# loocationUpdateEventCriteria
				raise BAD_REQUEST(f'Attribute luec is only allowed if los is Network_based.')

		super().validate(originator, dct, parentResource)

		# Error for unsupported location source types
		los = self.getFinalResourceAttribute('los', dct)	# locationSource
		if los in [ LocationSource.Network_based, LocationSource.Sharing_based]:
			raise NOT_IMPLEMENTED(L.logWarn(f'Unsupported LocationSource: {LocationSource(self.los)}'))


		# Check the various locationSource types
		match los:
			case LocationSource.Network_based | LocationSource.Sharing_based:
				raise NOT_IMPLEMENTED(L.logWarn(f'Unsupported LocationSource: {LocationSource(los)}'))
			case LocationSource.Device_based:
				validateNetworkBasedAttributes()
	
				# Always set the lost to an empty string as long as the locationSource is not Network_based 
				self.setAttribute('lost', '')

		# Validate the polygon
		if (gta := self.gta) is not None:
			if (g := getGeoPolygon(gta)) is None:
				raise BAD_REQUEST('Invalid geographicalTargetArea. Must be a valid geoJSON polygon.')
			self.setAttribute(Constants.attrGTA, g)	# store the geoJSON polygon in the internal attribute
		


		# TODO store lou to _lou 



		# TODO more warnings for unsupported attributes (mainly for geo server)
	

# TODo geographicalTargetArea : What if not closed?
# TODO geofenceEventCriteria should be a list of GeofenceEventCriteria
# TODO retrieveLastKnownLocation: Indicates if the Hosting CSE shall retrieve the last known location when the Hosting CSE fails to retrieve the latest location WTF`?????
# TODO: locationUpdateEventCriteria Not supported



#Procedure for <contentInstance> resource that stores location information

# After the <container> resource that stores the location information is created, each instance of location information shall be stored
#  in the different <contentInstance> resources. In order to store the location information in the <contentInstance> resource,
#  the Hosting CSE firstly checks the defined locationUpdatePeriod attribute. 
# If a valid period value is set for this attribute, the Hosting CSE shall perform the positioning procedures as defined by locationUpdatePeriod
#  in the associated <locationPolicy> resource and stores the results (e.g. position fix and uncertainty) in the <contentInstance> resource
#  under the created <container> resource. However, if no value (e.g. null or zero) is set and locationUpdateEventCriteria is absent, 
# the positioning procedure shall be performed when an Originator requests to retrieve the <latest> resource of the <container>
#  resource and the result shall be stored as a <contentInstance> resource under the <container> resource.
