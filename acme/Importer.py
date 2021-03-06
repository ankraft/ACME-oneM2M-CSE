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
import json, os, fnmatch, re, csv
from Utils import findXPath, removeCommentsFromJSON
from typing import cast
from Configuration import Configuration
from Constants import Constants as C
from Types import ResourceTypes as T
from Types import BasicType as BT, Cardinality as CAR, RequestOptionality as RO, Announced as AN, JSON, JSONLIST
import CSE
from Logging import Logging
from resources import Resource
import resources.Factory as Factory


class Importer(object):

	# List of "priority" resources that must be imported first for correct CSE operation
	_firstImporters = [ 'csebase.json']

	def __init__(self) -> None:
		self.macroMatch = re.compile(r"\$\{[\w.]+\}")
		Logging.log('Importer initialized')


	def importResources(self, path:str=None) -> bool:

		def setCSEParameters(csi:str, ri:str, rn:str) -> None:
			""" Set some values in the configuration and the CSE instance.
			"""
			CSE.cseCsi = csi
			Configuration.set('cse.csi', csi)
			CSE.cseRi  = ri
			Configuration.set('cse.ri', ri)
			CSE.cseRn  = rn
			Configuration.set('cse.rn', rn)


		countImport = 0
		countUpdate = 0

		# Only when the DB is empty else don't imports
		if CSE.dispatcher.countResources() > 0:
			Logging.log('Resources already imported, skipping importing')
			# But we still need the CSI etc of the CSE
			rss = CSE.dispatcher.retrieveResourcesByType(T.CSEBase)
			if rss is not None:
				# Set some values in the configuration and the CSE instance
				setCSEParameters(rss[0].csi, rss[0].ri, rss[0].rn)
				return True
			Logging.logErr('CSE not found')
			return False

		# Import
		if path is None:
			if Configuration.has('cse.resourcesPath'):
				path = Configuration.get('cse.resourcesPath')
			else:
				Logging.logErr('cse.resourcesPath not set')
				raise RuntimeError('cse.resourcesPath not set')
		if not os.path.exists(path):
			Logging.logWarn(f'Import directory does not exist: {path}')
			return False

		Logging.log(f'Importing resources from directory: {path}')

		self._prepareImporting()


		# first import the priority resources, like CSE, Admin ACP, Default ACP
		hasCSE = False
		for rn in self._firstImporters:
			fn = path + '/' + rn
			if os.path.exists(fn):
				Logging.log(f'Importing resource: {fn}')
				resource = Factory.resourceFromDict(cast(JSON, self.readJSONFromFile(fn)), create=True, isImported=True).resource

			# Check resource creation
			if not CSE.registration.checkResourceCreation(resource, CSE.cseOriginator):
				continue
			if (res := CSE.dispatcher.createResource(resource)).resource is None:
				Logging.logErr(f'Error during import: {res.dbg}')
				return False
			ty = resource.ty
			if ty == T.CSEBase:
				# Set some values in the configuration and the CSE instance
				setCSEParameters(resource.csi, resource.ri, resource.rn)
				hasCSE = True
			countImport += 1


		# Check presence of CSE and at least one ACP
		if not (hasCSE):
			Logging.logErr('CSE and/or default ACP missing during import')
			self._finishImporting()
			return False

		# then get the filenames of all other files and sort them. Process them in order

		filenames = sorted(fnmatch.filter(os.listdir(path), '*.json'))
		for fn in filenames:
			if fn not in self._firstImporters:
				Logging.log(f'Importing resource from file: {fn}')
				filename = path + '/' + fn

				# update an existing resource
				if 'update' in fn:
					dct = cast(JSON, self.readJSONFromFile(filename))
					keys = list(dct.keys())
					if len(keys) == 1 and (k := keys[0]) and 'ri' in dct[k] and (ri := dct[k]['ri']) is not None:
						if (resource := CSE.dispatcher.retrieveResource(ri).resource) is not None:
							CSE.dispatcher.updateResource(resource, dct)
							countUpdate += 1
						# TODO handle error

				# create a new cresource
				else:
					# Try to get parent resource
					if (resource := Factory.resourceFromDict(cast(JSON, self.readJSONFromFile(filename)), create=True, isImported=True).resource) is not None:
						parentResource = None
						if (pi := resource.pi) is not None:
							parentResource = CSE.dispatcher.retrieveResource(pi).resource
						# Check resource creation
						if not CSE.registration.checkResourceCreation(resource, CSE.cseOriginator):
							continue
						# Add the resource
						CSE.dispatcher.createResource(resource, parentResource)
						countImport += 1
					else:
						Logging.logWarn(f'Unknown resource in file: {fn}')

		self._finishImporting()
		Logging.logDebug(f'Imported {countImport} resources')
		Logging.logDebug(f'Updated  {countUpdate} resources')
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
			'list'				: BT.list,
			'dict' 				: BT.dict,
			'anyuri'			: BT.anyURI,
			'boolean'			: BT.boolean,
			'geocoordinates'	: BT.geoCoordinates,
			'float'				: BT.float,
			'integer'			: BT.integer,
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
		if path is None:
			if Configuration.has('cse.resourcesPath'):
				path = Configuration.get('cse.resourcesPath')
			else:
				Logging.logErr('cse.resourcesPath not set')
				raise RuntimeError('cse.resourcesPath not set')

		if not os.path.exists(path):
			Logging.logWarn(f'Import directory for attribute policies does not exist: {path}')
			return False

		filenames = fnmatch.filter(os.listdir(path), '*.ap')
		for fn in filenames:
			fn = os.path.join(path, fn)
			Logging.log(f'Importing attribute policies from file: {fn}')
			if os.path.exists(fn):
				if (lst := cast(JSONLIST, self.readJSONFromFile(fn))) is None:
					continue
				for ap in lst:
					if (tpe := findXPath(ap, 'type')) is None or len(tpe) == 0:
						Logging.logErr(f'Missing or empty resource type in file: {fn}')
						return False
					
					# Attributes are optional. However, add a dummy entry
					if (attrs := findXPath(ap, 'attributes')) is None:
						attrs = [ { "sname" : "__none__", "lname" : "__none__", "type" : "void", "car" : "01" } ]
						
					for attr in attrs:
						if (sn := findXPath(attr, 'sname')) is None or not isinstance(sn, str) or len(sn) == 0:
							Logging.logErr(f'Missing, empty, or wrong short name for type: {tpe} in file: {fn}')
							return False

						if (tmp := findXPath(attr, 'type').lower()) is None or not isinstance(tmp, str) or len(tmp) == 0:
							Logging.logErr(f'Missing, empty, or wrong type name: {tmp} for attribute: {sn} type: {tpe} in file: {fn}')
							return False
						dty = self._nameDataTypeMappings.get(tmp)

						if (tmp := findXPath(attr, 'car', 'car01').lower()) is None or not isinstance(tmp, str) or len(tmp) == 0 or tmp not in self._nameCardinalityMappings:	# default car01
							Logging.logErr(f'Empty, or wrong cardinality: {tmp} for attribute: {sn} type: {tpe} in file: {fn}')
							return False
						car = self._nameCardinalityMappings.get(tmp)

						if (tmp := findXPath(attr, 'oc', 'o').lower()) is None or not isinstance(tmp, str) or len(tmp) == 0 or tmp not in self._nameOptionalityMappings:	# default O
							Logging.logErr(f'Empty, or wrong optionalCreate: {tmp} for attribute: {sn} type: {tpe} in file: {fn}')
							return False
						oc = self._nameOptionalityMappings.get(tmp)

						if (tmp := findXPath(attr, 'ou', 'o').lower()) is None or not isinstance(tmp, str) or len(tmp) == 0 or tmp not in self._nameOptionalityMappings:	# default O
							Logging.logErr(f'Empty, or wrong optionalUpdate: {tmp} for attribute: {sn} type: {tpe} in file: {fn}')
							return False
						ou = self._nameOptionalityMappings.get(tmp)

						if (tmp := findXPath(attr, 'od', 'o').lower()) is None or not isinstance(tmp, str) or len(tmp) == 0 or tmp not in self._nameOptionalityMappings:	# default O
							Logging.logErr(f'Empty, or wrong optionalDiscovery: {tmp} for attribute: {sn} type: {tpe} in file: {fn}')
							return False
						od = self._nameOptionalityMappings.get(tmp)

						if (tmp := findXPath(attr, 'annc', 'oa').lower()) is None or not isinstance(tmp, str) or len(tmp) == 0 or tmp not in self._nameAnnouncementMappings:	# default OA
							Logging.logErr(f'Empty, or wrong announcement: {tmp} for attribute: {sn} type: {tpe} in file: {fn}')
							return False
						annc = self._nameAnnouncementMappings.get(tmp)

						# Add the attribute to the additional policies structure
						try:
							if not CSE.validator.addAdditionalAttributePolicy(tpe, { sn : ( dty, car, oc, ou, od, annc) }):
								Logging.logErr(f'Cannot add attribute policies for attribute: {sn} type: {tpe}')
								return False
							countAP += 1
						except Exception as e:
							Logging.logErr(str(e))
							return False
		
		Logging.logDebug(f'Imported {countAP} attribute policies')
		return True


	# def importAttributePolicies(self, path: str = None) -> bool:
	# 	fieldNames = ['resourceType', 'shortName', 'dataType', 'cardinality' , 'optionalCreate', 'optionalUpdate', 'optionalDiscovery', 'announced' ]

	# 	# Get import path
	# 	if path is None:
	# 		if Configuration.has('cse.resourcesPath'):
	# 			path = Configuration.get('cse.resourcesPath')
	# 		else:
	# 			Logging.logErr('cse.resourcesPath not set')
	# 			raise RuntimeError('cse.resourcesPath not set')

	# 	if not os.path.exists(path):
	# 		Logging.logWarn(f'Import directory for attribute policies does not exist: {path}')
	# 		return False

	# 	filenames = fnmatch.filter(os.listdir(path), '*.ap')
	# 	for fn in filenames:
	# 		fn = os.path.join(path, fn)
	# 		Logging.log(f'Importing attribute policies from file: {fn}')
	# 		if os.path.exists(fn):
	# 			with open(fn, newline='') as fp:
	# 				reader = csv.DictReader(filter(lambda row: not row.startswith('#') and len(row.strip()) > 0, fp), fieldnames=fieldNames)
	# 				for row in reader:
	# 					if len(row) != len(fieldNames):
	# 						Logging.logErr(f'Wrong number elements ({len(row)}) for row: {row} in file: {fn}. Must be {len(fieldNames)}.')
	# 						return False
	# 					if (tpe := row.get('resourceType')) is None or len(tpe) == 0:
	# 						Logging.logErr(f'Missing or empty resource type for row: {row} in file: {fn}')
	# 						return False
	# 					# if tpe.startswith('m2m:'):
	# 					# 	Logging.logErr(f'Adding attribute policies for "m2m" namspace is not allowed: {row}')
	# 					# 	return False
	# 					if (sn := row.get('shortName')) is None or len(sn) == 0:
	# 						Logging.logErr(f'Missing or empty shortname for row: {row} in file: {fn}')
	# 						return False
	# 					if (tmp := row.get('dataType')) is None or len(tmp) == 0:
	# 						Logging.logErr(f'Missing or empty data type for row: {row} in file: {fn}')
	# 						return False
	# 					dtpe = self._nameDataTypeMappings.get(tmp.lower())
	# 					if (tmp := row.get('cardinality')) is None or len(tmp) == 0:
	# 						Logging.logErr(f'Missing or empty cardinality for row: {row} in file: {fn}')
	# 						return False
	# 					car = self._nameCardinalityMappings.get(tmp.lower())
	# 					if (tmp := row.get('optionalCreate')) is None or len(tmp) == 0:
	# 						Logging.logErr(f'Missing or empty optional create for row: {row} in file: {fn}')
	# 						return False
	# 					opcr = self._nameOptionalityMappings.get(tmp.lower())
	# 					if (tmp := row.get('optionalUpdate')) is None or len(tmp) == 0:
	# 						Logging.logErr(f'Missing or empty optional create for row: {row} in file: {fn}')
	# 						return False
	# 					opup = self._nameOptionalityMappings.get(tmp.lower())
	# 					if (tmp := row.get('optionalDiscovery')) is None or len(tmp) == 0:
	# 						Logging.logErr(f'Missing or empty optional discovery for row: {row} in file: {fn}')
	# 						return False
	# 					opdi = self._nameOptionalityMappings.get(tmp.lower())
	# 					if (tmp := row.get('announced')) is None or len(tmp) == 0:
	# 						Logging.logErr(f'Missing or empty announced for row: {row} in file: {fn}')
	# 						return False
	# 					annc = self._nameAnnouncementMappings.get(tmp.lower())

	# 					# get possible existing definitions for that type, or create one
	# 					CSE.validator.addAdditionalAttributePolicy(tpe, { sn : [ dtpe, car, opcr, opup, opdi, annc] })

	# 	return True


	def _prepareImporting(self) -> None:
		# temporarily disable access control
		self._oldacp = Configuration.get('cse.security.enableACPChecks')
		Configuration.set('cse.security.enableACPChecks', False)


	def replaceMacro(self, macro: str, filename: str) -> str:
		macro = macro[2:-1]
		if (value := Configuration.get(macro)) is None:
			Logging.logErr(f'Unknown macro ${{{macro}}} in file {filename}')
			return f'*** UNKNWON MACRO : {macro} ***'
		return str(value)


	def readJSONFromFile(self, filename: str) -> JSON|JSONLIST:
		# read the file
		with open(filename) as file:
			content = file.read()
		# remove comments
		content = removeCommentsFromJSON(content).strip()
		if len(content) == 0:
			Logging.logWarn(f'Empty file: {filename}')
			return None

		# replace macros
		items = re.findall(self.macroMatch, content)
		for item in items:
			content = content.replace(item, self.replaceMacro(item, filename))
		# Load JSON and return directly or as resource
		try:
			dct:JSON = json.loads(content)
		except json.decoder.JSONDecodeError as e:
			Logging.logErr(str(e))
			return None
		return dct


	def _finishImporting(self) -> None:
		Configuration.set('cse.security.enableACPChecks', self._oldacp)

