#
#	BindingLayer.py
#
#	(c) 2020 by Yann Garcia
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Implement the transport layer based on the requested consifguration.
#   Supported transport layer are:
#	   http: oneM2M TS-0009 (over TCP/TLS)
#	   coap: oneM2M TS-0008 (over UDP/DTSL)
#	   mqtt: oneM2M TS-0010 (over TCP/TSL)
#

from IBindingLayer import IBindingLayer

from typing import Any, Callable, List, Tuple, Union
from Types import ResourceTypes as T, Result, ResponseCode as RC, Operation, Parameters, ContentSerializationType
from resources.Resource import Resource

from Logging import Logging

from HttpServer import HttpServer
from CoapBinding import CoapBinding
from MqttBinding import MqttBinding

class BindingLayer(IBindingLayer):
	"""
	"""
	
	__binding = None

	def __init__(self, bindingLayer:str):
		Logging.log('>>> BindingLayer.BindingLayer: %s' % (bindingLayer))
		if bindingLayer.lower() == 'http':
			self.__binding = HttpServer()
		elif bindingLayer.lower() == 'coap':
			self.__binding = CoapBinding()
		elif bindingLayer.lower() == 'mqtt':
			self.__binding = MqttBinding()
		else:
			raise ValueError('Unknown transport layer', 'transportLayer: %s' % (bindingLayer))
		self.serverAddress = self.__binding.serverAddress

	def __del__(self):
		self.__binding = None
		pass

	def run(self): # This does NOT return
		self.__binding.run()

	def sendRetrieveRequest(self, url:str, originator:str) -> Result:
		Logging.log('>>> BindingLayer.sendRetrieveRequest: %s - %s' % (url, originator))
		return self.__binding.sendRetrieveRequest(url, originator)

	def sendCreateRequest(self, url:str, originator:str, ty:T=None, data:Any=None, headers:dict=None) -> Result:
		Logging.log('>>> BindingLayer.sendCreateRequest: %s - %s' % (url, originator))
		return self.__binding.sendCreateRequest(url, originator, ty, data, headers)

	def sendUpdateRequest(self, url:str, originator:str, data:Any) -> Result:
		Logging.log('>>> BindingLayer.sendUpdateRequest: %s - %s' % (url, originator))
		return self.__binding.sendUpdateRequest(url, originator, data)

	def sendDeleteRequest(self, url:str, originator:str) -> Result:
		Logging.log('>>> BindingLayer.sendRetrieveRequest: %s - %s' % (url, originator))
		return self.__binding.sendDeleteRequest(url, originator)

	def sendRequest(self, method:Callable , url:str, originator:str, ty:T=None, data:Any=None, parameters:Parameters=None, ct:ContentSerializationType=None, targetResource:Resource=None, headers:dict=None) -> Result: # TODO Check if headers is required
		Logging.log('>>> BindingLayer.sendRequest: %s - %s - %s' % (url, originator, ct))
		return self.__binding.sendRequest(method , url, originator, ty, data, parameters, ct, targetResource, headers)

	def shutdown(self) -> bool:
		Logging.log('>>> BindingLayer.shutdown')
		return self.__binding.shutdown()

	# End of class BindingLayer

# End of file
