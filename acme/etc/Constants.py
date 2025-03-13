#
#	Constants.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
""" Various CSE and oneM2M constants """

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from ..etc.Types import ContentSerializationType, CSEType, CSEStatus


class Constants(object):
	""" Various CSE and oneM2M constants """

	
	version	= '2025.03.1'
	"""	ACME's release version """

	logoColor = '#b42025'
	"""	oneM2M logo colour """
	
	textLogo = f'[dim][[/dim][{logoColor}][i]ACME[/i][/{logoColor}][dim]][/dim]'
	"""	ACME's colorful console logo """

	copyright = '(c) 2025 by Andreas Kraft'
	"""	ACME's copyright """

	#
	#	Configuration files
	#

	defaultConfigFile = 'acme.ini.default'
	"""	The name of the INI file that contains the default configuration settings """

	defaultUserConfigFile = 'acme.ini'
	""" The name of the INI file that contains the user-defined configuration settings """


	#
	#	HTTP Header Fields
	#	These fields are here instead of the httpServer bc they are also used by the test cases.
	#

	hfOrigin = 'X-M2M-Origin'
	"""	HTTP header field: originator """

	hfRI = 'X-M2M-RI'
	"""	HTTP header field: request identifier """
	
	hfRVI = 'X-M2M-RVI'
	"""	HTTP header field: release version indicator """
	
	hfEC = 'X-M2M-EC'
	"""	HTTP header field: event category """
	
	hfRET = 'X-M2M-RET'
	"""	HTTP header field: request expiration timestamp """

	hfRST = 'X-M2M-RST'
	"""	HTTP header field: result expiration timestamp """
	
	hfOET = 'X-M2M-OET'
	"""	HTTP header field: operation execution time """

	hfOT = 'X-M2M-OT'
	"""	HTTP header field: originating timestamp """

	hfRTU = 'X-M2M-RTU'
	"""	HTTP header field: notificationURI element of the response type """
	
	hfRSC = 'X-M2M-RSC'
	"""	HTTP header field: response status code """

	hfVSI = 'X-M2M-VSI'
	"""	HTTP header field: vendor information """
			
	#
	# 	Contstants for internal Resource attributes
	#	They are here for easier access and to help not to include the "Resource" class all the time

	attrAnnouncedTo = '__announcedTo__'			# List
	""" Constant: Name of the 'Resource' internal *__announcedTo__* attribute. This attribute holds internal announcement information. """

	attrCreatedInternallyRI = '__createdInternallyRI__'
	""" Constant: Name of the `Resource` internal *__createdInternally__* attribute. This attribute indicates whether a resource was created internally or by an external request. """

	attrBCNI = '__bcni__'
	""" Constant: Name of the `Resource` internal *__bcni__* attribute. This attribute holds the value of the *bcni* attribute in s. """

	attrBCNT = '__bcnt__'
	""" Constant: Name of the `Resource` internal *__bcnt__* attribute. This attribute holds the value of the *bcnt* attribute in s. """

	attrDecodedDsp = '__decodedDsp__'
	""" Name of an internal string attribute that holds the semantic description after base64 decode. """

	attrGTA = '__gta__'
	""" Constant: Name of the `Resource` internal *__gta__* attribute. This attribute holds the geoJSON polygon of the geographical target area. """

	attrHasFCI	= '__hasFCI__'
	""" Constant: Name of the `Resource` internal *__hasFCI__* attribute. This attribute indicates whether this resource has la/ol installed. """

	attrImported = '__imported__'
	""" Constant: Name of the `Resource` internal *__imported__* attribute. This attribute indicates whether a resource was imported or created by a script, of created by a request. """

	attrIsManuallyInstantiated = '__isInstantiated__'
	""" Constant: Name of the `Resource` internal *__isInstantiated__* attribute. This attribute indicates whether a resource is manually instantiated. """

	attrLaRi = '__lari__'
	""" Constant: Name of the `Resource` internal *__lari__* attribute. This attribute holds the resourceID's of the *latest* child-resource for some resource types. """

	attrLCPLink = '__li__'
	""" Constant: Name of the `Resource` internal *__li__* attribute. This attribute holds the link to the LCP resource (from the parent <container> resource). """

	attrLocCoordinate = '__locCoordinate__'
	""" Constant: Name of the `Resource` internal *__locCoordinate__* attribute. This attribute holds the location coordinate of a resource. """

	attrModified = '__modified__'
	""" Constant: Name of the `Resource` internal *__modified__* attribute. This attribute holds the resource's precise modification timestamp. """

	attrNode = '__node__'
	"""	Constant: Name of the `Resource` internal __node__ attribute. This attribute is used in some resource types to hold a reference to the hosting <node> resource. """

	attrOlRi = '__olri__'
	""" Constant: Name of the 'Resource internal *__olri__* attribute. This attribute holds the resourceID's of the *oldest* child-resource for some resource types. """

	attrOriginator = '__originator__'			# Or creator
	""" Constant: Name of the `Resource` internal *__originator__* attribute. This attribute holds the original creator of a resource."""
	
	attrParentOriginator = '__parentOriginator__'
	""" Constant: Name of the `Resource` internal *__parentOriginator__* attribute. This attribute holds the parent resource's originator. """

	attrPCUAggregate = '__aggregate__'
	""" Constant: Name of the `Resource` internal *__aggregate__* attribute. This attribute holds the parent PCH resource's aggregate value. """

	attrPCURI = '__pcuRI__'
	""" Constant: Name of the `Resource` internal *__pcuRI__* attribute. This attribute holds the resourceID of the parent PCH resource. """

	attrRemoteID = '__remoteID__'			# When this is a resource from another CSE
	""" Constant: Name of the `Resource` internal *__remoteID__* attribute. This attribute holds a list of the resource's announced variants. """

	attrRiTyMapping = '__riTyMapping__'
	""" Constant: Name of the 'Resource internal *__riTyMapping__* attribute. This attribute holds the mapping of resourceID's to resource types. """

	attrRvi = '__rvi__'					# Request version indicator when created
	""" Constant: Name of the `Resource` internal *__rvi__* attribute. This attribute holds the Release Version Indicator for which the resource was created. """

	attrRtype = '__rtype__'
	"""	Constant: Name of the `Resource` internal *__rtype__* attribute. This attribute holds the resource type name, e.g. "m2m:cnt". """

	attrSrn = '__srn__'
	"""	Constant: Name of the `Resource` internal *__srn__* attribute. This attribute holds the resource's structured resource name. """

	attrSubSratRIs = '__subSratRIs__'
	""" Constant: Name of the `Resource` internal *__subSratRIs__* attribute. This attribute holds the resourceIDs of the <sub> resources that are subscribed to the <srat> resource. """

	attrSudRI = '__sudRI__'
	""" Constant: Name of the `Resource` internal *__sudRI__* attribute.  when the resource is been deleted because of the deletion of a rrat or srat subscription. Usually empty. """

	attrSubscriptionCounter = '__subCtr__'
	""" Constant: Name of the `Resource` internal *__subCtr__* attribute. This attribute holds the subscription counter for a resource. """




	#
	#	Supported URL schemes
	#
	supportedSchemes = ['coap', 'coaps', 'http', 'https', 'mqtt', 'mqtts', 'ws', 'wss', 'acme']
	""" The URL schemes supported by the CSE. """

	defaultWebSocketSchema = 'ws://default'
	""" The URL scheme used when a WebSocket connection cannot be established because the remote entity doesn't host a WebSocket server. """


	#
	#	Internal CSE's startup delay
	#

	cseStartupDelay:float = 2.0
	""" Internal CSE's startup delay. """


	#
	#	Network Coordination supported
	#
	networkCoordinationSupported = False
	""" Network coordination supported by the CSE. """


class RuntimeConstants(object):
	""" Various runtime constants, determined during startup of the CSE """

	cseAbsolute:str = None
	""" The CSE's Absolute prefix (SP-ID/CSE-ID). """

	cseAbsoluteSlash:str = None
	""" The CSE's Absolute prefix with an additional trailing /. """

	cseCsi:str = None
	""" The CSE-ID. """

	cseCsiSlash:str = None
	""" The CSE-ID with an additional trailing /. """

	cseCsiSlashLen:int = 0
	""" Length of the CSI with a slash. """

	cseCsiSlashLess:str = None
	""" The CSE-ID without the leading /. """

	cseOriginator:str = None
	"""	The CSE's admin originator, e.g. "CAdmin". """

	csePOA:list[str] = []
	""" The CSE's point-of-access's. """

	cseRi:str = None
	""" The CSE's Resource ID. """

	cseRn:str = None
	""" The CSE's Resource Name. """

	slashCseOriginator:str = None
	"""	The CSE's admin originator with a leading /. """

	cseSpid:str = None
	""" The Service Provider ID. """

	cseSPRelative:str = None
	"""	The SP-Relative CSE-ID. """

	cseStatus:CSEStatus = None
	""" The CSE's internal runtime status. """

	cseType:CSEType = None
	""" The kind of CSE: IN, MN, or ASN. """

	defaultSerialization:ContentSerializationType = None
	""" The default / preferred content serialization type. """

	isHeadless = False
	""" Indicator whether the CSE is running in headless mode. """

	releaseVersion:str = None
	""" The default / preferred release version. """

	supportedReleaseVersions:list[str] = None
	"""	List of the supported release versions. """

	idLength	= 10
	"""	Length of identifiers generated by the CSE. """
