#
#	CoAPthonTools.py
#
#	(c) 2024 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	This module provides helper functions to work with CoAPthon.
"""

from ..etc.Types import Operation
from coapthon import defines
from coapthon.messages.option import Option as CoapthonOption


operationsMethodsMap = {
	Operation.RETRIEVE: defines.Codes.GET.number,
	Operation.CREATE: defines.Codes.POST.number,
	Operation.UPDATE: defines.Codes.PUT.number,
	Operation.DELETE: defines.Codes.DELETE.number,
}
"""	Maps the oneM2M operation to the CoAP method number."""


#
#	Adding oneM2M options and content types to CoAPthon
#

def registerOneM2MOptions() -> None:
	"""	Register the oneM2M options with CoAPthon.
	"""

	defines.OptionRegistry.oneM2M_OT = defines.OptionItem(259, "oneM2M-OT", defines.STRING, False, None)			# type:ignore[attr-defined]
	defines.OptionRegistry.LIST[259]= defines.OptionRegistry.oneM2M_OT												# type:ignore[attr-defined]		
	
	defines.OptionRegistry.oneM2M_RTURI = defines.OptionItem(263, "oneM2M-RTURI", defines.STRING, False, None)		# type:ignore[attr-defined]
	defines.OptionRegistry.LIST[263]= defines.OptionRegistry.oneM2M_RTURI											# type:ignore[attr-defined]
	
	defines.OptionRegistry.oneM2M_TY = defines.OptionItem(267, "oneM2M-TY", defines.INTEGER, True, None)			# type:ignore[attr-defined]
	defines.OptionRegistry.LIST[267]= defines.OptionRegistry.oneM2M_TY												# type:ignore[attr-defined]	

	defines.OptionRegistry.oneM2M_RVI = defines.OptionItem(271, "oneM2M-RVI", defines.STRING, False, None)			# type:ignore[attr-defined]	
	defines.OptionRegistry.LIST[271]= defines.OptionRegistry.oneM2M_RVI												# type:ignore[attr-defined]	

	defines.OptionRegistry.oneM2M_ASRI = defines.OptionItem(275, "oneM2M-ASRI", defines.STRING, False, None)		# type:ignore[attr-defined]
	defines.OptionRegistry.LIST[275]= defines.OptionRegistry.oneM2M_ASRI											# type:ignore[attr-defined]		

	defines.OptionRegistry.oneM2M_FR = defines.OptionItem(279, "oneM2M-FR", defines.STRING, False, None)			# type:ignore[attr-defined]	
	defines.OptionRegistry.LIST[279]= defines.OptionRegistry.oneM2M_FR												# type:ignore[attr-defined]

	defines.OptionRegistry.oneM2M_RQI = defines.OptionItem(283, "oneM2M-RQI", defines.STRING, False, None)			# type:ignore[attr-defined]
	defines.OptionRegistry.LIST[283]= defines.OptionRegistry.oneM2M_RQI												# type:ignore[attr-defined]

	defines.OptionRegistry.oneM2M_RQET = defines.OptionItem(291, "oneM2M-RQET", defines.STRING, False, None)		# type:ignore[attr-defined]
	defines.OptionRegistry.LIST[291]= defines.OptionRegistry.oneM2M_RQET											# type:ignore[attr-defined]

	defines.OptionRegistry.oneM2M_RSET = defines.OptionItem(295, "oneM2M-RSET", defines.STRING, False, None)		# type:ignore[attr-defined]
	defines.OptionRegistry.LIST[295]= defines.OptionRegistry.oneM2M_RSET											# type:ignore[attr-defined]

	defines.OptionRegistry.oneM2M_OET = defines.OptionItem(299, "oneM2M-OET", defines.STRING, False, None)			# type:ignore[attr-defined]
	defines.OptionRegistry.LIST[299]= defines.OptionRegistry.oneM2M_OET												# type:ignore[attr-defined]

	defines.OptionRegistry.oneM2M_EC = defines.OptionItem(303, "oneM2M-EC", defines.INTEGER, False, None)			# type:ignore[attr-defined]
	defines.OptionRegistry.LIST[303]= defines.OptionRegistry.oneM2M_EC												# type:ignore[attr-defined]

	defines.OptionRegistry.oneM2M_RSC = defines.OptionItem(307, "oneM2M-RSC", defines.INTEGER, False, None)			# type:ignore[attr-defined]
	defines.OptionRegistry.LIST[307]= defines.OptionRegistry.oneM2M_RSC												# type:ignore[attr-defined]

	defines.OptionRegistry.oneM2M_GID = defines.OptionItem(311, "oneM2M-GID", defines.STRING, False, None)			# type:ignore[attr-defined]
	defines.OptionRegistry.LIST[311]= defines.OptionRegistry.oneM2M_GID												# type:ignore[attr-defined]

	defines.OptionRegistry.oneM2M_CTO = defines.OptionItem(319, "oneM2M-CTO", defines.INTEGER, False, None)			# type:ignore[attr-defined]
	defines.OptionRegistry.LIST[319]= defines.OptionRegistry.oneM2M_CTO												# type:ignore[attr-defined]

	defines.OptionRegistry.oneM2M_CTS = defines.OptionItem(323, "oneM2M-CTS", defines.INTEGER, False, None)			# type:ignore[attr-defined]
	defines.OptionRegistry.LIST[323]= defines.OptionRegistry.oneM2M_CTS												# type:ignore[attr-defined]

	defines.OptionRegistry.oneM2M_ATI = defines.OptionItem(327, "oneM2M-ATI", defines.STRING, False, None)			# type:ignore[attr-defined]
	defines.OptionRegistry.LIST[327]= defines.OptionRegistry.oneM2M_ATI												# type:ignore[attr-defined]

	defines.OptionRegistry.oneM2M_VSI = defines.OptionItem(331, "oneM2M-VSI", defines.STRING, False, None)			# type:ignore[attr-defined]
	defines.OptionRegistry.LIST[331]= defines.OptionRegistry.oneM2M_VSI												# type:ignore[attr-defined]

	defines.OptionRegistry.oneM2M_GTM = defines.OptionItem(335, "oneM2M-GTM", defines.STRING, False, None)			# type:ignore[attr-defined]
	defines.OptionRegistry.LIST[335]= defines.OptionRegistry.oneM2M_GTM												# type:ignore[attr-defined]

	defines.OptionRegistry.oneM2M_AUS = defines.OptionItem(339, "oneM2M-AUS", defines.STRING, False, None)			# type:ignore[attr-defined]
	defines.OptionRegistry.LIST[339]= defines.OptionRegistry.oneM2M_AUS												# type:ignore[attr-defined]

	defines.OptionRegistry.oneM2M_OMR = defines.OptionItem(343, "oneM2M-OMR", defines.STRING, False, None)			# type:ignore[attr-defined]
	defines.OptionRegistry.LIST[343]= defines.OptionRegistry.oneM2M_OMR												# type:ignore[attr-defined]

	defines.OptionRegistry.oneM2M_PRPI = defines.OptionItem(347, "oneM2M-PRPI", defines.STRING, False, None)		# type:ignore[attr-defined]
	defines.OptionRegistry.LIST[347]= defines.OptionRegistry.oneM2M_PRPI											# type:ignore[attr-defined]

	defines.OptionRegistry.oneM2M_MSU = defines.OptionItem(351, "oneM2M-MSU", defines.STRING, False, None)			# type:ignore[attr-defined]
	defines.OptionRegistry.LIST[351]= defines.OptionRegistry.oneM2M_MSU												# type:ignore[attr-defined]



def registerOneM2MContentTypes() -> None:
	"""	Register the oneM2M content types with CoAPthon.
	"""
	defines.Content_types['vnd.onem2m-res+xml'] = 10014
	defines.Content_types['vnd.onem2m-res+json'] = 10001
	defines.Content_types['vnd.onem2m-ntfy+xml'] = 10002
	defines.Content_types['vnd.onem2m-ntfy+json'] = 10003
	defines.Content_types['vnd.onem2m-preq+xml'] = 10006
	defines.Content_types['vnd.onem2m-preq+json'] = 10007
	defines.Content_types['vnd.onem2m-prsp+xml'] = 10008
	defines.Content_types['vnd.onem2m-prsp+json'] = 10009
	defines.Content_types['vnd.onem2m-res+cbor'] = 10010
	defines.Content_types['vnd.onem2m-ntfy+cbor'] = 10011
	defines.Content_types['vnd.onem2m-preq+cbor'] = 10012
	defines.Content_types['vnd.onem2m-prsp+cbor'] = 10013
	defines.Content_types['application/vnd.onem2m-res+xml'] = 10014
	defines.Content_types['application/vnd.onem2m-res+json'] = 10015
	defines.Content_types['application/vnd.onem2m-ntfy+xml'] = 10016
	defines.Content_types['application/vnd.onem2m-ntfy+json'] = 10003
	defines.Content_types['application/vnd.onem2m-preq+xml'] = 10006
	defines.Content_types['application/vnd.onem2m-preq+json'] = 10007
	defines.Content_types['application/vnd.onem2m-prsp+xml'] = 10008
	defines.Content_types['application/vnd.onem2m-prsp+json'] = 10009
	defines.Content_types['application/vnd.onem2m-res+cbor'] = 10010
	defines.Content_types['application/vnd.onem2m-ntfy+cbor'] = 10011
	defines.Content_types['application/vnd.onem2m-preq+cbor'] = 10012
	defines.Content_types['application/vnd.onem2m-prsp+cbor'] = 10013

	defines.build_content_types_numbers()


#
#	Helper functions
#

def newCoAPOption(number:int, value:str|int) -> CoapthonOption:
	"""	Create a new CoAP option.
	
		Args:
			number: The option number.
			value: The option value.

		Returns:
			The new CoAP option instance.
	"""
	option = CoapthonOption()
	option.number = number
	option.value = value
	return option
