 #
#	ResponseStatusCodes.py
#
#	(c) 2022 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
""" Type definitions and Exceptions for ResponseStatusCodes. """

from __future__ import annotations
from typing import Optional, Any, Type
from http import HTTPStatus
from coapthon.defines import Codes as CoAPCodes, CodeItem as CoAPCodeItem
from ..helpers.ACMEIntEnum import ACMEIntEnum

##############################################################################
#
#	Response Codes
#

class ResponseStatusCode(ACMEIntEnum):
	""" Response codes """

	ACCEPTED									= 1000
	"""	Request accepted """
	ACCEPTED_NON_BLOCKING_REQUEST_SYNC			= 1001
	"""	ACCEPTED for nonBlockingRequestSynch """
	ACCEPTED_NON_BLOCKING_REQUEST_ASYNC			= 1002
	"""	ACCEPTED for nonBlockingRequestAsynch """

	OK											= 2000
	"""	OK """
	CREATED 									= 2001
	"""	CREATED """
	DELETED 									= 2002
	"""	DELETED """
	UPDATED										= 2004
	"""	UPDATED """

	BAD_REQUEST									= 4000
	"""	BAD REQUEST """
	RELEASE_VERSION_NOT_SUPPORTED				= 4001
	"""	RELEASE VERSION NOT SUPPORTED """
	NOT_FOUND 									= 4004
	"""	NOT FOUND """
	OPERATION_NOT_ALLOWED						= 4005
	"""	OPERATION NOT ALLOWED """
	REQUEST_TIMEOUT 							= 4008
	"""	REQUEST TIMEOUT """
	UNSUPPORTED_MEDIA_TYPE						= 4015
	"""	UNSUPPORTED MEDIA TYPE """
	SUBSCRIPTION_CREATER_HAS_NO_PRIVILEGE		= 4101
	"""	SUBSCRIPTION CREATOR HAS NO PRIVILEGE """
	CONTENTS_UNACCEPTABLE						= 4102
	"""	CONTENTS UNACCEPTABLE """
	ORIGINATOR_HAS_NO_PRIVILEGE					= 4103
	""" ORIGINATOR HAS NO PRIVILEGE """
	CONFLICT									= 4105
	"""	CONFLICT """
	SECURITY_ASSOCIATION_REQUIRED				= 4107
	"""	SECURITY_ASSOCIATION_REQUIRED """
	INVALID_CHILD_RESOURCE_TYPE					= 4108
	"""	INVALID CHILD RESOURCE TYPE """
	GROUP_MEMBER_TYPE_INCONSISTENT				= 4110
	"""	GROUP MEMBER TYPE INCONSISTENT """
	ORIGINATOR_HAS_ALREADY_REGISTERED			= 4117
	"""	ORIGINATOR_HAS_ALREADY_REGISTERED """
	APP_RULE_VALIDATION_FAILED					= 4126
	"""	APP RULE VALIDATION FAILED """
	OPERATION_DENIED_BY_REMOTE_ENTITY			= 4127
	"""	OPERATION_DENIED_BY_REMOTE_ENTITY """
	SERVICE_SUBSCRIPTION_NOT_ESTABLISHED		= 4128
	"""	SERVICE_SUBSCRIPTION_NOT_ESTABLISHED """
	INVALID_PROCESS_CONFIGURATION				= 4142
	"""	INVALID PROCESS CONFIGURATION """
	INVALID_SPARQL_QUERY 						= 4143
	"""	INVALID_SPARQL_QUERY """
	INTERNAL_SERVER_ERROR						= 5000
	"""	INTERNAL SERVER ERROR """
	NOT_IMPLEMENTED								= 5001
	"""	NOT_IMPLEMENTED """
	TARGET_NOT_REACHABLE 						= 5103
	"""	TARGET NOT REACHABLE """
	RECEIVER_HAS_NO_PRIVILEGES					= 5105
	"""	RECEIVER_HAS_NO_PRIVILEGES """
	ALREADY_EXISTS								= 5106
	"""	ALREADY_EXISTS """
	REMOTE_ENTITY_NOT_REACHABLE					= 5107
	"""	REMOTE ENTITY NOT REACHABLE """
	TARGET_NOT_SUBSCRIBABLE						= 5203
	"""	TARGET NOT SUBSCRIBABLE """
	SUBSCRIPTION_VERIFICATION_INITIATION_FAILED	= 5204
	"""	SUBSCRIPTION VERIFICATION INITIATION FAILED """
	SUBSCRIPTION_HOST_HAS_NO_PRIVILEGE			= 5205
	"""	SUBSCRIPTION_HOST_HAS_NO_PRIVILEGE """
	NOT_ACCEPTABLE 								= 5207
	"""	NOT ACCEPTABLE """
	UNABLE_TO_RECALL_REQUEST					= 5220
	"""	UNABLE TO RECALL REQUEST """
	CROSS_RESOURCE_OPERATION_FAILURE 			= 5221
	"""	CROSS RESOURCE OPERATION FAILURE """
	MAX_NUMBER_OF_MEMBER_EXCEEDED				= 6010
	"""	MAX NUMBER OF MEMBER EXCEEDED """
	INVALID_ARGUMENTS							= 6023
	"""	INVALID ARGUMENTS """
	INSUFFICIENT_ARGUMENTS						= 6024
	"""	INSUFFICIENT_ARGUMENTS """

	UNKNOWN										= -1
	"""	Internal Status Code: UNKNOWN """

	NO_CONTENT									= -2
	""" Internal Status Code: No content"""


	def httpStatusCode(self) -> int:
		""" Map the oneM2M RSC to an http status code. """
		return _ResponseStatusCodeHttpStatusCodes[self][0]


	def coapStatusCode(self) -> CoAPCodeItem:
		""" Map the oneM2M RSC to a CoAP status code. """
		return _ResponseStatusCodeHttpStatusCodes[self][1]


	def nname(self) -> str:
		""" Return a "natural" string representation of the exception's name.

			Returns:
				A "natural" string representation of the exception's name.
		"""
		return f'{self.name.replace("_", " ")}'


#
#	Mapping of oneM2M return codes to http status codes
#

_ResponseStatusCodeHttpStatusCodes = {
	ResponseStatusCode.OK 											: (HTTPStatus.OK, CoAPCodes.CONTENT),											# OK
	ResponseStatusCode.DELETED 										: (HTTPStatus.OK, CoAPCodes.DELETED),											# DELETED
	ResponseStatusCode.UPDATED 										: (HTTPStatus.OK, CoAPCodes.CHANGED),											# UPDATED
	ResponseStatusCode.CREATED										: (HTTPStatus.CREATED, CoAPCodes.CREATED),										# CREATED
	ResponseStatusCode.ACCEPTED 									: (HTTPStatus.ACCEPTED, CoAPCodes.VALID), 										# ACCEPTED
	ResponseStatusCode.ACCEPTED_NON_BLOCKING_REQUEST_SYNC 			: (HTTPStatus.ACCEPTED, CoAPCodes.CREATED),										# ACCEPTED FOR NONBLOCKINGREQUESTSYNCH
	ResponseStatusCode.ACCEPTED_NON_BLOCKING_REQUEST_ASYNC 			: (HTTPStatus.ACCEPTED, CoAPCodes.CREATED),										# ACCEPTED FOR NONBLOCKINGREQUESTASYNCH
	ResponseStatusCode.BAD_REQUEST									: (HTTPStatus.BAD_REQUEST, CoAPCodes.BAD_REQUEST),								# BAD REQUEST
	ResponseStatusCode.CONTENTS_UNACCEPTABLE						: (HTTPStatus.BAD_REQUEST, CoAPCodes.NOT_ACCEPTABLE),							# NOT ACCEPTABLE
	ResponseStatusCode.INSUFFICIENT_ARGUMENTS 						: (HTTPStatus.BAD_REQUEST, CoAPCodes.BAD_REQUEST),								# INSUFFICIENT ARGUMENTS
	ResponseStatusCode.INVALID_ARGUMENTS							: (HTTPStatus.BAD_REQUEST, CoAPCodes.BAD_REQUEST),								# INVALID ARGUMENTS
	ResponseStatusCode.MAX_NUMBER_OF_MEMBER_EXCEEDED				: (HTTPStatus.BAD_REQUEST, CoAPCodes.BAD_REQUEST), 								# MAX NUMBER OF MEMBER EXCEEDED
	ResponseStatusCode.GROUP_MEMBER_TYPE_INCONSISTENT				: (HTTPStatus.BAD_REQUEST, CoAPCodes.BAD_REQUEST),								# GROUP MEMBER TYPE INCONSISTENT
	ResponseStatusCode.INVALID_PROCESS_CONFIGURATION				: (HTTPStatus.BAD_REQUEST, CoAPCodes.BAD_REQUEST),								# INVALID PROCESS CONFIGURATION
	ResponseStatusCode.INVALID_SPARQL_QUERY							: (HTTPStatus.BAD_REQUEST, CoAPCodes.BAD_REQUEST),								# INVALID SPARQL QUERY
	ResponseStatusCode.SERVICE_SUBSCRIPTION_NOT_ESTABLISHED			: (HTTPStatus.FORBIDDEN, CoAPCodes.FORBIDDEN),									# SERVICE SUBSCRIPTION NOT ESTABLISHED
	ResponseStatusCode.ORIGINATOR_HAS_NO_PRIVILEGE					: (HTTPStatus.FORBIDDEN, CoAPCodes.FORBIDDEN),									# ORIGINATOR HAS NO PRIVILEGE
	ResponseStatusCode.INVALID_CHILD_RESOURCE_TYPE					: (HTTPStatus.FORBIDDEN, CoAPCodes.FORBIDDEN),									# INVALID CHILD RESOURCE TYPE
	ResponseStatusCode.ALREADY_EXISTS								: (HTTPStatus.CONFLICT, CoAPCodes.BAD_REQUEST),									# ALREAD EXISTS
	ResponseStatusCode.TARGET_NOT_SUBSCRIBABLE						: (HTTPStatus.FORBIDDEN, CoAPCodes.FORBIDDEN),									# TARGET NOT SUBSCRIBABLE
	ResponseStatusCode.RECEIVER_HAS_NO_PRIVILEGES					: (HTTPStatus.FORBIDDEN, CoAPCodes.FORBIDDEN),									# RECEIVER HAS NO PRIVILEGE
	ResponseStatusCode.SECURITY_ASSOCIATION_REQUIRED				: (HTTPStatus.FORBIDDEN, CoAPCodes.FORBIDDEN),									# SECURITY ASSOCIATION REQUIRED
	ResponseStatusCode.SUBSCRIPTION_CREATER_HAS_NO_PRIVILEGE		: (HTTPStatus.FORBIDDEN, CoAPCodes.FORBIDDEN ),									# SUBSCRIPTION CREATOR HAS NO PRIVILEGE
	ResponseStatusCode.SUBSCRIPTION_HOST_HAS_NO_PRIVILEGE			: (HTTPStatus.FORBIDDEN, CoAPCodes.FORBIDDEN),									# SUBSCRIPTION HOST HAS NO PRIVILEGE
	ResponseStatusCode.ORIGINATOR_HAS_ALREADY_REGISTERED			: (HTTPStatus.FORBIDDEN, CoAPCodes.FORBIDDEN),									# ORIGINATOR HAS ALREADY REGISTERED
	ResponseStatusCode.APP_RULE_VALIDATION_FAILED					: (HTTPStatus.FORBIDDEN, CoAPCodes.FORBIDDEN),									# APP RULE VALIDATION FAILED
	ResponseStatusCode.OPERATION_DENIED_BY_REMOTE_ENTITY			: (HTTPStatus.FORBIDDEN, CoAPCodes.FORBIDDEN),									# OPERATION_DENIED_BY_REMOTE_ENTITY
	ResponseStatusCode.REQUEST_TIMEOUT								: (HTTPStatus.GATEWAY_TIMEOUT, CoAPCodes.GATEWAY_TIMEOUT),						# REQUEST TIMEOUT
	ResponseStatusCode.NOT_FOUND									: (HTTPStatus.NOT_FOUND, CoAPCodes.NOT_FOUND),									# NOT FOUND
	ResponseStatusCode.TARGET_NOT_REACHABLE							: (HTTPStatus.NOT_FOUND, CoAPCodes.NOT_FOUND),									# TARGET NOT REACHABLE
	ResponseStatusCode.REMOTE_ENTITY_NOT_REACHABLE					: (HTTPStatus.NOT_FOUND, CoAPCodes.NOT_FOUND),									# REMOTE_ENTITY_NOT_REACHABLE
	ResponseStatusCode.OPERATION_NOT_ALLOWED						: (HTTPStatus.METHOD_NOT_ALLOWED, CoAPCodes.METHOD_NOT_ALLOWED),				# OPERATION NOT ALLOWED
	ResponseStatusCode.NOT_ACCEPTABLE 								: (HTTPStatus.NOT_ACCEPTABLE, CoAPCodes.NOT_ACCEPTABLE),						# NOT ACCEPTABLE
	ResponseStatusCode.UNABLE_TO_RECALL_REQUEST 					: (HTTPStatus.CONFLICT, CoAPCodes.SERVICE_UNAVAILABLE),							# UNABLE TO RECALL REQUEST
	ResponseStatusCode.CROSS_RESOURCE_OPERATION_FAILURE				: (HTTPStatus.INTERNAL_SERVER_ERROR, CoAPCodes.INTERNAL_SERVER_ERROR),			# CROSS RESOURCE OPERATION FAILURE
	ResponseStatusCode.CONFLICT										: (HTTPStatus.CONFLICT, CoAPCodes.FORBIDDEN),									# CONFLICT
	ResponseStatusCode.UNSUPPORTED_MEDIA_TYPE						: (HTTPStatus.UNSUPPORTED_MEDIA_TYPE, CoAPCodes.UNSUPPORTED_CONTENT_FORMAT),	# UNSUPPORTED_MEDIA_TYPE
	ResponseStatusCode.INTERNAL_SERVER_ERROR 						: (HTTPStatus.INTERNAL_SERVER_ERROR, CoAPCodes.INTERNAL_SERVER_ERROR),			# INTERNAL SERVER ERROR
	ResponseStatusCode.SUBSCRIPTION_VERIFICATION_INITIATION_FAILED	: (HTTPStatus.INTERNAL_SERVER_ERROR, CoAPCodes.INTERNAL_SERVER_ERROR),			# SUBSCRIPTION_VERIFICATION_INITIATION_FAILED
	ResponseStatusCode.RELEASE_VERSION_NOT_SUPPORTED				: (HTTPStatus.NOT_IMPLEMENTED, CoAPCodes.NOT_IMPLEMENTED),						# RELEASE_VERSION_NOT_SUPPORTED
	ResponseStatusCode.NOT_IMPLEMENTED								: (HTTPStatus.NOT_IMPLEMENTED, CoAPCodes.NOT_IMPLEMENTED),						# NOT IMPLEMENTED
	
	ResponseStatusCode.UNKNOWN										: (HTTPStatus.NOT_IMPLEMENTED, CoAPCodes.NOT_IMPLEMENTED),						# NOT IMPLEMENTED

}
""" Mapping of oneM2M return codes to http status codes. """

_successRSC = (
	ResponseStatusCode.ACCEPTED,
	ResponseStatusCode.ACCEPTED_NON_BLOCKING_REQUEST_SYNC,
	ResponseStatusCode.ACCEPTED_NON_BLOCKING_REQUEST_ASYNC,
	ResponseStatusCode.OK,
	ResponseStatusCode.CREATED,
	ResponseStatusCode.DELETED,
	ResponseStatusCode.UPDATED,
)
""" The list of success response status codes. """


def isSuccessRSC(rsc:ResponseStatusCode) -> bool:
	""" Check whether a response status code is a success code. 
	
		Args:
			rsc: The response status code to check.
			
		Returns:
			True if the response status code is a success code, False otherwise.
"""
	return rsc in _successRSC


class ResponseException(Exception):
	"""	Base class for CSE Exceptions."""

	def __init__(self, rsc:ResponseStatusCode, 
					   dbg:Optional[str] = None,
					   data:Optional[Any] = None) -> None:
		""" Constructor.
		
			Args:
				rsc: The response status code.
				dbg: An optional debug message.
				data: Optional data.
		"""
		super().__init__()
		self.rsc = rsc
		""" The response status code. """
		self.dbg = dbg
		""" An optional debug message. """
		self.data = data
		""" Optional data. """
	
	def __str__(self) -> str:
		""" Return a string representation of the exception.

			Returns:
				A string representation of the exception.
		"""
		return f'{self.__class__.__name__}({self.rsc}, {self.dbg})'


	def nname(self) -> str:
		""" Return a "natural" string representation of the exception's name.

			Returns:
				A "natural" string representation of the exception's name.
		"""
		return self.rsc.nname()


class ALREADY_EXISTS(ResponseException):
	"""	ALREADY EXISTS Response Status Code.
	"""
	def __init__(self, dbg: Optional[str] = None, data:Optional[Any] = None) -> None:
		""" Constructor.
		
			Args:
				dbg: An optional debug message.
				data: Optional data.
		"""
		super().__init__(ResponseStatusCode.ALREADY_EXISTS, dbg, data)


class APP_RULE_VALIDATION_FAILED(ResponseException):
	"""	APP RULE VALIDATION FAILED Response Status Code.
	"""
	def __init__(self, dbg: Optional[str] = None, data:Optional[Any] = None) -> None:
		"""	Constructor.

			Args:
				dbg: An optional debug message.
				data: Optional data.
		"""
		super().__init__(ResponseStatusCode.APP_RULE_VALIDATION_FAILED, dbg, data)


class BAD_REQUEST(ResponseException):
	"""	BAD REQUEST Response Status Code.
	"""
	def __init__(self, dbg: Optional[str] = None, data:Optional[Any] = None) -> None:
		"""	Constructor.
		
			Args:
				dbg: An optional debug message.
				data: Optional data.
		"""
		super().__init__(ResponseStatusCode.BAD_REQUEST, dbg, data)


class CONFLICT(ResponseException):
	"""	CONFLICT Response Status Code.
	"""
	def __init__(self, dbg: Optional[str] = None, data:Optional[Any] = None) -> None:
		"""	Constructor.
		
			Args:
				dbg: An optional debug message.
				data: Optional data.
		"""
		super().__init__(ResponseStatusCode.CONFLICT, dbg, data)


class CONTENTS_UNACCEPTABLE(ResponseException):
	"""	CONTENTS UNACCEPTABLE Response Status Code.
	"""
	def __init__(self, dbg: Optional[str] = None, data:Optional[Any] = None) -> None:
		"""	Constructor.
		
			Args:
				dbg: An optional debug message.
				data: Optional data.
		"""
		super().__init__(ResponseStatusCode.CONTENTS_UNACCEPTABLE, dbg, data)


class CROSS_RESOURCE_OPERATION_FAILURE(ResponseException):
	"""	CROSS RESOURCE OPERATION FAILURE Response Status Code.
	"""
	def __init__(self, dbg: Optional[str] = None, data:Optional[Any] = None) -> None:
		"""	Constructor.
		
			Args:
				dbg: An optional debug message.
				data: Optional data.
		"""
		super().__init__(ResponseStatusCode.CROSS_RESOURCE_OPERATION_FAILURE, dbg, data)


class GROUP_MEMBER_TYPE_INCONSISTENT(ResponseException):
	"""	GROUP MEMBER TYPE INCONSISTENT Response Status Code.
	"""
	def __init__(self, dbg: Optional[str] = None, data:Optional[Any] = None) -> None:
		"""	Constructor.
		
			Args:
				dbg: An optional debug message.
				data: Optional data.
		"""
		super().__init__(ResponseStatusCode.GROUP_MEMBER_TYPE_INCONSISTENT, dbg, data)


class INSUFFICIENT_ARGUMENTS(ResponseException):
	"""	INSUFFICIENT ARGUMENTS Response Status Code.
	"""
	def __init__(self, dbg: Optional[str] = None, data:Optional[Any] = None) -> None:
		"""	Constructor.
		
			Args:
				dbg: An optional debug message.
				data: Optional data.
		"""
		super().__init__(ResponseStatusCode.INSUFFICIENT_ARGUMENTS, dbg, data)


class INTERNAL_SERVER_ERROR(ResponseException):
	"""	INTERNAL SERVER ERRROR Response Status Code.
	"""
	def __init__(self, dbg: Optional[str] = None, data:Optional[Any] = None) -> None:
		"""	Constructor.
		
			Args:
				dbg: An optional debug message.
				data: Optional data.
		"""
		super().__init__(ResponseStatusCode.INTERNAL_SERVER_ERROR, dbg, data)


class INVALID_CHILD_RESOURCE_TYPE(ResponseException):
	"""	INVALID CHILD RESOURCE TYPE Response Status Code.
	"""
	def __init__(self, dbg: Optional[str] = None, data:Optional[Any] = None) -> None:
		"""	Constructor.
		
			Args:
				dbg: An optional debug message.
				data: Optional data.
		"""
		super().__init__(ResponseStatusCode.INVALID_CHILD_RESOURCE_TYPE, dbg, data)


class INVALID_ARGUMENTS(ResponseException):
	"""	INVALID ARGUMENTS Response Status Code.
	"""
	def __init__(self, dbg: Optional[str] = None, data:Optional[Any] = None) -> None:
		"""	Constructor.
		
			Args:
				dbg: An optional debug message.
				data: Optional data.
		"""
		super().__init__(ResponseStatusCode.INVALID_ARGUMENTS, dbg, data)


class INVALID_PROCESS_CONFIGURATION(ResponseException):
	"""	INVALID PROCESS CONFIGURATION Response Status Code.
	"""
	def __init__(self, dbg: Optional[str] = None, data:Optional[Any] = None) -> None:
		"""	Constructor.
		
			Args:
				dbg: An optional debug message.
				data: Optional data.
		"""
		super().__init__(ResponseStatusCode.INVALID_PROCESS_CONFIGURATION, dbg, data)


class INVALID_SPARQL_QUERY(ResponseException):
	"""	INVALID SPARQL QUERY Response Status Code.
	"""
	def __init__(self, dbg: Optional[str] = None, data:Optional[Any] = None) -> None:
		"""	Constructor.
		
			Args:
				dbg: An optional debug message.
				data: Optional data.
		"""
		super().__init__(ResponseStatusCode.INVALID_SPARQL_QUERY, dbg, data)


class MAX_NUMBER_OF_MEMBER_EXCEEDED(ResponseException):
	"""	MAX NUMBER OF MEMBER EXCEEDED Response Status Code.
	"""
	def __init__(self, dbg: Optional[str] = None, data:Optional[Any] = None) -> None:
		super().__init__(ResponseStatusCode.MAX_NUMBER_OF_MEMBER_EXCEEDED, dbg, data)


class NO_CONTENT(ResponseException):
	"""	NO CONTENT internal Response Status Code.
	"""
	def __init__(self, dbg: Optional[str] = None, data:Optional[Any] = None) -> None:
		"""	Constructor.
		
			Args:
				dbg: An optional debug message.
				data: Optional data.
		"""
		super().__init__(ResponseStatusCode.NO_CONTENT, dbg, data)


class NOT_ACCEPTABLE(ResponseException):
	"""	NOT ACCEPTABLE Response Status Code.
	"""
	def __init__(self, dbg: Optional[str] = None, data:Optional[Any] = None) -> None:
		"""	Constructor.
		
			Args:
				dbg: An optional debug message.
				data: Optional data.
		"""
		super().__init__(ResponseStatusCode.NOT_ACCEPTABLE, dbg, data)


class NOT_FOUND(ResponseException):
	"""	NOT FOUND Response Status Code.
	"""
	def __init__(self, dbg: Optional[str] = None, data:Optional[Any] = None) -> None:
		"""	Constructor.
		
			Args:
				dbg: An optional debug message.
				data: Optional data.
		"""
		super().__init__(ResponseStatusCode.NOT_FOUND, dbg, data)


class NOT_IMPLEMENTED(ResponseException):
	"""	NOT IMPLEMENTED Response Status Code.
	"""
	def __init__(self, dbg: Optional[str] = None, data:Optional[Any] = None) -> None:
		"""	Constructor.
		
			Args:
				dbg: An optional debug message.
				data: Optional data.
		"""
		super().__init__(ResponseStatusCode.NOT_IMPLEMENTED, dbg, data)


class OPERATION_DENIED_BY_REMOTE_ENTITY(ResponseException):
	"""	OPERATION DENIED BY REMOTE ENTITY Response Status Code.
	"""
	def __init__(self, dbg: Optional[str] = None, data:Optional[Any] = None) -> None:
		"""	Constructor.
		
			Args:
				dbg: An optional debug message.
				data: Optional data.
		"""
		super().__init__(ResponseStatusCode.OPERATION_DENIED_BY_REMOTE_ENTITY, dbg, data)


class OPERATION_NOT_ALLOWED(ResponseException):
	"""	OPERATION NOT ALLOWED Response Status Code.
	"""
	def __init__(self, dbg: Optional[str] = None, data:Optional[Any] = None) -> None:
		"""	Constructor.
		
			Args:
				dbg: An optional debug message.
				data: Optional data.
		"""
		super().__init__(ResponseStatusCode.OPERATION_NOT_ALLOWED, dbg, data)


class ORIGINATOR_HAS_ALREADY_REGISTERED(ResponseException):
	"""	ORIGINATOR HAS ALREADY REGISTERED Response Status Code.
	"""
	def __init__(self, dbg: Optional[str] = None, data:Optional[Any] = None) -> None:
		"""	Constructor.
		
			Args:
				dbg: An optional debug message.
				data: Optional data.
		"""
		super().__init__(ResponseStatusCode.ORIGINATOR_HAS_ALREADY_REGISTERED, dbg, data)


class ORIGINATOR_HAS_NO_PRIVILEGE(ResponseException):
	"""	ORIGINATOR HAS NO PRIVILEGE Response Status Code.
	"""
	def __init__(self, dbg: Optional[str] = None, data:Optional[Any] = None) -> None:
		"""	Constructor.
		
			Args:
				dbg: An optional debug message.
				data: Optional data.
		"""
		super().__init__(ResponseStatusCode.ORIGINATOR_HAS_NO_PRIVILEGE, dbg, data)


class RECEIVER_HAS_NO_PRIVILEGES(ResponseException):
	"""	RECEIVER HAS NO PRIVILEGES Response Status Code.
	"""
	def __init__(self, dbg: Optional[str] = None, data:Optional[Any] = None) -> None:
		"""	Constructor.
		
			Args:
				dbg: An optional debug message.
				data: Optional data.
		"""
		super().__init__(ResponseStatusCode.RECEIVER_HAS_NO_PRIVILEGES, dbg, data)


class RELEASE_VERSION_NOT_SUPPORTED(ResponseException):
	"""	RELEASE VERSION NOT SUPPORTED Response Status Code.
	"""
	def __init__(self, dbg: Optional[str] = None, data:Optional[Any] = None) -> None:
		"""	Constructor.
		
			Args:
				dbg: An optional debug message.
				data: Optional data.
		"""
		super().__init__(ResponseStatusCode.RELEASE_VERSION_NOT_SUPPORTED, dbg, data)


class REMOTE_ENTITY_NOT_REACHABLE(ResponseException):
	"""	REMOTE ENTITY NOT REACHABLE Response Status Code.
	"""
	def __init__(self, dbg: Optional[str] = None, data:Optional[Any] = None) -> None:
		"""	Constructor.
		
			Args:
				dbg: An optional debug message.
				data: Optional data.
		"""
		super().__init__(ResponseStatusCode.REMOTE_ENTITY_NOT_REACHABLE, dbg, data)


class REQUEST_TIMEOUT(ResponseException):
	"""	REQUEST TIMEOUT Response Status Code.
	"""
	def __init__(self, dbg: Optional[str] = None, data:Optional[Any] = None) -> None:
		"""	Constructor.
		
			Args:
				dbg: An optional debug message.
				data: Optional data.
		"""
		super().__init__(ResponseStatusCode.REQUEST_TIMEOUT, dbg, data)


class SECURITY_ASSOCIATION_REQUIRED(ResponseException):
	"""	SECURITY ASSOCIATION REQUIRED Response Status Code.
	"""
	def __init__(self, dbg: Optional[str] = None, data:Optional[Any] = None) -> None:
		"""	Constructor.
		
			Args:
				dbg: An optional debug message.
				data: Optional data.
		"""
		super().__init__(ResponseStatusCode.SECURITY_ASSOCIATION_REQUIRED, dbg, data)


class SERVICE_SUBSCRIPTION_NOT_ESTABLISHED(ResponseException):
	"""	SERVICE SUBSCRIPTION NOT ESTABLISHED Response Status Code.
	"""
	def __init__(self, dbg: Optional[str] = None, data:Optional[Any] = None) -> None:
		"""	Constructor.
		
			Args:
				dbg: An optional debug message.
				data: Optional data.
		"""
		super().__init__(ResponseStatusCode.SERVICE_SUBSCRIPTION_NOT_ESTABLISHED, dbg, data)


class SUBSCRIPTION_CREATER_HAS_NO_PRIVILEGE(ResponseException):
	"""	SUBSCRIPTION CREATER HAS NO PRIVILEGE Response Status Code.
	"""
	def __init__(self, dbg: Optional[str] = None, data:Optional[Any] = None) -> None:
		"""	Constructor.
		
			Args:
				dbg: An optional debug message.
				data: Optional data.
		"""
		super().__init__(ResponseStatusCode.SUBSCRIPTION_CREATER_HAS_NO_PRIVILEGE, dbg, data)


class SUBSCRIPTION_HOST_HAS_NO_PRIVILEGE(ResponseException):
	"""	SUBSCRIPTION HOST HAS NO PRIVILEGE Response Status Code.
	"""
	def __init__(self, dbg: Optional[str] = None, data:Optional[Any] = None) -> None:
		"""	Constructor.
		
			Args:
				dbg: An optional debug message.
				data: Optional data.
		"""
		super().__init__(ResponseStatusCode.SUBSCRIPTION_HOST_HAS_NO_PRIVILEGE, dbg, data)


class SUBSCRIPTION_VERIFICATION_INITIATION_FAILED(ResponseException):
	"""	SUBSCRIPTION VERIFICATION INITIATION FAILED Response Status Code.
	"""
	def __init__(self, dbg: Optional[str] = None, data:Optional[Any] = None) -> None:
		"""	Constructor.
		
			Args:
				dbg: An optional debug message.
				data: Optional data.
		"""
		super().__init__(ResponseStatusCode.SUBSCRIPTION_VERIFICATION_INITIATION_FAILED, dbg, data)


class TARGET_NOT_REACHABLE(ResponseException):
	"""	TARGET NOT REACHABLE Response Status Code.
	"""
	def __init__(self, dbg: Optional[str] = None, data:Optional[Any] = None) -> None:
		"""	Constructor.
		
			Args:
				dbg: An optional debug message.
				data: Optional data.
		"""
		super().__init__(ResponseStatusCode.TARGET_NOT_REACHABLE, dbg, data)


class TARGET_NOT_SUBSCRIBABLE(ResponseException):
	"""	TARGET NOT SUBSCRIBABLE Response Status Code.
	"""
	def __init__(self, dbg: Optional[str] = None, data:Optional[Any] = None) -> None:
		"""	Constructor.
		
			Args:
				dbg: An optional debug message.
				data: Optional data.
		"""
		super().__init__(ResponseStatusCode.TARGET_NOT_SUBSCRIBABLE, dbg, data)


class UNABLE_TO_RECALL_REQUEST(ResponseException):
	"""	UNABLE TO RECALL REQUEST Response Status Code.
	"""
	def __init__(self, dbg: Optional[str] = None, data:Optional[Any] = None) -> None:
		"""	Constructor.
		
			Args:
				dbg: An optional debug message.
				data: Optional data.
		"""
		super().__init__(ResponseStatusCode.UNABLE_TO_RECALL_REQUEST, dbg, data)


class UNSUPPORTED_MEDIA_TYPE(ResponseException):
	"""	UNSUPPORTED MEDIA TYPE Response Status Code.
	"""
	def __init__(self, dbg: Optional[str] = None, data:Optional[Any] = None) -> None:
		"""	Constructor.
		
			Args:
				dbg: An optional debug message.
				data: Optional data.
		"""
		super().__init__(ResponseStatusCode.UNSUPPORTED_MEDIA_TYPE, dbg, data)


_mapping = {
	ResponseStatusCode.ALREADY_EXISTS: ALREADY_EXISTS,
	ResponseStatusCode.APP_RULE_VALIDATION_FAILED: APP_RULE_VALIDATION_FAILED,
	ResponseStatusCode.BAD_REQUEST: BAD_REQUEST,
	ResponseStatusCode.CONFLICT: CONFLICT,
	ResponseStatusCode.CONTENTS_UNACCEPTABLE: CONTENTS_UNACCEPTABLE,
	ResponseStatusCode.CROSS_RESOURCE_OPERATION_FAILURE: CROSS_RESOURCE_OPERATION_FAILURE,
	ResponseStatusCode.GROUP_MEMBER_TYPE_INCONSISTENT: GROUP_MEMBER_TYPE_INCONSISTENT,
	ResponseStatusCode.INSUFFICIENT_ARGUMENTS: INSUFFICIENT_ARGUMENTS,
	ResponseStatusCode.INTERNAL_SERVER_ERROR: INTERNAL_SERVER_ERROR,
	ResponseStatusCode.INVALID_ARGUMENTS: INVALID_ARGUMENTS,
	ResponseStatusCode.INVALID_CHILD_RESOURCE_TYPE: INVALID_CHILD_RESOURCE_TYPE,
	ResponseStatusCode.INVALID_SPARQL_QUERY: INVALID_SPARQL_QUERY,
	ResponseStatusCode.MAX_NUMBER_OF_MEMBER_EXCEEDED: MAX_NUMBER_OF_MEMBER_EXCEEDED,
	ResponseStatusCode.NOT_ACCEPTABLE: NOT_ACCEPTABLE,
	ResponseStatusCode.NOT_FOUND: NOT_FOUND,
	ResponseStatusCode.NOT_IMPLEMENTED: NOT_IMPLEMENTED,
	ResponseStatusCode.OPERATION_DENIED_BY_REMOTE_ENTITY: OPERATION_DENIED_BY_REMOTE_ENTITY,
	ResponseStatusCode.OPERATION_NOT_ALLOWED: OPERATION_NOT_ALLOWED,
	ResponseStatusCode.ORIGINATOR_HAS_ALREADY_REGISTERED: ORIGINATOR_HAS_ALREADY_REGISTERED,
	ResponseStatusCode.ORIGINATOR_HAS_NO_PRIVILEGE: ORIGINATOR_HAS_NO_PRIVILEGE,
	ResponseStatusCode.RECEIVER_HAS_NO_PRIVILEGES: RECEIVER_HAS_NO_PRIVILEGES,
	ResponseStatusCode.RELEASE_VERSION_NOT_SUPPORTED: RELEASE_VERSION_NOT_SUPPORTED,
	ResponseStatusCode.REMOTE_ENTITY_NOT_REACHABLE: REMOTE_ENTITY_NOT_REACHABLE,
	ResponseStatusCode.REQUEST_TIMEOUT: REQUEST_TIMEOUT,
	ResponseStatusCode.SECURITY_ASSOCIATION_REQUIRED: SECURITY_ASSOCIATION_REQUIRED,
	ResponseStatusCode.SERVICE_SUBSCRIPTION_NOT_ESTABLISHED: SERVICE_SUBSCRIPTION_NOT_ESTABLISHED,
	ResponseStatusCode.SUBSCRIPTION_CREATER_HAS_NO_PRIVILEGE: SUBSCRIPTION_CREATER_HAS_NO_PRIVILEGE,
	ResponseStatusCode.SUBSCRIPTION_HOST_HAS_NO_PRIVILEGE: SUBSCRIPTION_HOST_HAS_NO_PRIVILEGE,
	ResponseStatusCode.SUBSCRIPTION_VERIFICATION_INITIATION_FAILED: SUBSCRIPTION_VERIFICATION_INITIATION_FAILED,
	ResponseStatusCode.TARGET_NOT_REACHABLE: TARGET_NOT_REACHABLE,
	ResponseStatusCode.TARGET_NOT_SUBSCRIBABLE: TARGET_NOT_SUBSCRIBABLE, 
	ResponseStatusCode.UNSUPPORTED_MEDIA_TYPE: UNSUPPORTED_MEDIA_TYPE,
}
"""	Mapping between Response Status Codes and exceptions. """


def exceptionFromRSC(rsc:ResponseStatusCode) -> Optional[Type[ResponseException]]:
	""" Get the exception class for a Response Status Code.
	
		Args:
			rsc: The Response Status Code.

		Returns:
			The exception class or None if not found.
	"""
	return _mapping.get(rsc)

