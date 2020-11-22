
from Logging import Logging

import collections
import array
import struct
import ctypes
import random
import string

class CoapMessage(object):
	def __init__(self):
		"""
		Data structure that represent a CoAP message
		"""
		self._type = None
		self._mid = None
		self._token = None
		self._options = []
		self._payload = None
		self._destination = None
		self._source = None
		self._code = None
		self._acknowledged = None
		self._rejected = None
		self._timeouted = None
		self._cancelled = None
		self._duplicated = None
		self._timestamp = None
		self._version = 1
		# End of ctor

	@property
	def version(self):
		"""
		Return the CoAP version

		:return: the version
		"""
		return self._version

	@version.setter
	def version(self, v):
		"""
		Sets the CoAP version

		:param v: the version
		:raise AttributeError: if value is not 1
		"""
		if not isinstance(v, int) or v != 1:
			raise AttributeError
		self._version = v

	@property
	def type(self):
		"""
		Return the type of the message.

		:return: the type
		"""
		return self._type

	@type.setter
	def type(self, value):
		"""
		Sets the type of the message.

		:type value: Types
		:param value: the type
		:raise AttributeError: if value is not a valid type
		"""
		if value not in list(CoapDissector.Types.values()):
			raise AttributeError
		self._type = value

	@property
	def mid(self):
		"""
		Return the mid of the message.

		:return: the MID
		"""
		return self._mid

	@mid.setter
	def mid(self, value):
		"""
		Sets the MID of the message.

		:type value: Integer
		:param value: the MID
		:raise AttributeError: if value is not int or cannot be represented on 16 bits.
		"""
		if not isinstance(value, int) or value > 65536:
			raise AttributeError
		self._mid = value

	@mid.deleter
	def mid(self):
		"""
		Unset the MID of the message.
		"""
		self._mid = None

	@property
	def token(self):
		"""
		Get the Token of the message.

		:return: the Token
		"""
		return self._token

	@token.setter
	def token(self, value):
		"""
		Set the Token of the message.

		:type value: String
		:param value: the Token
		:raise AttributeError: if value is longer than 256
		"""
		if value is None:
			self._token = value
			return
		if not isinstance(value, str):
			value = str(value)
		if len(value) > 256:
			raise AttributeError
		self._token = value

	@token.deleter
	def token(self):
		"""
		Unset the Token of the message.
		"""
		self._token = None

	@property
	def options(self):
		"""
		Return the options of the CoAP message.

		:rtype: list
		:return: the options
		"""
		return self._options

	@options.setter
	def options(self, value):
		"""
		Set the options of the CoAP message.

		:type value: list
		:param value: list of options
		"""
		if value is None:
			value = []
		assert isinstance(value, list)
		self._options = value

	@property
	def payload(self):
		"""
		Return the payload.

		:return: the payload
		"""
		return self._payload

	@payload.setter
	def payload(self, value):
		"""
		Sets the payload of the message and eventually the Content-Type

		:param value: the payload
		"""
		if isinstance(value, tuple):
			content_type, payload = value
			self.content_type = content_type
			self._payload = payload
		else:
			self._payload = value

	@property
	def destination(self):
		"""
		Return the destination of the message.

		:rtype: tuple
		:return: (ip, port)
		"""
		return self._destination

	@destination.setter
	def destination(self, value):
		"""
		Set the destination of the message.

		:type value: tuple
		:param value: (ip, port)
		:raise AttributeError: if value is not a ip and a port.
		"""
		if value is not None and (not isinstance(value, tuple) or len(value)) != 2:
			raise AttributeError
		self._destination = value

	@property
	def source(self):
		"""
		Return the source of the message.

		:rtype: tuple
		:return: (ip, port)
		"""
		return self._source

	@source.setter
	def source(self, value):
		"""
		Set the source of the message.

		:type value: tuple
		:param value: (ip, port)
		:raise AttributeError: if value is not a ip and a port.
		"""
		if not isinstance(value, tuple) or len(value) != 2:
			raise AttributeError
		self._source = value

	@property
	def code(self):
		"""
		Return the code of the message.

		:rtype: Codes
		:return: the code
		"""
		return self._code

	@code.setter
	def code(self, value):
		"""
		Set the code of the message.

		:type value: Codes
		:param value: the code
		:raise AttributeError: if value is not a valid code
		"""
		if value not in list(CoapDissector.LIST_CODES.keys()) and value is not None:
			raise AttributeError
		self._code = value

	@property
	def acknowledged(self):
		"""
		Checks if is this message has been acknowledged.

		:return: True, if is acknowledged
		"""
		return self._acknowledged

	@acknowledged.setter
	def acknowledged(self, value):
		"""
		Marks this message as acknowledged.

		:type value: Boolean
		:param value: if acknowledged
		"""
		assert (isinstance(value, bool))
		self._acknowledged = value
		if value:
			self._timeouted = False
			self._rejected = False
			self._cancelled = False

	@property
	def rejected(self):
		"""
		Checks if this message has been rejected.

		:return: True, if is rejected
		"""
		return self._rejected

	@rejected.setter
	def rejected(self, value):
		"""
		Marks this message as rejected.

		:type value: Boolean
		:param value: if rejected
		"""
		assert (isinstance(value, bool))
		self._rejected = value
		if value:
			self._timeouted = False
			self._acknowledged = False
			self._cancelled = True

	@property
	def timeouted(self):
		"""
		Checks if this message has timeouted. Confirmable messages in particular
		might timeout.

		:return: True, if has timeouted
		"""
		return self._timeouted

	@timeouted.setter
	def timeouted(self, value):
		"""
		Marks this message as timeouted. Confirmable messages in particular might
		timeout.

		:type value: Boolean
		:param value:
		"""
		assert (isinstance(value, bool))
		self._timeouted = value
		if value:
			self._acknowledged = False
			self._rejected = False
			self._cancelled = True

	@property
	def duplicated(self):
		"""
		Checks if this message is a duplicate.

		:return: True, if is a duplicate
		"""
		return self._duplicated

	@duplicated.setter
	def duplicated(self, value):
		"""
		Marks this message as a duplicate.

		:type value: Boolean
		:param value: if a duplicate
		"""
		assert (isinstance(value, bool))
		self._duplicated = value

	@property
	def timestamp(self):
		"""
		Return the timestamp of the message.
		"""
		return self._timestamp

	@timestamp.setter
	def timestamp(self, value):
		"""
		Set the timestamp of the message.

		:type value: timestamp
		:param value: the timestamp
		"""
		self._timestamp = value

	def _already_in(self, option):
		"""
		Check if an option is already in the message.

		:type option: CoapOption
		:param option: the option to be checked
		:return: True if already present, False otherwise
		"""
		for opt in self._options:
			if option.number == opt.number:
				return True
		return False

	def add_option(self, option):
		"""
		Add an option to the message.

		:type option: CoapOption
		:param option: the option
		:raise TypeError: if the option is not repeatable and such option is already present in the message
		"""
		assert isinstance(option, CoapOption)
		repeatable = CoapDissector.LIST_OPTIONS[option.number].repeatable
		if not repeatable:
			ret = self._already_in(option)
			if ret:
				raise TypeError("CoapOption : %s is not repeatable", option.name)
			else:
				self._options.append(option)
		else:
			self._options.append(option)

	def del_option(self, option):
		"""
		Delete an option from the message

		:type option: CoapOption
		:param option: the option
		"""
		assert isinstance(option, CoapOption)
		while option in list(self._options):
			self._options.remove(option)

	def del_option_by_name(self, name):
		"""
		Delete an option from the message by name

		:type name: String
		:param name: option name
		"""
		for o in list(self._options):
			assert isinstance(o, CoapOption)
			if o.name == name:
				self._options.remove(o)

	def del_option_by_number(self, number):
		"""
		Delete an option from the message by number

		:type number: Integer
		:param number: option naumber
		"""
		for o in list(self._options):
			assert isinstance(o, CoapOption)
			if o.number == number:
				self._options.remove(o)


	@property
	def uri_host(self):
		"""
		Get the ETag option of the message.

		:rtype: list
		:return: the ETag values or [] if not specified by the request
		"""
		value = []
		for option in self.options:
			if option.number == CoapDissector.URI_HOST.number:
				value.append(option.value)
		return value

	@uri_host.setter
	def uri_host(self, uri_host):
		"""
		Add an ETag option to the message.

		:param uri_host: the uri_host
		"""
		if not isinstance(uri_host, list):
			uri_host = [uri_host]
		for e in uri_host:
			option = CoapOption()
			option.number = CoapDissector.URI_HOST.number
			if not  isinstance(e, bytes):
				e = bytes(e, "utf-8")
			option.value = e
			self.add_option(option)

	@uri_host.deleter
	def uri_host(self):
		"""
		Delete an ETag from a message.

		"""
		self.del_option_by_number(CoapDissector.URI_HOST.number)

	@property
	def etag(self):
		"""
		Get the ETag option of the message.

		:rtype: list
		:return: the ETag values or [] if not specified by the request
		"""
		value = []
		for option in self.options:
			if option.number == CoapDissector.ETAG.number:
				value.append(option.value)
		return value

	@etag.setter
	def etag(self, etag):
		"""
		Add an ETag option to the message.

		:param etag: the etag
		"""
		if not isinstance(etag, list):
			etag = [etag]
		for e in etag:
			option = CoapOption()
			option.number = CoapDissector.ETAG.number
			if not  isinstance(e, bytes):
				e = bytes(e, "utf-8")
			option.value = e
			self.add_option(option)

	@etag.deleter
	def etag(self):
		"""
		Delete an ETag from a message.

		"""
		self.del_option_by_number(CoapDissector.ETAG.number)

	@property
	def observe(self):
		"""
		Check if the request is an observing request.

		:return: 0, if the request is an observing request
		"""
		for option in self.options:
			if option.number == CoapDissector.OBSERVE.number:
				if option.value is None:
					return 0
				return option.value
		return None

	@observe.setter
	def observe(self, ob):
		"""
		Add the Observe option.

		:param ob: observe count
		"""
		option = CoapOption()
		option.number = CoapDissector.OBSERVE.number
		option.value = ob
		self.del_option_by_number(CoapDissector.OBSERVE.number)
		self.add_option(option)

	@observe.deleter
	def observe(self):
		"""
		Delete the Observe option.
		"""
		self.del_option_by_number(CoapDissector.OBSERVE.number)

	@property
	def uri_port(self):
		"""
		Check if the request is an observing request.

		:return: 0, if the request is an observing request
		"""
		for option in self.options:
			if option.number == CoapDissector.URI_PORT.number:
				if option.value is None:
					return 0
				return option.value
		return None

	@uri_port.setter
	def uri_port(self, ob):
		"""
		Add the Observe option.

		:param ob: uri_port count
		"""
		option = CoapOption()
		option.number = CoapDissector.URI_PORT.number
		option.value = ob
		self.del_option_by_number(CoapDissector.URI_PORT.number)
		self.add_option(option)

	@uri_port.deleter
	def uri_port(self):
		"""
		Delete the Observe option.
		"""
		self.del_option_by_number(CoapDissector.URI_PORT.number)

	@property
	def uri_path(self):
		"""
		Check if the request is an observing request.

		:return: None, if the request is an observing request
		"""
		value = ""
		for option in self.options:
			if option.number == CoapDissector.URI_PATH.number:
				value += "/" + str(option.value)
		return value[1:]

	@uri_path.setter
	def uri_path(self, ob):
		"""
		Add the Observe option.

		:param ob: uri_path count
		"""
		option = CoapOption()
		option.number = CoapDissector.URI_PATH.number
		option.value = ob
		self.del_option_by_number(CoapDissector.URI_PATH.number)
		self.add_option(option)

	@uri_path.deleter
	def uri_path(self):
		"""
		Delete the Observe option.
		"""
		self.del_option_by_number(CoapDissector.URI_PATH.number)

	@property
	def location_path(self):
		"""
		Check if the request is an observing request.

		:return: 0, if the request is an observing request
		"""
		for option in self.options:
			if option.number == CoapDissector.LOCATION_PATH.number:
				return option.value
		return None

	@location_path.setter
	def location_path(self, ob):
		"""
		Add the Observe option.

		:param ob: location_path count
		"""
		option = CoapOption()
		option.number = CoapDissector.LOCATION_PATH.number
		option.value = ob
		self.del_option_by_number(CoapDissector.LOCATION_PATH.number)
		self.add_option(option)

	@location_path.deleter
	def location_path(self):
		"""
		Delete the Observe option.
		"""
		self.del_option_by_number(CoapDissector.LOCATION_PATH.number)

	@property
	def content_type(self):
		"""
		Get the Content-Type option of a response.

		:return: the Content-Type value or 0 if not specified by the response
		"""
		value = 0
		for option in self.options:
			if option.number == CoapDissector.CONTENT_TYPE.number:
				value = int(option.value)
				return value
		return value

	@content_type.setter
	def content_type(self, content_type):
		"""
		Set the Content-Type option of a response.

		:type content_type: int
		:param content_type: the Content-Type
		"""
		option = CoapOption()
		option.number = CoapDissector.CONTENT_TYPE.number
		option.value = int(content_type)
		self.add_option(option)

	@content_type.deleter
	def content_type(self):
		"""
		Delete the Content-Type option of a response.
		"""

		self.del_option_by_number(CoapDissector.CONTENT_TYPE.number)

	@property
	def originator(self):
		"""
		Check if the request is an observing request.

		:return: 0, if the request is an observing request
		"""
		for option in self.options:
			if option.number == CoapDissector.OPT_ONEM2M_FR.number:
				return option.value
		return None

	@originator.deleter
	def originator(self, from_):
		"""
		Delete the Observe option.
		"""
		self.del_option_by_number(CoapDissector.OPT_ONEM2M_FR.number)

	@originator.setter
	def originator(self, from_):
		"""
		Add the Observe option.

		:param ob: observe count
		"""
		option = CoapOption()
		option.number = CoapDissector.OPT_ONEM2M_FR.number
		option.value = from_
		self.del_option_by_number(CoapDissector.OPT_ONEM2M_FR.number)
		self.add_option(option)

	@property
	def rqi(self):
		"""
		Check if the request is an observing request.

		:return: 0, if the request is an observing request
		"""
		for option in self.options:
			if option.number == CoapDissector.OPT_ONEM2M_RQI.number:
				return option.value
		return None

	@rqi.deleter
	def rqi(self, rqi):
		"""
		Delete the Observe option.
		"""
		self.del_option_by_number(CoapDissector.OPT_ONEM2M_RQI.number)

	@rqi.setter
	def rqi(self, rqi):
		"""
		Add the Observe option.

		:param ob: observe count
		"""
		option = CoapOption()
		option.number = CoapDissector.OPT_ONEM2M_RQI.number
		option.value = rqi
		self.del_option_by_number(CoapDissector.OPT_ONEM2M_RQI.number)
		self.add_option(option)

	@property
	def ot(self):
		"""
		Check if the request is an observing request.

		:return: 0, if the request is an observing request
		"""
		for option in self.options:
			if option.number == CoapDissector.OPT_ONEM2M_OT.number:
				# if option.value is None:
				#	return 0
				if option.value is None:
					return 0
				return option.value
		return None

	@ot.deleter
	def ot(self, ot):
		"""
		Delete the Observe option.
		"""
		self.del_option_by_number(CoapDissector.OPT_ONEM2M_OT.number)

	@ot.setter
	def ot(self, ot):
		"""
		Add the Observe option.

		:param ob: observe count
		"""
		option = CoapOption()
		option.number = CoapDissector.OPT_ONEM2M_OT.number
		option.value = ot
		self.del_option_by_number(CoapDissector.OPT_ONEM2M_OT.number)
		self.add_option(option)

	@property
	def rqet(self):
		"""
		Check if the request is an observing request.

		:return: 0, if the request is an observing request
		"""
		for option in self.options:
			if option.number == CoapDissector.OPT_ONEM2M_RQET.number:
				# if option.value is None:
				#	return 0
				if option.value is None:
					return 0
				return option.value
		return None

	@rqet.deleter
	def rqet(self, rqet):
		"""
		Delete the Observe option.
		"""
		self.del_option_by_number(CoapDissector.OPT_ONEM2M_RQET.number)

	@rqet.setter
	def rqet(self, rqet):
		"""
		Add the Observe option.

		:param ob: observe count
		"""
		option = CoapOption()
		option.number = CoapDissector.OPT_ONEM2M_RQET.number
		option.value = rqet
		self.del_option_by_number(CoapDissector.OPT_ONEM2M_RQET.number)
		self.add_option(option)

	@property
	def rset(self):
		"""
		Check if the request is an observing request.

		:return: 0, if the request is an observing request
		"""
		for option in self.options:
			if option.number == CoapDissector.OPT_ONEM2M_RSET.number:
				# if option.value is None:
				#	return 0
				if option.value is None:
					return 0
				return option.value
		return None

	@rset.deleter
	def rset(self, rset):
		"""
		Delete the Observe option.
		"""
		self.del_option_by_number(CoapDissector.OPT_ONEM2M_RSET.number)

	@rset.setter
	def rset(self, rset):
		"""
		Add the Observe option.

		:param ob: observe count
		"""
		option = CoapOption()
		option.number = CoapDissector.OPT_ONEM2M_RSET.number
		option.value = rset
		self.del_option_by_number(CoapDissector.OPT_ONEM2M_RSET.number)
		self.add_option(option)

	@property
	def oet(self):
		"""
		Check if the request is an observing request.

		:return: 0, if the request is an observing request
		"""
		for option in self.options:
			if option.number == CoapDissector.OPT_ONEM2M_OET.number:
				# if option.value is None:
				#	return 0
				if option.value is None:
					return 0
				return option.value
		return None

	@oet.deleter
	def oet(self, oet):
		"""
		Delete the Observe option.
		"""
		self.del_option_by_number(CoapDissector.OPT_ONEM2M_OET.number)

	@oet.setter
	def oet(self, oet):
		"""
		Add the Observe option.

		:param ob: observe count
		"""
		option = CoapOption()
		option.number = CoapDissector.OPT_ONEM2M_OET.number
		option.value = oet
		self.del_option_by_number(CoapDissector.OPT_ONEM2M_OET.number)
		self.add_option(option)

	@property
	def rturi(self):
		"""
		Check if the request is an obserturing request.

		:return: 0, if the request is an obserturing request
		"""
		for option in self.options:
			if option.number == CoapDissector.OPT_ONEM2M_RTURI.number:
				# if option.value is None:
				#	return 0
				if option.value is None:
					return 0
				return option.value
		return None

	@rturi.deleter
	def rturi(self, rturi):
		"""
		Delete the Observe option.
		"""
		self.del_option_by_number(CoapDissector.OPT_ONEM2M_RTURI.number)

	@rturi.setter
	def rturi(self, rturi):
		"""
		Add the Observe option.

		:param ob: observe count
		"""
		option = CoapOption()
		option.number = CoapDissector.OPT_ONEM2M_RTURI.number
		option.value = rturi
		self.del_option_by_number(CoapDissector.OPT_ONEM2M_RTURI.number)
		self.add_option(option)

	@property
	def rsc(self):
		"""
		Check if the request is an observing request.

		:return: 0, if the request is an observing request
		"""
		for option in self.options:
			if option.number == CoapDissector.OPT_ONEM2M_RSC.number:
				# if option.value is None:
				#	return 0
				if option.value is None:
					return 0
				return option.value
		return 0

	@rsc.deleter
	def rsc(self, rsc):
		"""
		Delete the Observe option.
		"""
		self.del_option_by_number(CoapDissector.OPT_ONEM2M_RSC.number)

	@rsc.setter
	def rsc(self, rsc):
		"""
		Add the Observe option.

		:param ob: observe count
		"""
		option = CoapOption()
		option.number = CoapDissector.OPT_ONEM2M_RSC.number
		option.value = rsc
		self.del_option_by_number(CoapDissector.OPT_ONEM2M_RSC.number)
		self.add_option(option)

	@property
	def ty(self):
		"""
		Check if the request is an observing request.

		:return: 0, if the request is an observing request
		"""
		for option in self.options:
			if option.number == CoapDissector.OPT_ONEM2M_TY.number:
				# if option.value is None:
				#	return 0
				if option.value is None:
					return 0
				return option.value
		return 0

	@ty.deleter
	def ty(self, ty):
		"""
		Delete the Observe option.
		"""
		self.del_option_by_number(CoapDissector.OPT_ONEM2M_TY.number)

	@ty.setter
	def ty(self, ty):
		"""
		Add the Observe option.

		:param ob: observe count
		"""
		option = CoapOption()
		option.number = CoapDissector.OPT_ONEM2M_TY.number
		option.value = ty
		self.del_option_by_number(CoapDissector.OPT_ONEM2M_TY.number)
		self.add_option(option)

	@property
	def rvi(self):
		"""
		Check if the request is an observing request.

		:return: None, if the request is an observing request
		"""
		for option in self.options:
			if option.number == CoapDissector.OPT_ONEM2M_RVI.number:
				if option.value is None:
					return None
				return option.value
		return None

	@rvi.deleter
	def rvi(self, rvi):
		"""
		Delete the Observe option.
		"""
		self.del_option_by_number(CoapDissector.OPT_ONEM2M_RVI.number)

	@rvi.setter
	def rvi(self, rvi):
		"""
		Add the Observe option.

		:param ob: observe count
		"""
		option = CoapOption()
		option.number = CoapDissector.OPT_ONEM2M_RVI.number
		option.value = rvi
		self.del_option_by_number(CoapDissector.OPT_ONEM2M_RVI.number)
		self.add_option(option)

	@property
	def vsi(self):
		"""
		Check if the request is an observing request.

		:return: None, if the request is an observing request
		"""
		for option in self.options:
			if option.number == CoapDissector.OPT_ONEM2M_VSI.number:
				if option.value is None:
					return None
				return option.value
		return None

	@vsi.deleter
	def vsi(self, vsi):
		"""
		Delete the Observe option.
		"""
		self.del_option_by_number(CoapDissector.OPT_ONEM2M_VSI.number)

	@vsi.setter
	def vsi(self, vsi):
		"""
		Add the Observe option.

		:param ob: observe count
		"""
		option = CoapOption()
		option.number = CoapDissector.OPT_ONEM2M_VSI.number
		option.value = vsi
		self.del_option_by_number(CoapDissector.OPT_ONEM2M_VSI.number)
		self.add_option(option)

	@property
	def line_print(self):
		"""
		Return the message as a one-line string.

		:return: the string representing the message
		"""
		inv_types = {v: k for k, v in CoapDissector.Types.items()}

		if self._code is None:
			self._code = CoapDissector.LIST_CODES.EMPTY.number

		msg = "From {source}, To {destination}, {type}-{mid}, {code}-{token}, ["\
			.format(source=self._source, destination=self._destination, type=inv_types[self._type], mid=self._mid,
					code=CoapDissector.LIST_CODES[self._code].name, token=self._token)
		for opt in self._options:
			msg += "{name}: {value}, ".format(name=opt.name, value=opt.value)
		msg += "]"
		if self.payload is not None:
			if isinstance(self.payload, dict):
				tmp = list(self.payload.values())[0][0:20]
			else:
				tmp = self.payload[0:20]
			msg += " {payload}...{length} bytes".format(payload=tmp, length=len(self.payload))
		else:
			msg += " No payload"
		return msg

	def __str__(self):
		return self.line_print

	def pretty_print(self):
		"""
		Return the message as a formatted string.

		:return: the string representing the message
		"""
		msg = "Source: " + str(self._source) + "\n"
		msg += "Destination: " + str(self._destination) + "\n"
		inv_types = {v: k for k, v in CoapDissector.Types.items()}
		msg += "Type: " + str(inv_types[self._type]) + "\n"
		msg += "MID: " + str(self._mid) + "\n"
		if self._code is None:
			self._code = 0

		msg += "Code: " + str(CoapDissector.LIST_CODES[self._code].name) + "\n"
		msg += "Token: " + str(self._token) + "\n"
		for opt in self._options:
			msg += str(opt)
		msg += "Payload: " + "\n"
		msg += str(self._payload) + "\n"
		return msg

	# End of class CoapMessage

class CoapMessageRequest(CoapMessage):
	pass
	# End of class CoapMessageRequest

class CoapMessageResponse(CoapMessage):
	pass
	# End of class CoapMessageResponse

class CoapDissector(object):

	@staticmethod
	def get_option_flags(option_num):
		"""
		Get Critical, UnSafe, NoCacheKey flags from the option number (see RFC 7252, section 5.4.6)
		:param option_num: option number
		:return: option flags
		:rtype: 3-tuple (critical, unsafe, no-cache)
		"""
		opt_bytes = array.array('B', [0, 0])
		if option_num < 256:
			s = struct.Struct("!B")
			s.pack_into(opt_bytes, 0, option_num)
		else:
			s = struct.Struct("H")
			s.pack_into(opt_bytes, 0, option_num)
		critical = (opt_bytes[0] & 0x01) > 0
		unsafe = (opt_bytes[0] & 0x02) > 0
		nocache = ((opt_bytes[0] & 0x1e) == 0x1c)
		return (critical, unsafe, nocache)

	@staticmethod
	def decode(p_data, p_source) -> CoapMessage:
		try:
			fmt = "!BBH"
			pos = struct.calcsize(fmt)
			s = struct.Struct(fmt)
			values = s.unpack_from(p_data)
			first = values[0]
			code = values[1]
			mid = values[2]
			version = (first & 0xC0) >> 6
			message_type = (first & 0x30) >> 4
			token_length = (first & 0x0F)
			message = None
			if CoapDissector.is_response(code):
				message = CoapMessageResponse()
				message.code = code
			elif CoapDissector.is_request(code):
				message = CoapMessageRequest()
				message.code = code
			else:
				message = CoapMessage()
				message.code = code
			message.source = p_source
			message.destination = None
			message.version = version
			message.type = message_type
			message.mid = mid
			if token_length > 0:
				fmt = "%ss" % token_length
				s = struct.Struct(fmt)
				token_value = s.unpack_from(p_data[pos:])[0]
				message.token = token_value.decode("utf-8")
			else:
				message.token = None

			pos += token_length
			current_option = 0
			values = p_data[pos:]
			length_packet = len(values)
			pos = 0
			while pos < length_packet:
				next_byte = struct.unpack("B", values[pos].to_bytes(1, "big"))[0]
				pos += 1
				if next_byte != int(CoapDissector.PAYLOAD_MARKER):
					# The first 4 bits of the byte represent the option delta
					num, option_length, pos = CoapDissector.read_option_value_len_from_byte(next_byte, pos, values)
					current_option += num
					# Read option
					try:
						option_item = CoapDissector.LIST_OPTIONS[current_option]
					except KeyError:
						(opt_critical, _, _) = CoapDissector.get_option_flags(current_option)
						if opt_critical:
							raise AttributeError("Critical option %s unknown" % current_option)
						else:
							# If the non-critical option is unknown
							# (vendor-specific, proprietary) - just skip it
							#log.err("unrecognized option %d" % current_option)
							pass
					else:
						if option_length == 0:
							value = None
						elif option_item.value_type == CoapDissector.INTEGER:
							tmp = values[pos: pos + option_length]
							value = 0
							for b in tmp:
								value = (value << 8) | struct.unpack("B", b.to_bytes(1, "big"))[0]
						elif option_item.value_type == CoapDissector.OPAQUE:
							tmp = values[pos: pos + option_length]
							value = tmp
						else:
							value = values[pos: pos + option_length]

						option = CoapOption()
						option.number = current_option
						option.value = CoapDissector.convert_to_raw(current_option, value, option_length)

						message.add_option(option)
						if option.number == CoapDissector.CONTENT_TYPE.number:
							message.payload_type = option.value
					finally:
						pos += option_length
				else:

					if length_packet <= pos:
						# log.err("Payload Marker with no payload")
						raise AttributeError("Packet length %s, pos %s" % (length_packet, pos))
					message.payload = ""
					payload = values[pos:]
					try:
						if message.payload_type == CoapDissector.Content_types["application/octet-stream"]:
							message.payload = payload
						else:
							message.payload = payload.decode("utf-8")
					except AttributeError:
						message.payload = payload.decode("utf-8")
					pos += len(payload)

			return message
		except AttributeError:
			return CoapDissector.BAD_REQUEST.number
		except struct.error:
			return CoapDissector.BAD_REQUEST.number
		# End of method decode

	@staticmethod
	def encode(p_coap_message:CoapMessage):
		fmt = "!BBH"

		if p_coap_message.token is None or p_coap_message.token == "":
			tkl = 0
		else:
			tkl = len(p_coap_message.token)
		tmp = (CoapDissector.VERSION << 2)
		tmp |= p_coap_message.type
		tmp <<= 4
		tmp |= tkl

		values = [tmp, p_coap_message.code, p_coap_message.mid]

		if p_coap_message.token is not None and tkl > 0:

			for b in str(p_coap_message.token):
				fmt += "c"
				values.append(bytes(b, "utf-8"))

		options = CoapDissector.as_sorted_list(p_coap_message.options)  # already sorted
		lastoptionnumber = 0
		for option in options:

			# write 4-bit option delta
			optiondelta = option.number - lastoptionnumber
			optiondeltanibble = CoapDissector.get_option_nibble(optiondelta)
			tmp = (optiondeltanibble << CoapDissector.OPTION_DELTA_BITS)

			# write 4-bit option length
			optionlength = option.length
			optionlengthnibble = CoapDissector.get_option_nibble(optionlength)
			tmp |= optionlengthnibble
			fmt += "B"
			values.append(tmp)

			# write extended option delta field (0 - 2 bytes)
			if optiondeltanibble == 13:
				fmt += "B"
				values.append(optiondelta - 13)
			elif optiondeltanibble == 14:
				fmt += "H"
				values.append(optiondelta - 269)

			# write extended option length field (0 - 2 bytes)
			if optionlengthnibble == 13:
				fmt += "B"
				values.append(optionlength - 13)
			elif optionlengthnibble == 14:
				fmt += "H"
				values.append(optionlength - 269)

			# write option value
			if optionlength > 0:
				opt_type = CoapDissector.LIST_OPTIONS[option.number].value_type
				if opt_type == CoapDissector.INTEGER:
					words = CoapDissector.int_to_words(option.value, optionlength, 8)
					for num in range(0, optionlength):
						fmt += "B"
						values.append(words[num])
				elif opt_type == CoapDissector.STRING:
					fmt += str(len(bytes(option.value, "utf-8"))) + "s"
					values.append(bytes(option.value, "utf-8"))

				else:  # OPAQUE
					for b in option.value:
						fmt += "B"
						values.append(b)

			# update last option number
			lastoptionnumber = option.number

		payload = p_coap_message.payload

		if payload is not None and len(payload) > 0:
			# if payload is present and of non-zero length, it is prefixed by
			# an one-byte Payload Marker (0xFF) which indicates the end of
			# options and the start of the payload

			fmt += "B"
			values.append(CoapDissector.PAYLOAD_MARKER)

			if isinstance(payload, bytes):
				fmt += str(len(payload)) + "s"
				values.append(payload)
			else:
				fmt += str(len(bytes(payload, "utf-8"))) + "s"
				values.append(bytes(payload, "utf-8"))
			# for b in str(payload):
			#	 fmt += "c"
			#	 values.append(bytes(b, "utf-8"))

		datagram = None
		if values[1] is None:
			values[1] = 0
		if values[2] is None:
			values[2] = 0
		try:
			s = struct.Struct(fmt)
			datagram = ctypes.create_string_buffer(s.size)
			s.pack_into(datagram, 0, *values)
		except struct.error:
			# The .exception method will report on the exception encountered
			# and provide a traceback.
			Logging.logDebug(fmt)
			Logging.logDebug(values)
			Logging.exception('Failed to pack structure')

		return datagram
		# End of method encode

	@staticmethod
	def is_request(code):
		"""
		Checks if it is a request.

		:return: True, if is request
		"""
		return CoapDissector.REQUEST_CODE_LOWER_BOUND <= code <= CoapDissector.REQUEST_CODE_UPPER_BOUND

	@staticmethod
	def is_response(code):
		"""
		Checks if it is a response.
		:return: True, if is response
		"""
		return CoapDissector.RESPONSE_CODE_LOWER_BOUND <= code <= CoapDissector.RESPONSE_CODE_UPPER_BOUND

	@staticmethod
	def read_option_value_len_from_byte(byte, pos, values):
		"""
		Calculates the value and length used in the extended option fields.

		:param byte: 1-byte option header value.
		:return: the value and length, calculated from the header including the extended fields.
		"""
		h_nibble = (byte & 0xF0) >> 4
		l_nibble = byte & 0x0F
		value = 0
		length = 0
		if h_nibble <= 12:
			value = h_nibble
		elif h_nibble == 13:
			value = struct.unpack("!B", values[pos].to_bytes(1, "big"))[0] + 13
			pos += 1
		elif h_nibble == 14:
			s = struct.Struct("!H")
			value = s.unpack_from(values[pos:].to_bytes(2, "big"))[0] + 269
			pos += 2
		else:
			raise AttributeError("Unsupported option number nibble " + str(h_nibble))

		if l_nibble <= 12:
			length = l_nibble
		elif l_nibble == 13:
			length = struct.unpack("!B", values[pos].to_bytes(1, "big"))[0] + 13
			pos += 1
		elif l_nibble == 14:
			length = s.unpack_from(values[pos:].to_bytes(2, "big"))[0] + 269
			pos += 2
		else:
			raise AttributeError("Unsupported option length nibble " + str(l_nibble))
		return value, length, pos

	@staticmethod
	def convert_to_raw(number, value, length):
		"""
		Get the value of an option as a ByteArray.

		:param number: the option number
		:param value: the option value
		:param length: the option length
		:return: the value of an option as a BitArray
		"""

		opt_type = CoapDissector.LIST_OPTIONS[number].value_type

		if length == 0 and opt_type != CoapDissector.INTEGER:
			return bytes()
		elif length == 0 and opt_type == CoapDissector.INTEGER:
			return 0
		elif opt_type == CoapDissector.STRING:
			if isinstance(value, bytes):
				return value.decode("utf-8")
		elif opt_type == CoapDissector.OPAQUE:
			if isinstance(value, bytes):
				return value
			else:
				return bytes(value, "utf-8")
		if isinstance(value, tuple):
			value = value[0]
		if isinstance(value, str):
			value = str(value)
		if isinstance(value, str):
			return bytearray(value, "utf-8")
		elif isinstance(value, int):
			return value
		else:
			return bytearray(value)

	@staticmethod
	def as_sorted_list(options):
		"""
		Returns all options in a list sorted according to their option numbers.

		:return: the sorted list
		"""
		if len(options) > 0:
			options = sorted(options, key=lambda o: o.number)
		return options

	@staticmethod
	def get_option_nibble(optionvalue):
		"""
		Returns the 4-bit option header value.

		:param optionvalue: the option value (delta or length) to be encoded.
		:return: the 4-bit option header value.
		 """
		if optionvalue <= 12:
			return optionvalue
		elif optionvalue <= 255 + 13:
			return 13
		elif optionvalue <= 65535 + 269:
			return 14
		else:
			raise AttributeError("Unsupported option delta " + optionvalue)

	@staticmethod
	def int_to_words(int_val, num_words=4, word_size=32):
		"""
		Convert a int value to bytes.

		:param int_val: an arbitrary length Python integer to be split up.
			Network byte order is assumed. Raises an IndexError if width of
			integer (in bits) exceeds word_size * num_words.

		:param num_words: number of words expected in return value tuple.

		:param word_size: size/width of individual words (in bits).

		:return: a list of fixed width words based on provided parameters.
		"""
		max_int = 2 ** (word_size*num_words) - 1
		max_word_size = 2 ** word_size - 1

		if not 0 <= int_val <= max_int:
			raise AttributeError('integer %r is out of bounds!' % hex(int_val))

		words = []
		for _ in range(num_words):
			word = int_val & max_word_size
			words.append(int(word))
			int_val >>= word_size
		words.reverse()

		return words

	#Message Format
	# Number of bits used for the encoding of the CoAP version field.
	VERSION_BITS = 2
	# Number of bits used for the encoding of the message type field.
	TYPE_BITS = 2
	# Number of bits used for the encoding of the token length field.
	TOKEN_LENGTH_BITS = 4
	# Number of bits used for the encoding of the request method/response code field.
	CODE_BITS = 8
	# Number of bits used for the encoding of the message ID.
	MESSAGE_ID_BITS = 16
	# Number of bits used for the encoding of the option delta field.
	OPTION_DELTA_BITS = 4
	# Number of bits used for the encoding of the option delta field.
	OPTION_LENGTH_BITS = 4
	# One byte which indicates indicates the end of options and the start of the payload.
	PAYLOAD_MARKER = 0xFF
	# CoAP version supported by this Californium version.
	VERSION = 1
	# The lowest value of a request code.
	REQUEST_CODE_LOWER_BOUND = 1
	# The highest value of a request code.
	REQUEST_CODE_UPPER_BOUND = 31
	# The lowest value of a response code.
	RESPONSE_CODE_LOWER_BOUND = 64
	# The highest value of a response code.
	RESPONSE_CODE_UPPER_BOUND = 191

	# Type codes
	# The integer.
	INTEGER = 0
	# The string.
	STRING = 1
	# The opaque.
	OPAQUE = 2
	# The unknown.
	UNKNOWN = 3

	Types = {
		'CON': 0,
		'NON': 1,
		'ACK': 2,
		'RST': 3,
		'None': None
	}

# Create new type for CoAP CoapOption sequence
	OptionItem = collections.namedtuple('OptionItem', 'number name value_type repeatable default')
	# Regular CoAP options
	RESERVED		= OptionItem(0, "Reserved", UNKNOWN, True, None)
	IF_MATCH		= OptionItem(1, "If-Match", OPAQUE, True, None)
	URI_HOST		= OptionItem(3, "Uri-Host", STRING, True, None)
	ETAG			= OptionItem(4, "ETag", OPAQUE, True, None)
	IF_NONE_MATCH	= OptionItem(5, "If-None-Match", OPAQUE, False, None)
	OBSERVE			= OptionItem(6, "Observe", INTEGER, False, 0)
	URI_PORT		= OptionItem(7, "Uri-Port",INTEGER, False, 5683)
	LOCATION_PATH	= OptionItem(8, "Location-Path",STRING, True, None)
	URI_PATH		= OptionItem(11, "Uri-Path", STRING, True, None)
	CONTENT_TYPE	= OptionItem(12, "Content-Type", INTEGER, False, 0)
	MAX_AGE			= OptionItem(14, "Max-Age", INTEGER, False, 60)
	URI_QUERY		= OptionItem(15, "Uri-Query", STRING, True, None)
	ACCEPT			= OptionItem(17, "Accept", INTEGER, False, 0)
	LOCATION_QUERY	= OptionItem(20,"Location-Query", STRING, True, None)
	BLOCK2			= OptionItem(23, "Block2", INTEGER, False, None)
	BLOCK1			= OptionItem(27, "Block1", INTEGER, False, None)
	PROXY_URI		= OptionItem(35, "Proxy-Uri", STRING,  False, None)
	PROXY_SCHEME	= OptionItem(39, "Proxy-Schema", STRING,  False, None)
	SIZE1			= OptionItem(60, "Size1", INTEGER, False, None)
	#NO_RESPONSE		= OptionItem(258, "No-Response", INTEGER, False, None)
	RM_MESSAGE_SWITCHING	= OptionItem(65524, "Routing", OPAQUE, False, None)
	# oneM2M CoAP option
	# See TS-0008 Table 6.2.2.4.0-1: Definition of New Options
	OPT_ONEM2M_FR			= OptionItem(256, "from_", STRING, False, None)
	OPT_ONEM2M_RQI			= OptionItem(257, "requestIdentifier", STRING, False, None)
	OPT_ONEM2M_NAME			= OptionItem(258, "name", STRING, False, None)
	OPT_ONEM2M_OT			= OptionItem(259, "originatingTimestamp", STRING, False, None)
	OPT_ONEM2M_RQET			= OptionItem(260, "requestExpirationTimestamp", STRING, False, None)
	OPT_ONEM2M_RSET			= OptionItem(261, "resultExpirationTimestamp", STRING, False, None)
	OPT_ONEM2M_OET			= OptionItem(262, "operationExecutionTime", STRING, False, None)
	OPT_ONEM2M_RTURI		= OptionItem(263, "notificationUri", STRING, False, None)
	OPT_ONEM2M_EC			= OptionItem(264, "eventCategory", INTEGER, False, None)
	OPT_ONEM2M_RSC			= OptionItem(265, "responseStatusCode", INTEGER, False, None)
	OPT_ONEM2M_GID			= OptionItem(266, "groupRequestIdentifier", STRING, False, None)
	OPT_ONEM2M_TY			= OptionItem(267, "resourceType", INTEGER, False, None)
	OPT_ONEM2M_CTO			= OptionItem(268, "contentOffset", INTEGER, False, None)
	OPT_ONEM2M_CTS			= OptionItem(269, "contentStatus", INTEGER, False, None)
	OPT_ONEM2M_ATI			= OptionItem(270, "assignedTokenIdentifiers", STRING, False, None)
	OPT_ONEM2M_RVI			= OptionItem(271, "releaseVersionIndicator", STRING, False, None)
	OPT_ONEM2M_VSI			= OptionItem(272, "vendorInformation", STRING, False, None)
	OPT_ONEM2M_GTM			= OptionItem(273, "GrouprequestTargetMember", STRING, False, None)
	OPT_ONEM2M_AUS			= OptionItem(274, "AutohorizationSignature", STRING, False, None)
	OPT_ONEM2M_ASRI			= OptionItem(275, "AuthorizationSignatureRequestInformation", STRING, False, None)

	# Create the list on both regular and oneM2M options
	LIST_OPTIONS = {
		0: RESERVED,
		1: IF_MATCH,
		3: URI_HOST,
		4: ETAG,
		5: IF_NONE_MATCH,
		6: OBSERVE,
		7: URI_PORT,
		8: LOCATION_PATH,
		11: URI_PATH,
		12: CONTENT_TYPE,
		14: MAX_AGE,
		15: URI_QUERY,
		17: ACCEPT,
		20: LOCATION_QUERY,
		23: BLOCK2,
		27: BLOCK1,
		35: PROXY_URI,
		39: PROXY_SCHEME,
		60: SIZE1,
		256: OPT_ONEM2M_FR,
		257: OPT_ONEM2M_RQI,		
		258: OPT_ONEM2M_NAME,
		259: OPT_ONEM2M_OT,
		260: OPT_ONEM2M_RQET,
		261: OPT_ONEM2M_RSET,
		262: OPT_ONEM2M_OET,
		263: OPT_ONEM2M_RTURI,
		264: OPT_ONEM2M_EC,
		265: OPT_ONEM2M_RSC,
		266: OPT_ONEM2M_GID,
		267: OPT_ONEM2M_TY,
		268: OPT_ONEM2M_CTO,
		269: OPT_ONEM2M_CTS,
		270: OPT_ONEM2M_ATI,
		271: OPT_ONEM2M_RVI,
		272: OPT_ONEM2M_VSI,
		65524: RM_MESSAGE_SWITCHING
	}

	# Create new type for CoAP codes
	# See RFC 7252 The Constrained Application Protocol (CoAP) 5.9.  Response Code Definitions
	# See RFC 7959 Block-Wise Transfers in the Constrained Application Protocol (CoAP)
	# See TS-0008 Table 6.2.4-1: Mapping between oneM2M Response Status Code and CoAP Response Code
	# See TS-0009 Table 6.3.2-1: Status Code Mapping
	CodeItem = collections.namedtuple('CodeItem', 'number name')
	EMPTY = CodeItem(0, 'EMPTY')
	GET = CodeItem(1, 'GET')
	POST = CodeItem(2, 'POST')
	PUT = CodeItem(3, 'PUT')
	DELETE = CodeItem(4, 'DELETE')
	OK = CodeItem(205, 'CREATED')
	CREATED = CodeItem(201, 'CREATED')
	DELETED = CodeItem(202, 'DELETED')
	VALID = CodeItem(203, 'VALID')
	CHANGED = CodeItem(204, 'CHANGED')
	CONTENT = CodeItem(205, 'CONTENT')
	CONTINUE = CodeItem(231, 'CONTINUE')
	BAD_REQUEST = CodeItem(400, 'BAD_REQUEST')
	FORBIDDEN = CodeItem(403, 'FORBIDDEN')
	NOT_FOUND = CodeItem(404, 'NOT_FOUND')
	METHOD_NOT_ALLOWED = CodeItem(405, 'METHOD_NOT_ALLOWED')
	NOT_ACCEPTABLE = CodeItem(406, 'NOT_ACCEPTABLE')
	REQUEST_ENTITY_INCOMPLETE = CodeItem(408, 'REQUEST_ENTITY_INCOMPLETE')
	PRECONDITION_FAILED = CodeItem(412, 'PRECONDITION_FAILED')
	REQUEST_ENTITY_TOO_LARGE = CodeItem(413, 'REQUEST_ENTITY_TOO_LARGE')
	UNSUPPORTED_CONTENT_FORMAT = CodeItem(415, 'UNSUPPORTED_CONTENT_FORMAT')
	INTERNAL_SERVER_ERROR = CodeItem(500, 'INTERNAL_SERVER_ERROR')
	NOT_IMPLEMENTED = CodeItem(501, 'NOT_IMPLEMENTED')
	BAD_GATEWAY = CodeItem(502, 'BAD_GATEWAY')
	SERVICE_UNAVAILABLE = CodeItem(503, 'SERVICE_UNAVAILABLE')
	GATEWAY_TIMEOUT = CodeItem(504, 'GATEWAY_TIMEOUT')
	PROXY_NOT_SUPPORTED = CodeItem(505, 'PROXY_NOT_SUPPORTED')

	LIST_CODES = {
		0: EMPTY,
		1: GET,
		2: POST,
		3: PUT,
		4: DELETE,

		205: OK,
		201: CREATED,
		202: DELETE,
		203: VALID,
		204: CHANGED,
		205: CONTENT,
		231: CONTINUE,

		400: BAD_REQUEST,
		403: FORBIDDEN,
		404: NOT_FOUND,
		405: METHOD_NOT_ALLOWED,
		406: NOT_ACCEPTABLE,
		408: REQUEST_ENTITY_INCOMPLETE,
		412: PRECONDITION_FAILED,
		413: REQUEST_ENTITY_TOO_LARGE,
		415: UNSUPPORTED_CONTENT_FORMAT,

		500: INTERNAL_SERVER_ERROR,
		501: NOT_IMPLEMENTED,
		502: BAD_GATEWAY,
		503: SERVICE_UNAVAILABLE,
		504: GATEWAY_TIMEOUT,
		505: PROXY_NOT_SUPPORTED
	}

	@staticmethod
	def is_uri_option(number):
		"""
		checks if the option is part of uri-path, uri-host, uri-port, uri-query

		:param number:
		:return:
		"""
		if number == 3 | number == 7 | number == 11 | number == 15:
			return True
		return False

	@staticmethod
	def generate_random_token(size):
		return ''.join(random.choice(string.ascii_letters) for _ in range(size))

	@staticmethod
	def parse_blockwise(value):
		"""
		Parse Blockwise option.

		:param value: option value
		:return: num, m, size
		"""

		length = CoapDissector.byte_len(value)
		if length == 1:
			num = value & 0xF0
			num >>= 4
			m = value & 0x08
			m >>= 3
			size = value & 0x07
		elif length == 2:
			num = value & 0xFFF0
			num >>= 4
			m = value & 0x0008
			m >>= 3
			size = value & 0x0007
		else:
			num = value & 0xFFFFF0
			num >>= 4
			m = value & 0x000008
			m >>= 3
			size = value & 0x000007
		return num, int(m), pow(2, (size + 4))

	@staticmethod
	def byte_len(int_type):
		"""
		Get the number of byte needed to encode the int passed.

		:param int_type: the int to be converted
		:return: the number of bits needed to encode the int passed.
		"""
		length = 0
		while int_type:
			int_type >>= 1
			length += 1
		if length > 0:
			if length % 8 != 0:
				length = int(length / 8) + 1
			else:
				length = int(length / 8)
		return length

	# End of class CoapDissector

class CoapOption(object):
	"""
	Class to handle the CoAP Options.
	"""
	def __init__(self):
		"""
		Data structure to store options.
		"""
		self._number = None
		self._value = None

	@property
	def number(self):
		"""
		Return the number of the option.

		:return: the option number
		"""
		return self._number

	@number.setter
	def number(self, value):
		"""
		Set the option number.

		:type value: int
		:param value: the option number
		"""
		self._number = value

	@property
	def value(self):
		"""
		Return the option value.

		:return: the option value in the correct format depending on the option
		"""
		if type(self._value) is None:
			self._value = bytearray()
		opt_type = CoapDissector.LIST_OPTIONS[self._number].value_type
		if opt_type == CoapDissector.INTEGER:
			if CoapDissector.byte_len(self._value) > 0:
				return int(self._value)
			else:
				return CoapDissector.LIST_OPTIONS[self._number].default
		return self._value

	@value.setter
	def value(self, value):
		"""
		Set the value of the option.

		:param value: the option value
		"""
		opt_type = CoapDissector.LIST_OPTIONS[self._number].value_type
		if opt_type == CoapDissector.INTEGER:
			if type(value) is not int:
				value = int(value)
			if CoapDissector.byte_len(value) == 0:
				value = 0
		elif opt_type == CoapDissector.STRING:
			if type(value) is not str:
				value = str(value)
		elif opt_type == CoapDissector.OPAQUE:
			if type(value) is bytes:
				pass
			else:
				if value is not None:
					value = bytes(value, "utf-8")

		self._value = value

	@property
	def length(self):
		"""
		Return the value length

		:rtype : int
		"""
		if isinstance(self._value, int):
			return CoapDissector.byte_len(self._value)
		if self._value is None:
			return 0
		return len(self._value)

	@property
	def name(self):
		"""
		Return option name.

		:rtype : String
		:return: the option name
		"""
		return CoapDissector.LIST_OPTIONS[self._number].name

	def __str__(self):
		"""
		Return a string representing the option

		:rtype : String
		:return: a message with the option name and the value
		"""
		return self.name + ": " + str(self.value) + "\n"

	def __eq__(self, other):
		"""
		Return True if two option are equal

		:type other: CoapOption
		:param other: the option to be compared against
		:rtype : Boolean
		:return: True, if option are equal
		"""
		return self.__dict__ == other.__dict__

	# End of class CoapOption

# End of file