#
#	Constants.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
""" Various CSE and oneM2M constants """


class Constants(object):
	""" Various CSE and oneM2M constants """

	
	version	= '0.12.0'
	"""	ACME's release version """

	logoColor = '#b42025'
	"""	oneM2M logo colour """
	
	textLogo = f'[dim][[/dim][{logoColor}][i]ACME[/i][/{logoColor}][dim]][/dim]'
	"""	ACME's colorful console logo """

	copyright = '(c) 2023 by Andreas Kraft'
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

	attrRtype = '__rtype__'
	"""	Constant: Name of the `Resource` internal *__rtype__* attribute. This attribute holds the resource type name, e.g. "m2m:cnt". """

	attrSrn = '__srn__'
	"""	Constant: Name of the `Resource` internal *__srn__* attribute. This attribute holds the resource's structured resource name. """

	attrNode = '__node__'
	"""	Constant: Name of the `Resource` internal __node__ attribute. This attribute is used in some resource types to hold a reference to the hosting <node> resource. """

	attrCreatedInternallyRI = '__createdInternallyRI__'
	""" Constant: Name of the `Resource` internal *__createdInternally__* attribute. This attribute indicates whether a resource was created internally or by an external request. """

	attrImported = '__imported__'
	""" Constant: Name of the `Resource` internal *__imported__* attribute. This attribute indicates whether a resource was imported or created by a script, of created by a request. """

	attrAnnouncedTo = '__announcedTo__'			# List
	""" Constant: Name of the 'Resource' internal *__announcedTo__* attribute. This attribute holds internal announcement information. """

	attrIsInstantiated = '__isInstantiated__'
	""" Constant: Name of the `Resource` internal *__isInstantiated__* attribute. This attribute indicates whether a resource is instantiated. """

	attrOriginator = '__originator__'			# Or creator
	""" Constant: Name of the `Resource` internal *__originator__* attribute. This attribute holds the original creator of a resource."""

	attrModified = '__modified__'
	""" Constant: Name of the `Resource` internal *__modified__* attribute. This attribute holds the resource's precise modification timestamp. """

	attrRemoteID = '__remoteID__'			# When this is a resource from another CSE
	""" Constant: Name of the `Resource` internal *__remoteID__* attribute. This attribute holds a list of the resource's announced variants. """

	attrRvi = '__rvi__'					# Request version indicator when created
	""" Constant: Name of the `Resource` internal *__rvi__* attribute. This attribute holds the Release Version Indicator for which the resource was created. """

	attrLaRi = '__lari__'
	""" Constant: Name of the 'Resource internal *__lari__* attribute. This attribute holds the resourceID's of the *latest* child-resource for some resource types. """

	attrOlRi = '__olri__'
	""" Constant: Name of the 'Resource internal *__olri__* attribute. This attribute holds the resourceID's of the *oldest* child-resource for some resource types. """

	attrRiTyMapping = '__riTyMapping__'
	""" Constant: Name of the 'Resource internal *__riTyMapping__* attribute. This attribute holds the mapping of resourceID's to resource types. """
 
	attrExpireTime = '__et__'
	""" Constant: Name of the Resource internal *__et__* attribute. This attribute holds resource expiretime in python datetime object"""


	#
	#	Supported URL schemes
	#
	supportedSchemes = ['http', 'https', 'mqtt', 'mqtts', 'acme']
	""" The URL schemes supported by the CSE """


	#
	#	Magic strings and numbers
	#

	maxIDLength	= 10
	"""	Maximum length of identifiers generated by the CSE """


	
