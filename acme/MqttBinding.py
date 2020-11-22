from IBindingLayer import IBindingLayer
import json, requests, logging, os, sys, traceback
from typing import Any, Callable, List, Tuple, Union
import flask
from flask import Flask, Request, make_response, request
from werkzeug.wrappers import Response
from Configuration import Configuration
from Constants_ import Constants_ as C
from Types import ResourceTypes as T, Result, ResponseCode as RC, Operation
import CSE, Utils
from Logging import Logging
from resources.Resource import Resource
from werkzeug.serving import WSGIRequestHandler
import ssl


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