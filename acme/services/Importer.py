#
#	Importer.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Entity to import various resources into the CSE. It is mainly run before 
#	the CSE is actually started.
#

from __future__ import annotations
import json, os, fnmatch, re
from typing import cast
from etc.Utils import findXPath, getCSE
from etc.Types import ResourceTypes as T
from etc.Types import BasicType as BT, Cardinality as CAR, RequestOptionality as RO, Announced as AN, JSON, JSONLIST
import resources.Factory as Factory
from services.Configuration import Configuration
import services.CSE as CSE
from services.Logging import Logging as L
from helpers.TextTools import removeCommentsFromJSON

# TODO Support child specialization in attribute definitionsEv

class Importer(object):

	# List of "priority" resources that must be imported first for correct CSE operation
	_firstImporters = [ 'csebase.json']

	def __init__(self) -> None:
		self.macroMatch = re.compile(r"\$\{[\w.]+\}")
		self.isImporting = False
		L.isInfo and L.log('Importer initialized')


	def importResources(self, path:str=None) -> bool:

		def setCSEParameters(csi:str, ri:str, rn:str) -> None:
			""" Set some values in the configuration and the CSE instance.
			"""
			if CSE.cseCsi != csi:
				L.logWarn(f'Imported CSEBase overwrites configuration. csi: {CSE.cseCsi} -> {csi}')
				CSE.cseCsi = csi
				Configuration.set('cse.csi', csi)

			if CSE.cseRi != ri:
				L.logWarn(f'Imported CSEBase overwrites configuration. ri: {CSE.cseRi} -> {ri}')
				CSE.cseRi  = ri
				Configuration.set('cse.ri', ri)

			if CSE.cseRn != rn:
				L.logWarn(f'Imported CSEBase overwrites configuration. rn: {CSE.cseRn} -> {rn}')
				CSE.cseRn  = rn
				Configuration.set('cse.rn', rn)


		countImport = 0
		countUpdate = 0

		# Only when the DB is empty else don't imports
		if CSE.dispatcher.countResources() > 0:
			L.isInfo and L.log('Resources already imported, skipping importing')
			# But we still need the CSI etc of the CSE
			if cse := getCSE().resource:
				# Set some values in the configuration and the CSE instance
				setCSEParameters(cse.csi, cse.ri, cse.rn)
				return True
			L.logErr('CSE not found')
			return False

		# Import
		if not path:
			if Configuration.has('cse.resourcesPath'):
				path = Configuration.get('cse.resourcesPath')
			else:
				L.logErr('cse.resourcesPath not set')
				raise RuntimeError('cse.resourcesPath not set')
		if not os.path.exists(path):
			L.isWarn and L.logWarn(f'Import directory does not exist: {path}')
			return False

		L.isInfo and L.log(f'Importing resources from directory: {path}')
		self._prepareImporting()


		# first import the priority resources, like CSE, Admin ACP, Default ACP
		hasCSE = False
		for rn in self._firstImporters:
			fn = path + '/' + rn
			if os.path.exists(fn):
				L.isInfo and L.log(f'Importing resource: {fn}')
				resource = Factory.resourceFromDict(cast(JSON, self.readJSONFromFile(fn)), create=True, isImported=True).resource

			# Check resource creation
			if not CSE.registration.checkResourceCreation(resource, CSE.cseOriginator):
				continue
			if not (res := CSE.dispatcher.createResource(resource)).resource:
				L.isInfo and L.logErr(f'Error during import: {res.dbg}', showStackTrace=False)
				return False
			ty = resource.ty
			if ty == T.CSEBase:
				# Set some values in the configuration and the CSE instance
				setCSEParameters(resource.csi, resource.ri, resource.rn)
				hasCSE = True
			countImport += 1


		# Check presence of CSE and at least one ACP
		if not (hasCSE):
			L.logErr('CSE and/or default ACP missing during import')
			self._finishImporting()
			return False

		# then get the filenames of all other files and sort them. Process them in order

		filenames = sorted(fnmatch.filter(os.listdir(path), '*.json'))
		for fn in filenames:
			if fn not in self._firstImporters:
				L.isInfo and L.log(f'Importing resource: {fn}')
				filename = path + '/' + fn

				# update an existing resource
				if 'update' in fn:
					dct = cast(JSON, self.readJSONFromFile(filename))
					keys = list(dct.keys())
					if len(keys) == 1 and (k := keys[0]) and 'ri' in dct[k] and (ri := dct[k]['ri']):
						if resource := CSE.dispatcher.retrieveResource(ri).resource:
							CSE.dispatcher.updateResource(resource, dct)
							countUpdate += 1
						# TODO handle error

				# create a new cresource
				else:
					# Try to get parent resource
					if not (jsn := self.readJSONFromFile(filename)):
						L.isWarn and L.logWarn(f'Error parsing file: {filename}')
						continue
					if resource := Factory.resourceFromDict(cast(JSON, jsn), create=True, isImported=True).resource:
						parentResource = None
						if pi := resource.pi:
							parentResource = CSE.dispatcher.retrieveResource(pi).resource
						# Check resource creation
						if not CSE.registration.checkResourceCreation(resource, CSE.cseOriginator):
							continue
						# Add the resource
						CSE.dispatcher.createResource(resource, parentResource)
						countImport += 1
					else:
						L.isWarn and L.logWarn(f'Unknown or wrong resource in file: {fn}')

		self._finishImporting()
		L.isDebug and L.logDebug(f'Imported {countImport} resources')
		L.isDebug and L.logDebug(f'Updated  {countUpdate} resources')
		return True


	###########################################################################
	#
	#	Attribute Policies
	#

	_nameDataTypeMappings = {
			'positiveinteger'	: BT.positiveInteger,
			'nonneginteger'		: BT.nonNegInteger,
			'unsignedint'		: BT.unsignedInt,
			'unsignedlong'		: BT.unsignedLong,
			'string' 			: BT.string,
			'timestamp' 		: BT.timestamp,
			'time' 				: BT.timestamp,
			'date'				: BT.timestamp,
			'list'				: BT.list,
			'dict' 				: BT.dict,
			'anyuri'			: BT.anyURI,
			'boolean'			: BT.boolean,
			'geocoordinates'	: BT.geoCoordinates,
			'float'				: BT.float,
			'integer'			: BT.integer,
			'void'				: BT.void,
	}


	_nameCardinalityMappings = {
		'car1'					: CAR.car1,
		'1'						: CAR.car1,
		'car1l'					: CAR.car1L,
		'1l'					: CAR.car1L,
		'car01'					: CAR.car01,
		'01'					: CAR.car01,
		'car01l'				: CAR.car01L,
		'01l'					: CAR.car01L,
	}


	_nameOptionalityMappings = {
		'np'					: RO.NP,
		'o'						: RO.O,
		'm'						: RO.M,
	}

	_nameAnnouncementMappings = {
		'na'					: AN.NA,
		'ma'					: AN.MA,
		'oa'					: AN.OA,
	}


	def importAttributePolicies(self, path:str=None) -> bool:
		countAP = 0

		# Get import path
		if not path:
			if Configuration.has('cse.resourcesPath'):
				path = Configuration.get('cse.resourcesPath')
			else:
				L.logErr('cse.resourcesPath not set')
				raise RuntimeError('cse.resourcesPath not set')

		if not os.path.exists(path):
			L.isWarn and L.logWarn(f'Import directory for attribute policies does not exist: {path}')
			return False

		filenames = fnmatch.filter(os.listdir(path), '*.ap')
		for fn in filenames:
			fn = os.path.join(path, fn)
			L.isInfo and L.log(f'Importing attribute policies: {fn}')
			if os.path.exists(fn):
				if not (lst := cast(JSONLIST, self.readJSONFromFile(fn))):
					continue
				for ap in lst:
					if not (tpe := findXPath(ap, 'type')):
						L.logErr(f'Missing or empty resource type in file: {fn}')
						return False
					
					# Attributes are optional. However, add a dummy entry
					if not (attrs := findXPath(ap, 'attributes')):
						attrs = [ { "sname" : "__none__", "lname" : "__none__", "type" : "void", "car" : "01" } ]
						
					for attr in attrs:
						if not (sn := findXPath(attr, 'sname')) or not isinstance(sn, str) or len(sn) == 0:
							L.logErr(f'Missing, empty, or wrong short name for type: {tpe} in file: {fn}')
							return False

						if not (tmp := findXPath(attr, 'type').lower()) or not isinstance(tmp, str) or len(tmp) == 0:
							L.logErr(f'Missing, empty, or wrong type name: {tmp} for attribute: {sn} type: {tpe} in file: {fn}')
							return False
						
						if not (dty := self._nameDataTypeMappings.get(tmp)):
							L.isWarn and L.logWarn(f'Unknown data type {tmp}')

						if not (tmp := findXPath(attr, 'car', 'car01').lower()) or not isinstance(tmp, str) or len(tmp) == 0 or tmp not in self._nameCardinalityMappings:	# default car01
							L.logErr(f'Empty, or wrong cardinality: {tmp} for attribute: {sn} type: {tpe} in file: {fn}')
							return False
						car = self._nameCardinalityMappings.get(tmp)

						if not (tmp := findXPath(attr, 'oc', 'o').lower()) or not isinstance(tmp, str) or len(tmp) == 0 or tmp not in self._nameOptionalityMappings:	# default O
							L.logErr(f'Empty, or wrong optionalCreate: {tmp} for attribute: {sn} type: {tpe} in file: {fn}')
							return False
						oc = self._nameOptionalityMappings.get(tmp)

						if not (tmp := findXPath(attr, 'ou', 'o').lower()) or not isinstance(tmp, str) or len(tmp) == 0 or tmp not in self._nameOptionalityMappings:	# default O
							L.logErr(f'Empty, or wrong optionalUpdate: {tmp} for attribute: {sn} type: {tpe} in file: {fn}')
							return False
						ou = self._nameOptionalityMappings.get(tmp)

						if not (tmp := findXPath(attr, 'od', 'o').lower()) or not isinstance(tmp, str) or len(tmp) == 0 or tmp not in self._nameOptionalityMappings:	# default O
							L.logErr(f'Empty, or wrong optionalDiscovery: {tmp} for attribute: {sn} type: {tpe} in file: {fn}')
							return False
						od = self._nameOptionalityMappings.get(tmp)

						if not (tmp := findXPath(attr, 'annc', 'oa').lower()) or not isinstance(tmp, str) or len(tmp) == 0 or tmp not in self._nameAnnouncementMappings:	# default OA
							L.logErr(f'Empty, or wrong announcement: {tmp} for attribute: {sn} type: {tpe} in file: {fn}')
							return False
						annc = self._nameAnnouncementMappings.get(tmp)

						# Add the attribute to the additional policies structure
						try:
							if not CSE.validator.addAdditionalAttributePolicy(tpe, { sn : ( dty, car, oc, ou, od, annc) }):
								L.logErr(f'Cannot add attribute policies for attribute: {sn} type: {tpe}')
								return False
							countAP += 1
						except Exception as e:
							L.logErr(str(e))
							return False
		
		L.isDebug and L.logDebug(f'Imported {countAP} attribute policies')
		return True


	def _prepareImporting(self) -> None:
		# temporarily disable access control
		self._oldacp = Configuration.get('cse.security.enableACPChecks')
		Configuration.set('cse.security.enableACPChecks', False)
		self.isImporting = True


	def replaceMacro(self, macro: str, filename: str) -> str:
		macro = macro[2:-1]
		if (value := Configuration.get(macro)) is None:	# could be int or len == 0
			L.logErr(f'Unknown macro ${{{macro}}} in file {filename}')
			return f'*** UNKNWON MACRO : {macro} ***'
		return str(value)


	def readJSONFromFile(self, filename: str) -> JSON|JSONLIST:
		"""	Read and parse a JSON data structure from a file `filename`. 
			Return the parsed structure, or `None` in case of an error.
		"""
		# read the file
		with open(filename) as file:
			content = file.read()
		# remove comments
		content = removeCommentsFromJSON(content).strip()
		if len(content) == 0:
			L.isWarn and L.logWarn(f'Empty file: {filename}')
			return None

		# replace macros
		items = re.findall(self.macroMatch, content)
		for item in items:
			content = content.replace(item, self.replaceMacro(item, filename))
		# Load JSON and return directly or as resource
		try:
			dct:JSON = json.loads(content)
		except json.decoder.JSONDecodeError as e:
			L.logErr(str(e))
			return None
		return dct


	def _finishImporting(self) -> None:
		Configuration.set('cse.security.enableACPChecks', self._oldacp)
		self.isImporting = False

