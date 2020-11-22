#
#	MqttBinding.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	This module contains various utilty functions that are used from various
#	modules and entities of the CSE.
#

from IBindingLayer import IBindingLayer

import json, requests, logging, os, sys, traceback, queue
from typing import Any, Callable, List, Tuple, Union
from Configuration import Configuration
from Constants import Constants as C
from Types import ResourceTypes as T, Result,  RequestHeaders, Operation, RequestArguments, FilterUsage, DesiredIdentifierResultType, ResultContentType, ResponseType, ResponseCode as RC, FilterOperation
from Types import CSERequest
import CSE, Utils
from Logging import Logging
from resources.Resource import Resource

from werkzeug.datastructures import MultiDict

#from MqttDissector import MqttDissector, MqttMessage, MqttMessageRequest, MqttMessageResponse
#import TcpServer



class MqttBinding(IBindingLayer):

	def __init__(self) -> None:
		pass

	def run(self): # This does NOT return
		pass


	def sendRetrieveRequest(self, url:str, originator:str) -> Result:
		pass

	def sendCreateRequest(self, url:str, originator:str, ty:T=None, data:Any=None, headers:dict=None) -> Result:
		pass

	def sendUpdateRequest(self, url:str, originator:str, data:Any) -> Result:
		pass

	def sendDeleteRequest(self, url:str, originator:str) -> Result:
		pass

	def sendRequest(self, method:Callable , url:str, originator:str, ty:T=None, data:Any=None, ct:str='application/json', headers:dict=None) -> Result:
		pass

	# End of class MqttBinding

# End of file