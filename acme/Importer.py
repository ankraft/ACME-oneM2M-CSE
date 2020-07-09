#
#	Importer.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Entity to import various resources into the CSE. It is mainly run before 
#	the CSE is actually started.
#

import json, os, fnmatch, re, csv
from typing import Tuple, Union
from Utils import *
from Configuration import Configuration
from Constants import Constants as C
from Types import ResourceTypes as T
from Types import BasicType as BT, Cardinality as CAR, RequestOptionality as RO, Announced as AN 		# type: ignore
import CSE
from Logging import Logging
from resources import Resource


class Importer(object):

	# List of "priority" resources that must be imported first for correct CSE operation
	_firstImporters = [ 'csebase.json', 'acp.admin.json', 'acp.default.json', 'acp.csebaseAccess.json']

	def __init__(self) -> None:
		Logging.log('Importer initialized')


	def importResources(self, path: str = None) -> bool:

		# Only when the DB is empty else don't imports
		if CSE.dispatcher.countResources() > 0:
			Logging.log('Resources already imported, skipping importing')
			# But we still need the CSI etc of the CSE
			rss = CSE.dispatcher.retrieveResourcesByType(T.CSEBase)
			if rss is not None:
				Configuration.set('cse.csi', rss[0]['csi'])
				Configuration.set('cse.ri', rss[0]['ri'])
				Configuration.set('cse.rn', rss[0]['rn'])
				return True
			Logging.logErr('CSE not found')
			return False

		# get the originator for the creator attribute of imported resources
		originator = Configuration.get('cse.originator')

		# Import
		if path is None:
			if Configuration.has('cse.resourcesPath'):
				path = Configuration.get('cse.resourcesPath')
			else:
				Logging.logErr('cse.resourcesPath not set')
				raise RuntimeError('cse.resourcesPath not set')
		if not os.path.exists(path):
			Logging.logWarn('Import directory does not exist: %s' % path)
			return False

		Logging.log('Importing resources from directory: %s' % path)

		self._prepareImporting()


		# first import the priority resources, like CSE, Admin ACP, Default ACP
		hasCSE = False
		hasACP = False
		for rn in self._firstImporters:
			fn = path + '/' + rn
			if os.path.exists(fn):
				Logging.log('Importing resource: %s ' % fn)
				jsn = self.readJSONFromFile(fn)
				r, _ = resourceFromJSON(jsn, create=True, isImported=True)

			# Check resource creation
			if not CSE.registration.checkResourceCreation(r, originator):
				continue
			CSE.dispatcher.createResource(r)
			ty = r.ty
			if ty == T.CSEBase:
				Configuration.set('cse.csi', r.csi)
				Configuration.set('cse.ri', r.ri)
				Configuration.set('cse.rn', r.rn)
				hasCSE = True
			elif ty == T.ACP:
				hasACP = True

		# Check presence of CSE and at least one ACP
		if not (hasCSE and hasACP):
			Logging.logErr('CSE and/or default ACP missing during import')
			self._finishImporting()
			return False


		# then get the filenames of all other files and sort them. Process them in order

		filenames = sorted(fnmatch.filter(os.listdir(path), '*.json'))
		for fn in filenames:
			if fn not in self._firstImporters:
				Logging.log('Importing resource from file: %s' % fn)
				filename = path + '/' + fn

				# update an existing resource
				if 'update' in fn:
					jsn = self.readJSONFromFile(filename)
					keys = list(jsn.keys())
					if len(keys) == 1 and (k := keys[0]) and 'ri' in jsn[k] and (ri := jsn[k]['ri']) is not None:
						r, _, _ = CSE.dispatcher.retrieveResource(ri)
						if r is not None:
							CSE.dispatcher.updateResource(r, jsn)
						# TODO handle error

				# create a new cresource
				else:
					jsn = self.readJSONFromFile(filename)
					r, _ = resourceFromJSON(jsn, create=True, isImported=True)

					# Try to get parent resource
					if r is not None:
						parent = None
						if (pi := r.pi) is not None:
							parent, _, _ = CSE.dispatcher.retrieveResource(pi)
						# Check resource creation
						if not CSE.registration.checkResourceCreation(r, originator):
							continue
						# Add the resource
						CSE.dispatcher.createResource(r, parent)
					else:
						Logging.logWarn('Unknown resource in file: %s' % fn)

		self._finishImporting()
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
	}


	_nameCardinalityMappings = {
		'car1'					: CAR.car1,
		'car1L'					: CAR.car1L,
		'car01'					: CAR.car01,
		'car01l'				: CAR.car01L,
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


	def importAttributePolicies(self, path: str = None) -> bool:
		fieldNames = ['resourceType', 'shortName', 'dataType', 'cardinality' , 'optionalCreate', 'optionalUpdate', 'optionalDiscovery', 'announced' ]

		# Get import path
		if path is None:
			if Configuration.has('cse.resourcesPath'):
				path = Configuration.get('cse.resourcesPath')
			else:
				Logging.logErr('cse.resourcesPath not set')
				raise RuntimeError('cse.resourcesPath not set')

		if not os.path.exists(path):
			Logging.logWarn('Import directory for attribute policies does not exist: %s' % path)
			return False

		filenames = fnmatch.filter(os.listdir(path), '*.ap')
		for fn in filenames:
			fn = os.path.join(path, fn)
			Logging.log('Importing attribute policies from file: %s' % fn)
			if os.path.exists(fn):
				with open(fn, newline='') as fp:
					reader = csv.DictReader(filter(lambda row: not row.startswith('#'), fp), fieldnames=fieldNames)
					for row in reader:
						if len(row) != len(fieldNames):
							Logging.logErr('Missing element(s) for row: %s in file: %s' % (row, fn))
							continue
						if (tpe := row.get('resourceType')) is None or len(tpe) == 0:
							Logging.logErr('Missing or empty resource type for row: %s in file: %s' % (row, fn))
							return False
						if (sn := row.get('shortName')) is None or len(sn) == 0:
							Logging.logErr('Missing or empty shortname for row: %s in file: %s' % (row, fn))
							return False
						if (tmp := row.get('dataType')) is None or len(tmp) == 0:
							Logging.logErr('Missing or empty data type for row: %s in file: %s' % (row, fn))
							return False
						dtpe = self._nameDataTypeMappings.get(tmp.lower())
						if (tmp := row.get('cardinality')) is None or len(tmp) == 0:
							Logging.logErr('Missing or empty cardinality for row: %s in file: %s' % (row, fn))
							return False
						car = self._nameCardinalityMappings.get(tmp.lower())
						if (tmp := row.get('optionalCreate')) is None or len(tmp) == 0:
							Logging.logErr('Missing or empty optional create for row: %s in file: %s' % (row, fn))
							return False
						opcr = self._nameOptionalityMappings.get(tmp.lower())
						if (tmp := row.get('optionalUpdate')) is None or len(tmp) == 0:
							Logging.logErr('Missing or empty optional create for row: %s in file: %s' % (row, fn))
							return False
						opup = self._nameOptionalityMappings.get(tmp.lower())
						if (tmp := row.get('optionalDiscovery')) is None or len(tmp) == 0:
							Logging.logErr('Missing or empty optional discovery for row: %s in file: %s' % (row, fn))
							return False
						opdi = self._nameOptionalityMappings.get(tmp.lower())
						if (tmp := row.get('announced')) is None or len(tmp) == 0:
							Logging.logErr('Missing or empty announced for row: %s in file: %s' % (row, fn))
							return False
						annc = self._nameAnnouncementMappings.get(tmp.lower())

						# get possible existing definitions for that type, or create one
						CSE.validator.addAdditionalAttributePolicy(tpe, { sn : [ dtpe, car, opcr, opup, opdi, annc] })

		return True


	def _prepareImporting(self) -> None:
		# temporarily disable access control
		self._oldacp = Configuration.get('cse.security.enableACPChecks')
		Configuration.set('cse.security.enableACPChecks', False)
		self.macroMatch = re.compile(r"\$\{[\w.]+\}")




	def replaceMacro(self, macro: str, filename: str) -> str:
		macro = macro[2:-1]
		if (value := Configuration.get(macro)) is None:
			Logging.logErr('Unknown macro ${%s} in file %s' %(macro, filename))
			return '*** UNKNWON MACRO : %s ***' % macro
		return value


	def readJSONFromFile(self, filename: str) -> dict:
		# read the file
		with open(filename) as file:
			content = file.read()
		# replace macros
		items = re.findall(self.macroMatch, content)
		for item in items:
			content = content.replace(item, self.replaceMacro(item, filename))
		# Load JSON and return directly or as resource
		jsn = json.loads(content)
		return jsn


	def _finishImporting(self) -> None:
		Configuration.set('cse.security.enableACPChecks', self._oldacp)

