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
from copy import deepcopy

from ..etc.Utils import findXPath, getCSE
from ..etc.Types import AttributePolicy
from ..etc.Types import ResourceTypes as T
from ..etc.Types import BasicType as BT, Cardinality as CAR, RequestOptionality as RO, Announced as AN, JSON, JSONLIST
from ..services.Configuration import Configuration
from ..services import CSE as CSE
from ..services.Logging import Logging as L
from ..resources import Factory as Factory
from ..helpers.TextTools import removeCommentsFromJSON

# TODO Support child specialization in attribute definitionsEv

class Importer(object):

	# List of "priority" resources that must be imported first for correct CSE operation
	_firstImporters = [ 'csebase.json']

	def __init__(self) -> None:
		self.resourcePath = Configuration.get('cse.resourcesPath')
		self.macroMatch = re.compile(r"\$\{[\w.]+\}")
		self.isImporting = False
		L.isInfo and L.log('Importer initialized')


	def doImport(self) -> bool:
		"""	Perform all the imports. This imports the attribute policies, flexContainer policies,
			and scripts.

			Return:
				Boolean indicating success or failure
		"""
		# Remove previously imported structures before importing
		self.removeImports()

		# Do Imports
		if not (self.importAttributePolicies() and \
				self.importFlexContainerPolicies() and \
				self.assignAttributePolicies() and \
				self.importScripts()):
			return False
		if CSE.script.scriptDirectories:
			if not self.importScripts(CSE.script.scriptDirectories):
				return False
		return True		


	def removeImports(self) -> None:
		"""	Remove all previous imported scripts and definitions.
		"""
		CSE.validator.clearAttributePolicies()
		CSE.validator.clearFlexContainerAttributes()
		CSE.validator.clearFlexContainerSpecializations()
		CSE.script.removeScripts()


	def importScripts(self, path:str = None) -> bool:
		"""	Import the ACME script from a directory.
		
			Args:
				path: Optional string with the path to a directory to look for scripts. Default is the CSE's data directory.
			Return:
				Boolean indicating success or failure.
		"""
		countScripts = 0

		# Import
		if not path:
			if (path := self.resourcePath) is None:
				L.logErr('cse.resourcesPath not set')
				raise RuntimeError('cse.resourcesPath not set')
		# if not os.path.exists(path):
		# 	L.isWarn and L.logWarn(f'Import directory does not exist: {path}')
		# 	return False

		self._prepareImporting()
		try:
			L.isInfo and L.log(f'Importing scripts from directories: {path}')
			if (countScripts := CSE.script.loadScriptsFromDirectory(path)) == -1:
				return False
		
			# Check that there is only one startup script, then execute it
			if len(scripts := CSE.script.findScripts(meta = 'startup')) > 1:
				L.logErr(f'Only one startup script allowed. Found: {[ s.scriptName for s in scripts ]}')
				return False

			elif len(scripts) == 1:
				# Check whether there is already a filled DB, then skip the imports
				if CSE.dispatcher.countResources() > 0:
					L.isInfo and L.log('Resources already imported, skipping boostrap')
				else:
					# Run the startup script. There shall only be one.
					s = scripts[0]
					L.isInfo and L.log(f'Running boostrap script: {s.scriptName}')
					if not CSE.script.runScript(s):	
						L.logErr(f'Error during startup: {s.error}')
						return False
		finally:
			# This is executed no matter whether the code above returned or just succeeded
			self._finishImporting()

		# But we still need the CSI etc of the CSE, and also check presence of CSE
		if cse := getCSE().resource:
			# Set some values in the configuration and the CSE instance
			if CSE.cseCsi != cse.csi:
				L.logWarn(f'Imported CSEBase overwrites configuration. csi: {CSE.cseCsi} -> {cse.csi}')
				CSE.cseCsi = cse.csi
				Configuration.update('cse.csi', cse.csi)
			if CSE.cseRi != cse.ri:
				L.logWarn(f'Imported CSEBase overwrites configuration. ri: {CSE.cseRi} -> {cse.ri}')
				CSE.cseRi = cse.ri
				Configuration.update('cse.ri',cse.ri)
			if CSE.cseRn != cse.rn:
				L.logWarn(f'Imported CSEBase overwrites configuration. rn: {CSE.cseRn} -> {cse.rn}')
				CSE.cseRn  = cse.rn
				Configuration.update('cse.rn', cse.rn)
		else:
			# We don't have a CSE!
			L.logErr('CSE missing in startup script')
			return False

		L.isDebug and L.logDebug(f'Imported {countScripts} scripts')
		return True


	###########################################################################
	#
	#	Attribute Policies
	#


	def importFlexContainerPolicies(self, path:str = None) -> bool:
		"""	Import the attribute and hierarchy policies for flexContainer specializations.
		"""
		countFCP = 0

		# Get import path
		if not path:
			if (path := self.resourcePath) is None:
				L.logErr('cse.resourcesPath not set')
				raise RuntimeError('cse.resourcesPath not set')

		if not os.path.exists(path):
			L.isWarn and L.logWarn(f'Import directory for flexContainer policies does not exist: {path}')
			return False

		L.isInfo and L.log(f'Importing flexContainer attribute policies from: {path}')
		filenames = fnmatch.filter(os.listdir(path), '*.fcp')
		for each in filenames:
			fn = os.path.join(path, each)
			L.isDebug and L.logDebug(f'Importing policies: {each}')
			if os.path.exists(fn):
				if (definitions := cast(JSONLIST, self.readJSONFromFile(fn))) is None:
					return False
				for eachDefinition in definitions:
					if not (tpe := findXPath(eachDefinition, 'type')):
						L.logErr(f'Missing or empty resource type in file: {fn}')
						return False
					if (cnd := findXPath(eachDefinition, 'cnd')) is None:
						L.logDebug(f'Missing containerDefinition (cnd) for type: {tpe} in file: {fn}')
					
					# Attributes are optional. However, add a dummy entry
					if not (attrs := findXPath(eachDefinition, 'attributes')):
						attrs = [ { "sname" : "__none__", "lname" : "__none__", "type" : "void", "car" : "01" } ]
						
					definedAttrs:list[str] = []
					for attr in attrs:
						if not (attributePolicy := self._parseAttribute(attr, fn, tpe, checkListType = False)):		# TODO Handle list sub-types for flexContainers
							return False

						# Test whether an attribute has been defined twice
						# Prevent copy-paste errors
						if attributePolicy.sname in definedAttrs:
							L.logErr(f'Double defined attribute: {attributePolicy.sname} type: {tpe}')
							return False
						definedAttrs.append(attributePolicy.sname)

						# Add the attribute to the additional policies structure
						try:
							if not CSE.validator.addFlexContainerAttributePolicy(attributePolicy):
								L.logErr(f'Cannot add attribute policies for attribute: {attributePolicy.sname} type: {tpe}')
								return False
							countFCP += 1
						except Exception as e:
							L.logErr(str(e))
							return False
					
					# Add the available specialization information
					if cnd:
						if CSE.validator.hasFlexContainerContainerDefinition(cnd):
							L.logErr(f'flexContainer containerDefinition: {cnd} already defined')
							return False

						if not CSE.validator.addFlexContainerSpecialization(tpe, cnd):
							L.logErr(f'Cannot add flexContainer specialization for type: {tpe}')
							return False

		
		L.isDebug and L.logDebug(f'Imported {countFCP} flexContainer policies')
		return True


	def importAttributePolicies(self, path:str = None) -> bool:
		"""	Import the resource attribute policies.
		"""
		countAP = 0

		# Get import path
		if not path:
			if (path := self.resourcePath) is None:
				L.logErr('cse.resourcesPath not set')
				raise RuntimeError('cse.resourcesPath not set')

		if not os.path.exists(path):
			L.isWarn and L.logWarn(f'Import directory for attribute policies does not exist: {path}')
			return False

		L.isInfo and L.log(f'Importing attribute policies from: {path}')

		filenames = fnmatch.filter(os.listdir(path), '*.ap')
		for fno in filenames:
			fn = os.path.join(path, fno)
			L.isInfo and L.log(f'Importing policies: {fno}')
			if os.path.exists(fn):
				
				# Read the JSON file
				if not (attributeList := cast(JSON, self.readJSONFromFile(fn))):
					return False
				
				# go through all the attributes in that attribute definition file
				for sname in attributeList:
					if not isinstance(sname, str):
						L.logErr(f'Attribute name must be a string: {str(sname)} in file: {fn}', showStackTrace = False)
						return False

					attributeDefs = attributeList[sname]
					if not attributeDefs or not isinstance(attributeDefs, list):
						L.logErr(f'Attribute definition must be a non-empty list for attribute: {sname} in file: {fn}', showStackTrace = False)
						return False

					# for each definition for this attribute parse it and add one or more attribute Policies
					for entry in attributeDefs:
						if not (attributePolicy := self._parseAttribute(entry, fn, sname = sname)):
							return False
						# L.isDebug and L.logDebug(attributePolicy)
						for rtype in attributePolicy.rtypes:
							ap = deepcopy(attributePolicy)
							CSE.validator.addAttributePolicy(rtype if ap.ctype is None else ap.ctype, sname, ap)
				
					countAP += 1
		

		# Check whether there is an unresolved type used in any of the attributes (in the type and listType)
		# TODO ? The following can be optimized sometimes, but since it is only called once during startup the small overhead may be neglectable.
		for p in CSE.validator.getAllAttributePolicies().values():
			if p.type == BT.complex:
				for each in CSE.validator.getAllAttributePolicies().values():
					if p.typeName == each.ctype:	# found a definition
						break
				else:
					L.logErr(f'No complex type definition found: {p.typeName} for attribute: {p.sname} in file: {p.fname}', showStackTrace = False)
					return False
			elif p.type == BT.list and p.ltype is not None:
				if p.ltype == BT.complex:
					for each in CSE.validator.getAllAttributePolicies().values():
						if p.lTypeName == each.ctype:	# found a definition
							break
					else:
						L.logErr(f'No list sub-type definition found: {p.lTypeName} for attribute: {p.sname} in file: {p.fname}', showStackTrace = False)
						return False			
		
		
		L.isDebug and L.logDebug(f'Imported {countAP} attribute policies')
		return True


	def assignAttributePolicies(self) -> bool:
		"""	Assign the imported attribute policies to each of the resources.
			This injects the imported attribute policies into all the Python Resource classes.
		"""
		L.isInfo and L.log(f'Assigning attribute policies to resource types')

		noErrors = True
		for ty in T:
			if (rc := Factory.resourceClassByType(ty)):								# Get the Python class for each Resource (only real resources)
				if hasattr(rc, '_attributes'):										# If it has attributes defined
					for sn in rc._attributes.keys():								# Then add the policies for those attributes
						if not (ap := CSE.validator.getAttributePolicy(ty, sn)):
							L.logErr(f'No attribute policy for: {str(ty)}.{sn}', showStackTrace=False)
							noErrors = False
							continue
						rc._attributes[sn] = ap
				else:
					L.logErr(f'Cannot assign attribute policies for resource class: {str(ty)}', showStackTrace=False)
					noErrors = False
					continue
				# Check for presence of _allowedChildResourceTypes attribute
				# TODO Move this to a general health check test function
				if not hasattr(rc, '_allowedChildResourceTypes'):
					L.logErr(f'Attribute "_allowedChildResourceTypes" missing for: {str(ty)}', showStackTrace=False)
					noErrors = False
					continue

		return noErrors


	def _parseAttribute(self, attr:JSON, fn:str, tpe:str = None, sname:str = None, checkListType:bool = True) -> AttributePolicy:
		"""	Parse a single attribute definitions for common as well as for flexContainer attributes.

			Args:
				attr: JSON dictionary with the attribute definition to parse.
				fn: Filename that contains the attribute definition.
				tpe: Domain and attribute name. Mandatory for a flexContainer specialization, optional otherwise.
				sname: Shortname of the attribute.
			Return:
				The parsed definition in an `AttributePolicy`.
		"""

		#	Get the attribute short name
		if not sname:
			if not (sname := findXPath(attr, 'sname')) or not isinstance(sname, str) or len(sname) == 0:
				L.logErr(f'Missing, empty, or wrong short name (sname) for attribute: {tpe}:{sname} in file: {fn}', showStackTrace=False)
				return None

		#	Get the name space and determine the full tpe
		if not (ns := findXPath(attr, 'ns')):
			ns = 'm2m'	# default
		if not isinstance(ns, str) or not ns:
			L.logErr(f'"ns" must be a non-empty string for attribute: {sname} in file: {fn}', showStackTrace=False)
			return None
		if not tpe:
			tpe = f'{ns}:{sname}'
		
		#	Get the attribute long name
		if not (lname := findXPath(attr, 'lname')) or not isinstance(lname, str) or len(lname) == 0:
			L.logErr(f'Missing, empty, or wrong long name (lname) for attribute: {tpe} in file: {fn}', showStackTrace=False)
			return None

		#	Look for complex type first
		if (ctype := findXPath(attr, 'ctype')) is not None:
			if not isinstance(ctype, str) or len(ctype) == 0:
				L.logErr(f'Wrong complex type name (ctype) for attribute: {tpe} in file: {fn}', showStackTrace=False)
				return None

		#	Determine the type name and assign the internal data type
		if not (typeName := findXPath(attr, 'type')) or not isinstance(typeName, str) or len(typeName) == 0:
			L.logErr(f'Missing, empty, or wrong type name (type): {typeName} for attribute: {tpe} in file: {fn}', showStackTrace=False)
			return None
		if not (typ := BT.to(typeName)):	# automatically a complex type if not found in the type definition. Check for this happens later
			typ = BT.complex

		#	Get the optional cardinality
		if not (tmp := findXPath(attr, 'car', '01')) or not isinstance(tmp, str) or len(tmp) == 0 or not (car := CAR.to(tmp, insensitive=True)):	# default car01
			L.logErr(f'Empty, or wrong cardinality (car): {tmp} for attribute: {tpe} in file: {fn}', showStackTrace=False)
			return None

		# 	Get the create optionality
		if not (tmp := findXPath(attr, 'oc', 'o')) or not isinstance(tmp, str) or len(tmp) == 0 or not (oc := RO.to(tmp, insensitive=True)):	# default O
			L.logErr(f'Empty, or wrong optionalCreate (oc): {tmp} for attribute: {tpe} in file: {fn}', showStackTrace=False)
			return None

		#	Get the update optionality
		if not (tmp := findXPath(attr, 'ou', 'o')) or not isinstance(tmp, str) or len(tmp) == 0 or not (ou := RO.to(tmp, insensitive=True)):	# default O
			L.logErr(f'Empty, or wrong optionalUpdate (ou): {tmp} for attribute: {tpe} in file: {fn}', showStackTrace=False)
			return None

		#	Get the delete optionality
		if not (tmp := findXPath(attr, 'od', 'o')) or not isinstance(tmp, str) or len(tmp) == 0 or not (od := RO.to(tmp, insensitive=True)):	# default O
			L.logErr(f'Empty, or wrong optionalDiscovery (od): {tmp} for attribute: {tpe} in file: {fn}', showStackTrace=False)
			return None

		#	Ge the announcement optionality
		if not (tmp := findXPath(attr, 'annc', 'oa')) or not isinstance(tmp, str) or len(tmp) == 0 or not (annc := AN.to(tmp, insensitive=True)):	# default OA
			L.logErr(f'Empty, or wrong announcement (annc): {tmp} for attribute: {tpe} in file: {fn}', showStackTrace=False)
			return None
				
		#	Check and determine the list type
		lTypeName:str = None
		ltype:BT = None
		if checkListType:	# TODO remove this when flexContainer definitions support list sub-types
			if lTypeName := findXPath(attr, 'ltype'):
				if not isinstance(lTypeName, str) or len(lTypeName) == 0:
					L.logErr(f'Empty list type name (ltype): {lTypeName} for attribute: {tpe} in file: {fn}', showStackTrace=False)
					return None
				if typ not in [ BT.list, BT.listNE ]:
					L.logErr(f'List type (ltype) defined for non-list attribute type: {typ} for attribute: {tpe} in file: {fn}', showStackTrace=False)
					return None
				if not (ltype := BT.to(lTypeName)):	# automatically a complex type if not found in the type definition. Check for this happens later
					ltype = BT.complex
				if ltype == BT.enum:	# check sub-type enums
					if not (evalues := findXPath(attr, 'evalues')) or not isinstance(evalues, list) or len(evalues) == 0:
						L.logErr(f'Missing, wrong of empty enum values (evalue) list for attribute: {tpe} in file: {fn}', showStackTrace=False)
						return None
			if typ == BT.list and lTypeName is None:
					L.isDebug and L.logDebug(f'Missing list type for attribute: {tpe} in file: {fn}')

		#	Check and get enum definitions
		evalues = None
		if typ == BT.enum or (typ == BT.list and ltype == BT.enum):
			if not (evalues := findXPath(attr, 'evalues')) or not isinstance(evalues, list) or len(evalues) == 0:
				L.logErr(f'Missing, wrong of empty enum values (evalue) list for attribute: {tpe} in file: {fn}', showStackTrace=False)
				return None
			# get ranges in enums
			_evalues:list[int] = []
			for each in evalues:
				if isinstance(each, int):
					_evalues.append(each)
					continue
				if isinstance(each, str):
					s, found, e = each.partition('..')
					if not found:
						L.logErr(f'Error in evalue range definition: {each} for enum attribute: {tpe} in file: {fn}', showStackTrace=False)
						return None
					try:
						si = int(s)
						ei = int(e)
					except ValueError:
						L.logErr(f'Error in evalue range definition: {each} (range shall consist of integer numbers) for enum attribute: {tpe} in file: {fn}', showStackTrace=False)
						return None
					if not si < ei:
						L.logErr(f'Error in evalue range definition: {each} (begin >= end) for enum attribute: {tpe} in file: {fn}', showStackTrace=False)
						return None
					_evalues.extend(list(range(si, ei+1)))
					continue
				L.logErr(f'Unsupported value: {each} for enum attribute: {tpe} in file: {fn}', showStackTrace=False)
				return None
			evalues = _evalues

		#	Check missing complex type definition
		if typ == BT.dict or ltype == BT.dict:
			L.isDebug and L.logDebug(f'Missing complex type definition for attribute: {tpe} in file: {fn}')
		# re-type an anonymous dict to a normal dict
		if typ == BT.adict:
			typ = BT.dict
		


		#	CHeck whether the mandatory rtypes field is set
		if (rtypes := findXPath(attr, 'rtypes')):
			if not isinstance(rtypes, list):
				L.logErr(f'Empty, or wrong resourceTypes (rtypes): {rtypes} for attribute: {tpe} in file: {fn}', showStackTrace=False)
				return None

		#	Create an AttributePolicy instance and return it
		ap = AttributePolicy(	type = typ,
								typeName = typeName,
								optionalCreate = oc,
								optionalUpdate = ou,
								optionalDiscovery = od,
								cardinality = car,
								announcement = annc,
								namespace = ns,
								lname = lname,
								sname = sname,
								tpe = tpe,
								rtypes = T.to(tuple(rtypes)) if rtypes else None, 	# type:ignore[arg-type]
								ctype = ctype,
								fname = fn,
								ltype = ltype,
								lTypeName = lTypeName,
								evalues = evalues
							)
		return ap


	def _prepareImporting(self) -> None:
		# temporarily disable access control
		self._oldacp = Configuration.get('cse.security.enableACPChecks')
		Configuration.update('cse.security.enableACPChecks', False)
		self.isImporting = True


	def replaceMacro(self, macro:str, filename:str) -> str:	# TODO move to helper
		macro = macro[2:-1]
		if (value := Configuration.get(macro)) is None:	# could be int or len == 0
			L.logErr(f'Unknown macro ${{{macro}}} in file {filename}')
			return f'*** UNKNWON MACRO : {macro} ***'
		return str(value)


	def readJSONFromFile(self, filename:str) -> JSON|JSONLIST:		# TODO move to helper
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
			L.logErr(f'Error in file: {filename} - {str(e)}', showStackTrace=False)
			return None
		return dct


	def _finishImporting(self) -> None:
		Configuration.update('cse.security.enableACPChecks', self._oldacp)
		self.isImporting = False

