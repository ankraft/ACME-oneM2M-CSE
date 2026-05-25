#
#	Importer.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Entity to import various resources into the CSE. It is mainly run before 
#	the CSE is actually started.
#

"""	Import various resources, scripts, policies etc into the CSE. """

from __future__ import annotations
from typing import cast, Optional, TYPE_CHECKING

import json, os, fnmatch, re
from copy import deepcopy

from ..helpers.TextTools import findXPath
from ..etc.Types import AttributePolicy, ResourceTypes, BasicType, Cardinality, RequestOptionality, Announced, JSON, JSONLIST, ResourceDescription
from ..etc.Types import resourceTypeDetails
from ..etc.Constants import RuntimeConstants as RC
from ..runtime.Logging import Logging as L
from ..runtime.ScriptManager import _metaInit
from ..runtime.Configuration import Configuration
from ..helpers.Singleton import Singleton
from ..helpers.TextTools import removeCommentsFromJSON
from ..resources.CSEBase import getCSE
from ..runtime.PluginSupport import requires

if TYPE_CHECKING:
	from ..runtime.Factory import Factory
	from ..services.Dispatcher import Dispatcher
	from ..services.Validator import Validator
	from ..runtime.ScriptManager import ScriptManager


# TODO Support child specialization in attribute definitionsEv

# TODO change error handling to exceptions
@requires(dispatcher='acmecse.services.Dispatcher')
@requires(factory='acmecse.runtime.Factory')
@requires(validator='acmecse.services.Validator')
@requires(scriptManager='acmecse.runtime.ScriptManager')
class Importer(metaclass=Singleton):
	""" Importer class to import various objects, configurations etc.
	
		It is mainly run before the CSE is actually started or restarted."""

	factory: Factory = None
	""" Injected Factory instance. """

	dispatcher: Dispatcher = None
	""" Injected Dispatcher instance. """

	validator: Validator = None
	""" Injected Validator instance. """

	scriptManager: ScriptManager = None
	""" ScriptManager instance. """

	__slots__ = (
		'resourcePath',
		'extendedScriptPaths',
		'macroMatch',
		'isImporting',
		'rtDir',

		'_oldEnabbleAcpChecks',
	)
	""" Slots for Importer class. """


	_enumValues:dict[str, dict[int, str]] = {}
	"""	Imported enumeration values. """

	def initialize(self) -> None:
		"""	Initialization of an *Importer* instance.
		"""

		self.resourcePath = Configuration.cse_resourcesPath
		""" Path to the directory from where to import resources, policies, scripts etc. """
		
		self.extendedScriptPaths:list[str] = []
		""" Extended list of script paths, which is used for importing scripts."""
		
		self.macroMatch = re.compile(r"\$\{[\w.]+\}")
		""" Regular expression to match macros in scripts. """

		self.isImporting = False
		""" Boolean flag to indicate whether the importer is currently importing resources. """

		self.rtDir = f'{Configuration.baseDirectory}{os.sep}init'
		""" Path to the directory from where to import additional resources, policies, scripts etc. """

		self._oldEnabbleAcpChecks: Optional[bool] = None
		""" Used to store the old value of the enableAcpChecks configuration setting during importing."""

		L.isInfo and L.log('Importer initialized')


	def importPolicies(self) -> bool:
		"""	Import the attribute, enum, flexContainer policies, and documentation.

			Return:
				Boolean indicating success or failure
		"""
		# Remove previously imported structures before importing
		self.removePolicyImports()

		# Do Imports from the internal init directory of the CSE
		L.isInfo and L.log(f'Importing standard resources and policies from: {self.resourcePath}')

		if not (self.importEnumPolicies(self.resourcePath) and
				self.importAttributePolicies(self.resourcePath) and
				self.importFlexContainerPolicies(self.resourcePath)):
			return False
		
		# Do extra imports from the init directory of the runtime data directory
		if os.path.exists(self.rtDir):
			L.isInfo and L.log(f'Importing additional resources from runtime data directory: {self.rtDir}')
			if not (self.importEnumPolicies(self.rtDir) and
					self.importAttributePolicies(self.rtDir) and
					self.importFlexContainerPolicies(self.rtDir)):
				return False
	
		# Assign the attribute policies 
		if not self.assignAttributePolicies():
			return False
		
		# Import configuation documentation and scripts
		if not self.importConfigDocs():
			return False
		
		return True		


	def removePolicyImports(self) -> None:
		"""	Remove all previous imported scripts and definitions.
		"""
		self.validator.clearAttributePolicies()
		self.validator.clearFlexContainerAttributes()
		self.validator.clearFlexContainerSpecializations()
	
	
	def removeScripts(self) -> None:
		""" Internally remove all imported scripts.
		"""
		self.scriptManager.removeScripts()


	###########################################################################
	#
	#	ResourceType policies
	#

	
	def importResourcePolicies(self) -> None:
		"""	Import the resource type policies from the resource paths.
		"""

		def _importResourcePolicies(path: str) -> None:
			"""	Import the resource type policies.

				Args:
					path: Path to a directory from where to import resource type policies.
				Return:
					True if the policies were successfully imported, False otherwise.
			"""
			if not os.path.exists(path):
				raise RuntimeError(L.logWarn(f'Import directory for resource type policies does not exist: {path}'))

			L.isDebug and L.logDebug('Importing resource type policies')
			countRP = 0

			filenames = fnmatch.filter(os.listdir(path), '*.rtp')
			for fno in filenames:
				fn = os.path.join(path, fno)
				L.isDebug and L.logDebug(f'Importing resource type policies: {fno}')
				if not os.path.exists(fn):
					continue

				# Read the JSON file
				if not (resourceTypes := cast(JSON, self.readJSONFromFile(fn))):
					raise RuntimeError(f'Error reading resource type policies from file: {fn}')
			
				# Add a ResourceDescription for each resource type
				for rtName, rtDef in resourceTypes.items():
					if not isinstance(rtDef, dict):
						raise RuntimeError(L.logErr(f'Wrong or empty resource type definition for resource type: {rtName} in file: {fn}'))
					try:
						resourceTypeDetails[ResourceTypes[rtName]] = ResourceDescription(
							type=ResourceTypes(rtDef['type']),
							typeName=rtDef['typeName'],
							fullName=rtDef['fullName'],
							announcedType=ResourceTypes[rtDef.get('announcedType')] if rtDef.get('announcedType') else None,
							virtualResourceName=rtDef.get('virtualResourceName'),
							isAnnouncedResource=rtDef.get('isAnnouncedResource', False),
							isContainer=rtDef.get('isContainer', False),
							isInstanceResource=rtDef.get('isInstanceResource', False),
							isInternalType=rtDef.get('isInternalType', False),
							isMgmtSpecialization=rtDef.get('isMgmtSpecialization', False),
							isNotificationEntity=rtDef.get('isNotificationEntity', False),
							isRequestCreatable=rtDef.get('isRequestCreatable', True),
							isRequestUpdatable=rtDef.get('isRequestUpdatable', True),
							isRequestDeletable=rtDef.get('isRequestDeletable', True),
							isSpecializationBaseResource=rtDef.get('isSpecializationBaseResource', False),
							inheritACP=rtDef.get('inheritACP', False),
							mgmtType=ResourceTypes(rtDef.get('mgmtType', ResourceTypes.UNKNOWN)),
							attributes=rtDef.get('attributes', []) if rtDef.get('attributes') is not None else None,
							childResourceTypes=[ ResourceTypes.to(crt, insensitive=True) for crt in rtDef.get('childResourceTypes', []) ] if rtDef.get('childResourceTypes') is not None else None
						)
						countRP += 1
					except KeyError as e:
						raise RuntimeError(L.logErr(f'Wrong resource type definition for resource type: {rtName} in file: {fn} - missing or wrong value for: {str(e)}'))


			L.isDebug and L.logDebug(f'Imported {countRP} resource policies')


		# Resource type policies are the first thing to import, 
		# because they are needed for the attribute policies and the resource factory initialization.	
		_importResourcePolicies(self.resourcePath)

		# Initialize the resource factory, e.g. register resource types and their constructors
		# This can only be done after the importer has imported the resource type definitions, 
		# which are used in the resource descriptions for the factory registration
		if not self.factory.initResources():
			raise RuntimeError(L.logErr('Failed to initialize resources'))




	###########################################################################
	#
	#	Scripts
	#

	def importScripts(self) -> bool:
		"""	Import the scripts from the resource path and additional directories specified in the configuration.
		"""
	
		def _importScripts(path: str|list[str]=None) -> bool:
			"""	Import the ACME script from a directory.
			
				Args:
					path: Optional string with the path to a directory to look for scripts. Default is the CSE's data directory.
				Return:
					Boolean indicating success or failure.
			"""
			countScripts = 0

			# Import
			if isinstance(path, str):
				path = [ path ]
			scriptPaths = path.copy()

			for p in list(scriptPaths):
				if not os.path.exists(p):
					L.isDebug and L.logDebug(f'Import directory for scripts does not exist: {p}')
					scriptPaths.remove(p)
					continue
				# automatically add all subdirectories with the .scripts suffix
				for _e in os.scandir(p):
					if _e.is_dir() and _e.name.endswith('.scripts'):
						scriptPaths.append(_e.path)
			self.extendedScriptPaths.extend(scriptPaths)	# save for later use

			self._prepareImporting()
			try:
				L.isDebug and L.logDebug(f'Importing scripts from directory(s): {self.extendedScriptPaths}')
				if (countScripts := self.scriptManager.loadScriptsFromDirectory(self.extendedScriptPaths)) == -1:
					return False
				
				# Check that there is only one startup script, then execute it
				match len(scripts := self.scriptManager.findScripts(meta=_metaInit)):
					case l if l > 1:
						L.logErr(f'Only one initialization script allowed. Found: {",".join([ s.scriptName for s in scripts ])}')
						return False
					case 1:
						# Check whether there is already a filled DB, then skip the imports
						if self.dispatcher.countResources() > 0:
							L.isInfo and L.log('Resources already imported, skipping boostrap')
						else:
							# Run the startup script. There shall only be one.
							s = scripts[0]
							L.isInfo and L.log(f'Running boostrap script: {s.scriptName}')
							if not self.scriptManager.runScript(s):	
								L.logErr(f'Error during startup: {s.error}')
								return False
			finally:
				# This is executed no matter whether the code above returned or just succeeded
				self._finishImporting()

			# But we still need the CSI etc of the CSE, and also check presence of CSE
			if cse := getCSE():
				# Set some values in the configuration and the CSE instance
				if RC.cseCsi != cse.csi:
					L.logWarn(f'Imported CSEBase overwrites configuration. csi: {RC.cseCsi} -> {cse.csi}')
					RC.cseCsi = cse.csi
					Configuration.update('cse.cseID', cse.csi)
				if RC.cseRi != cse.ri:
					L.logWarn(f'Imported CSEBase overwrites configuration. ri: {RC.cseRi} -> {cse.ri}')
					RC.cseRi = cse.ri
					Configuration.update('cse.resourceID',cse.ri)
				if RC.cseRn != cse.rn:
					L.logWarn(f'Imported CSEBase overwrites configuration. rn: {RC.cseRn} -> {cse.rn}')
					RC.cseRn  = cse.rn
					Configuration.update('cse.resourceName', cse.rn)
			else:
				# We don't have a CSE!
				L.logErr('CSE missing during startup, or database mismatch due to wrong CSE-ID in configuration settings.')
				return False

			L.isDebug and L.logDebug(f'Imported {countScripts} scripts')
			return True

		# remove scripts before importing
		self.removeScripts()

		# Import from the CSE's init directory
		if not _importScripts([self.resourcePath, self.rtDir]):
			return False

		# Import from additional directories specified in the configuration
		if Configuration.scripting_scriptDirectories:
			if not _importScripts(Configuration.scripting_scriptDirectories):
				return False

		return True

	###########################################################################
	#
	#	Configuraton documentation
	#

	def importConfigDocs(self) -> bool:
		""" Import the configuration documentation from the resource path. 
		
			Return:
				True if the documentation was successfully imported, False otherwise.
		"""
		# Get import path
		if (path := self.resourcePath) is None:
			L.logErr('cse.resourcesPath not set')
			raise RuntimeError('cse.resourcesPath not set')

		if not os.path.exists(path):
			L.isWarn and L.logWarn(f'Import directory for attribute policies does not exist: {path}')
			return False

		L.isDebug and L.logDebug(f'Importing configuration documentation')
		
		# Import the markdown help texts here. Split them in section at each "# name" line.
		try:
			with open(f'{path}/configurations.docmd', 'r') as f:
				id = None
				text:list[str] = []
				for line in f: 
					if line.lstrip().startswith('# '):

						# Add current documentation
						Configuration.addDoc(id, ''.join(text))
						
						# Prepare the next documentation
						id = line[2:].strip()
						text = []
						continue
					text.append(line)
				else:
					# Add last documentation
					Configuration.addDoc(id, ''.join(text))

		except FileNotFoundError as e:
			L.isWarn and L.logWarn(f'Documentation file not forund: {e}')
			return False
		return True




	###########################################################################
	#
	#	Attribute Policies
	#

	def importEnumPolicies(self, path:str) -> bool:
		"""	Import the enumeration types policies.

			Args:
				path: Path to a directory from where to import enumeration policies.
			Return:
				True if the policies were successfully imported, False otherwise.
		"""
		countEP = 0

		if not os.path.exists(path):
			L.isWarn and L.logWarn(f'Import directory for attribute policies does not exist: {path}')
			return False

		L.isDebug and L.logDebug('Importing enumerated data types policies')

		filenames = fnmatch.filter(os.listdir(path), '*.ep')
		for fno in filenames:
			fn = os.path.join(path, fno)
			L.isDebug and L.logDebug(f'Importing policies: {os.path.basename(fno)}')

			if not os.path.exists(fn):
				continue
			
			# Read the JSON file
			if not (enums := cast(JSON, self.readJSONFromFile(fn))):
				return False

			for enumName, enumDef in enums.items():
				if not isinstance(enumDef, dict):
					L.logErr(f'Wrong or empty enumeration definition for enum: {enumName} in file: {fn}')
					return False
				
				enm:dict[int, str] = {}
				for enumValue, enumInterpretation in enumDef.items():
					s, found, e = enumValue.partition('..')
					if not found:
						# Single value
						try:
							value = int(enumValue)
						except ValueError:
							L.logErr(f'Wrong enumeration value: {enumValue} in enum: {enumName} in file: {fn} (must be an integer)')
							return False
						if not isinstance(enumInterpretation, str):
							L.logErr(f'Wrong interpretation for enum value: {enumValue} in enum: {enumName} in file: {fn}')
							return False
						enm[value] = enumInterpretation

					else:
						# Range
						try:
							si = int(s)
							ei = int(e)
						except ValueError:
							L.logErr(f'Error in evalue range definition: {enumValue} (range shall consist of integer numbers) for enum attribute: {enumName} in file: {fn}', showStackTrace=False)
							return None
						for i in range(si, ei+1):
							enm[i] = enumInterpretation

				self._enumValues[enumName] = enm
				countEP += 1


		L.isDebug and L.logDebug(f'Imported {countEP} enum policies')
		return True


	def importFlexContainerPolicies(self, path:str) -> bool:
		"""	Import the attribute and hierarchy policies for flexContainer specializations.

			Args:
				path: Path to a directory from where to import flexContainer policies. 
			Return:
				True if the policies were successfully imported, False otherwise.
		"""
		countFCP = 0

		if not os.path.exists(path):
			L.isWarn and L.logWarn(f'Import directory for flexContainer policies does not exist: {path}')
			return False

		L.isDebug and L.logDebug('Importing flexContainer attribute policies')
		filenames = fnmatch.filter(os.listdir(path), '*.fcp')
		for each in filenames:
			fn = os.path.join(path, each)
			L.isDebug and L.logDebug(f'Importing policies: {os.path.relpath(fn)}')
			if not os.path.exists(fn):
				continue

			if (definitions := cast(JSONLIST, self.readJSONFromFile(fn))) is None:
				return False
			for eachDefinition in definitions:
				if not (typeShortname := findXPath(eachDefinition, 'type')):
					L.logErr(f'Missing or empty resource type in file: {fn}')
					return False
				if (cnd := findXPath(eachDefinition, 'cnd')) is None:
					L.logDebug(f'Missing containerDefinition (cnd) for type: {typeShortname} in file: {fn}')
				if (lname := findXPath(eachDefinition, 'lname')) is None:
					L.logDebug(f'Missing long name (lname) for type: {typeShortname} in file: {fn}')
				
				# Attributes are optional. However, add a dummy entry
				if not (attrs := findXPath(eachDefinition, 'attributes')):
					attrs = [ { "sname" : "__none__", "lname" : "__none__", "type" : "void", "car" : "01" } ]
					
				definedAttrs:list[str] = []
				for attr in attrs:
					if not (attributePolicy := self._parseAttribute(attr, fn, typeShortname, checkListType=False)):		# TODO Handle list sub-types for flexContainers
						return False

					# Test whether an attribute has been defined twice
					# Prevent copy-paste errors
					if attributePolicy.sname in definedAttrs:
						L.logErr(f'Double defined attribute: {attributePolicy.sname} type: {typeShortname}')
						return False
					definedAttrs.append(attributePolicy.sname)

					# Add the attribute to the additional policies structure
					try:
						if not self.validator.addFlexContainerAttributePolicy(attributePolicy):
							L.logErr(f'Cannot add attribute policies for attribute: {attributePolicy.sname} type: {typeShortname}')
							return False
						countFCP += 1
					except Exception as e:
						L.logErr(str(e))
						return False
				
				# Add the available specialization information
				if cnd:
					if self.validator.hasFlexContainerContainerDefinition(cnd):
						L.logErr(f'flexContainer containerDefinition: {cnd} already defined')
						return False

					if not self.validator.addFlexContainerSpecialization(typeShortname, cnd, lname):
						L.logErr(f'Cannot add flexContainer specialization for type: {typeShortname}')
						return False

		L.isDebug and L.logDebug(f'Imported {countFCP} flexContainer policies')
		return True


	def importAttributePolicies(self, path:str) -> bool:
		"""	Import the resource attribute policies.

			Args:
				path: Path to a directory from where to import attribute policies.
			Return:
				True if the policies were successfully imported, False otherwise.
		"""
		countAP = 0

		if not os.path.exists(path):
			L.isWarn and L.logWarn(f'Import directory for attribute policies does not exist: {path}')
			return False

		L.isDebug and L.logDebug('Importing attribute policies')

		filenames = fnmatch.filter(os.listdir(path), '*.ap')
		for fno in filenames:
			fn = os.path.join(path, fno)
			L.isDebug and L.logDebug(f'Importing policies: {fno}')
			
			if not os.path.exists(fn):
				continue
			
			# Read the JSON file
			if not (attributeList := cast(JSON, self.readJSONFromFile(fn))):
				return False
			
			# go through all the attributes in that attribute definition file
			for sname in attributeList:
				if not isinstance(sname, str):
					L.logErr(f'Attribute name must be a string: {str(sname)} in file: {fn}', showStackTrace=False)
					return False

				attributeDefs = attributeList[sname]
				if not attributeDefs or not isinstance(attributeDefs, list):
					L.logErr(f'Attribute definition must be a non-empty list for attribute: {sname} in file: {fn}', showStackTrace=False)
					return False

				# for each definition for this attribute parse it and add one or more attribute Policies
				for entry in attributeDefs:
					if not (attributePolicy := self._parseAttribute(entry, fn, sname=sname)):
						return False
					if not attributePolicy.rtypes:
						L.logErr(f'Missing or unknown resource type definition for attribute: {sname} in file {fn}', showStackTrace=False)
						return False
					for rtype in attributePolicy.rtypes:
						ap = deepcopy(attributePolicy)
						try:
							self.validator.addAttributePolicy(rtype if ap.ctype is None else ap.ctype, sname, ap)
							countAP += 1
						except ValueError as e:
							L.logErr(str(e))
							return False


		# Check whether there is an unresolved type used in any of the attributes (in the type and listType)
		# TODO ? The following can be optimized sometimes, but since it is only called once during startup the small overhead may be neglectable.
		for p in self.validator.getAllAttributePolicies().values():
			match p.type:
				case BasicType.complex:
					for each in self.validator.getAllAttributePolicies().values():
						if p.typeName == each.ctype:	# found a definition
							break
					else:
						L.logErr(f'No type or complex type definition found: {p.typeName} for attribute: {p.sname} in file: {p.fname}', showStackTrace=False)
						return False
				case BasicType.list | BasicType.listNE if p.ltype is not None:
					if p.ltype == BasicType.complex:
						for each in self.validator.getAllAttributePolicies().values():
							if p.lTypeName == each.ctype:	# found a definition
								break
						else:
							L.logErr(f'No list sub-type definition found: {p.lTypeName} for attribute: {p.sname} in file: {p.fname}', showStackTrace=False)
							return False			
		
		L.isDebug and L.logDebug(f'Imported {countAP} attribute policies')
		return True


	def assignAttributePolicies(self) -> bool:
		"""	Assign the imported attribute policies to each of the resources.
			This injects the imported attribute policies into all the Python Resource classes.

			Return:
				True if there were no errors during the assignment, False otherwise.
		"""
		L.isDebug and L.logDebug('Assigning attribute policies to resource types')

		hasErrors = False
		for ty in ResourceTypes:
			if (rc := self.factory.getResourceClassForType(ty)):									# Get the Python class for each Resource (only real resources)
				if hasattr(rc, '_attributes') and isinstance(rc._attributes, dict):	# If it has attributes defined
					for sn in rc._attributes.keys():								# Then add the policies for those attributes
						if not (ap := self.validator.getAttributePolicy(ty, sn)):
							L.logErr(f'No attribute policy for: {ty.name}.{sn}', showStackTrace=False)
							hasErrors = True
							continue
						rc._attributes[sn] = ap
				# else:
				# 	L.logErr(f'Cannot assign attribute policies for resource class: {str(ty)}', showStackTrace=False)
				# 	hasErrors = True
				# 	continue
				# Check for presence of _allowedChildResourceTypes attribute
				# TODO Move this to a general health check test function
				if not hasattr(rc, '_allowedChildResourceTypes'):
					L.logErr(f'Attribute "_allowedChildResourceTypes" missing for: {str(ty)}', showStackTrace=False)
					hasErrors = True
					continue

		return not hasErrors


	def _parseAttribute(self, attr:JSON, 
							  fn:str, 
							  typeShortname:Optional[str] = None, 
							  sname:Optional[str] = None, 
							  checkListType:Optional[bool] = True) -> Optional[AttributePolicy]:
		"""	Parse a single attribute definitions for common as well as for flexContainer attributes.

			Args:
				attr: JSON dictionary with the attribute definition to parse.
				fn: Filename that contains the attribute definition.
				typeShortname: Domain and attribute name. Mandatory for a flexContainer specialization, optional otherwise.
				sname: Shortname of the attribute.
			Return:
				The parsed definition in an `AttributePolicy`.
		"""

		#	Get the attribute short name
		if not sname:
			if not (sname := findXPath(attr, 'sname')) or not isinstance(sname, str) or len(sname) == 0:
				L.logErr(f'Missing, empty, or wrong short name (sname) for attribute: {typeShortname}:{sname} in file: {fn}', showStackTrace=False)
				return None

		#	Get the name space and determine the full typeShortname
		if not (ns := findXPath(attr, 'ns')):
			ns = 'm2m'	# default
		if not isinstance(ns, str) or not ns:
			L.logErr(f'"ns" must be a non-empty string for attribute: {sname} in file: {fn}', showStackTrace=False)
			return None
		if not typeShortname:
			typeShortname = f'{ns}:{sname}' if not sname.startswith(f'{ns}:') else sname
		
		#	Get the attribute long name
		if not (lname := findXPath(attr, 'lname')) or not isinstance(lname, str) or len(lname) == 0:
			L.logErr(f'Missing, empty, or wrong long name (lname) for attribute: {typeShortname} in file: {fn}', showStackTrace=False)
			return None

		#	Look for complex type first
		if (ctype := findXPath(attr, 'ctype')) is not None:
			if not isinstance(ctype, str) or len(ctype) == 0:
				L.logErr(f'Wrong complex type name (ctype) for attribute: {typeShortname} in file: {fn}', showStackTrace=False)
				return None
		
		# Get the optional choice attribute
		if (choice := findXPath(attr, 'choice')) is not None:
			if not isinstance(choice, bool):
				L.logErr(f'Wrong type for choice for attribute: {typeShortname} in file: {fn} - must be boolean', showStackTrace=False)
				return None

		#	Determine the type name and assign the internal data type
		if not (typeName := findXPath(attr, 'type')) or not isinstance(typeName, str) or len(typeName) == 0:
			L.logErr(f'Missing, empty, or wrong type name (type): {typeName} for attribute: {typeShortname} in file: {fn}', showStackTrace=False)
			return None
		if not (typ := BasicType.to(typeName)):	# automatically a complex type if not found in the type definition. Check for this happens later
			typ = BasicType.complex

		#	Get the optional cardinality
		if not (tmp := findXPath(attr, 'car', '01')) or not isinstance(tmp, str) or len(tmp) == 0 or not (car := Cardinality.to(tmp, insensitive=True)):	# default car01
			L.logErr(f'Empty, or wrong cardinality (car): {tmp} for attribute: {typeShortname} in file: {fn}', showStackTrace=False)
			return None

		# 	Get the create optionality
		if not (tmp := findXPath(attr, 'oc', 'o')) or not isinstance(tmp, str) or len(tmp) == 0 or not (oc := RequestOptionality.to(tmp, insensitive=True)):	# default O
			L.logErr(f'Empty, or wrong optionalCreate (oc): {tmp} for attribute: {typeShortname} in file: {fn}', showStackTrace=False)
			return None

		#	Get the update optionality
		if not (tmp := findXPath(attr, 'ou', 'o')) or not isinstance(tmp, str) or len(tmp) == 0 or not (ou := RequestOptionality.to(tmp, insensitive=True)):	# default O
			L.logErr(f'Empty, or wrong optionalUpdate (ou): {tmp} for attribute: {typeShortname} in file: {fn}', showStackTrace=False)
			return None

		#	Get the delete optionality
		if not (tmp := findXPath(attr, 'od', 'o')) or not isinstance(tmp, str) or len(tmp) == 0 or not (od := RequestOptionality.to(tmp, insensitive=True)):	# default O
			L.logErr(f'Empty, or wrong optionalDiscovery (od): {tmp} for attribute: {typeShortname} in file: {fn}', showStackTrace=False)
			return None

		#	Ge the announcement optionality
		if not (tmp := findXPath(attr, 'annc', 'oa')) or not isinstance(tmp, str) or len(tmp) == 0 or not (annc := Announced.to(tmp, insensitive=True)):	# default OA
			L.logErr(f'Empty, or wrong announcement (annc): {tmp} for attribute: {typeShortname} in file: {fn}', showStackTrace=False)
			return None
				
		#	Check and determine the list type
		lTypeName:str = None
		ltype:BasicType = None
		etype:str = None
		evalues:dict[int, str] = None
		if checkListType:	# TODO remove this when flexContainer definitions support list sub-types
			if lTypeName := findXPath(attr, 'ltype'):
				if not isinstance(lTypeName, str) or len(lTypeName) == 0:
					L.logErr(f'Empty list type name (ltype): {lTypeName} for attribute: {typeShortname} in file: {fn}', showStackTrace=False)
					return None
				if typ not in [ BasicType.list, BasicType.listNE ]:
					L.logErr(f'List type (ltype) defined for non-list attribute type: {typ} for attribute: {typeShortname} in file: {fn}', showStackTrace=False)
					return None
				if not (ltype := BasicType.to(lTypeName)):	# automatically a complex type if not found in the type definition. Check for this happens later
					ltype = BasicType.complex
				if ltype == BasicType.enum:	# check sub-type enums
					if (etype := findXPath(attr, 'etype')):	# Get the values indirectly from the enums read above
						evalues = self._enumValues.get(etype)
					else:
						evalues = findXPath(attr, 'evalues')	# TODO?
					if not evalues or not isinstance(evalues, dict):
						L.logErr(f'Missing, wrong of empty enum values (evalue) list for attribute: {typeShortname} in file: {fn}', showStackTrace=False)
						return None
					# evalues = self._expandEnumValues(evalues, typeShortname, fn)	# TODO this is perhaps wrong, bc we changed the evalue handling to a different format
			if typ == BasicType.list and lTypeName is None:
					L.isDebug and L.logDebug(f'Missing list type for attribute: {typeShortname} in file: {fn}')
		
		# Check optional list size
		if lSize := findXPath(attr, 'lsize'):
			if not lTypeName:
				L.logErr(f'List size (lsize) defined for non-list attribute type: {typ} for attribute: {typeShortname} in file: {fn}', showStackTrace=False)
				return None
			if not isinstance(lSize, int) or lSize < 0:
				L.logErr(f'Wrong list size (lsize): {lSize} for attribute: {typeShortname} in file: {fn}', showStackTrace=False)
				return None

		#	Check and get enum definitions
		evalues = None
		if typ == BasicType.enum or (typ == BasicType.list and ltype == BasicType.enum):
			if (etype := findXPath(attr, 'etype')):	# Get the values indirectly from the enums read above
				evalues = self._enumValues.get(etype)
			else:
				evalues = findXPath(attr, 'evalues')	# TODO?
			if not evalues or not isinstance(evalues, dict):
				L.logErr(f'Missing, wrong of empty enum values (evalue) list for attribute: {typeShortname} etype: {etype} in file: {fn}', showStackTrace=False)
				return None
			# evalues = self._expandEnumValues(evalues, typeShortname, fn)

		#	Check missing complex type definition
		if typ == BasicType.dict or ltype == BasicType.dict:
			L.isDebug and L.logDebug(f'Missing complex type definition for attribute: {typeShortname} in file: {fn}')
		# re-type an anonymous dict to a normal dict
		if typ == BasicType.adict:
			typ = BasicType.dict


		#	CHeck whether the mandatory rtypes field is set
		if (rtypes := findXPath(attr, 'rtypes')):
			if not isinstance(rtypes, list):
				L.logErr(f'Empty, or wrong resourceTypes (rtypes): {rtypes} for attribute: {typeShortname} in file: {fn}', showStackTrace=False)
				return None

		# Test whether the rtypes are known and convert them to the internal representation
		_rtypes = ResourceTypes.to(tuple(rtypes)) if rtypes else None 	# type:ignore[arg-type]
		if rtypes and not _rtypes:
			L.logErr(f'Unknown resource type definition: {rtypes} for attribute: {typeShortname} in file: {fn}', showStackTrace=False)
			return None
		
		#	Create an AttributePolicy instance and return it
		ap = AttributePolicy(	type=typ,
								typeName=typeName,
								optionalCreate=oc,
								optionalUpdate=ou,
								optionalDiscovery=od,
								cardinality=car,
								announcement=annc,
								namespace=ns,
								lname=lname,
								sname=sname,
								typeShortname=typeShortname,
								rtypes=_rtypes,
								ctype=ctype,
								fname=fn,
								ltype=ltype,
								etype=etype,
								lTypeName=lTypeName,
								evalues=evalues,
								lSize=lSize,
								choice=choice,
							)
		return ap


	def _prepareImporting(self) -> None:
		"""	Prepare the importing process.
		"""
		# temporarily disable access control
		self._oldEnabbleAcpChecks = Configuration.cse_security_enableACPChecks
		Configuration.update('cse.security.enableACPChecks', False)
		self.isImporting = True


	def replaceMacro(self, macro:str, filename:str) -> str:	# TODO move to helper
		"""
		"""
		macro = macro[2:-1]
		if (value := Configuration.get(macro)) is None:	# could be int or len == 0
			L.logErr(f'Unknown macro ${{{macro}}} in file {filename}')
			return f'*** UNKNWON MACRO : {macro} ***'
		return str(value)


	def readJSONFromFile(self, filename:str) -> Optional[JSON|JSONLIST]:		# TODO move to helper
		"""	Read and parse a JSON data structure from a file *filename*. 

			Args:
				filename: The full filename of the input file.

			Return:
				Return the parsed structure, or *None* in case of an error.
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
		""" Finish the importing process, e.g. re-enable access control.
		"""
		Configuration.update('cse.security.enableACPChecks', self._oldEnabbleAcpChecks)
		self.isImporting = False


	def _expandEnumValues(self, evalues:list[int|str], typeShortname:str, fn:str) -> Optional[list[int]]:
		""" Expand an enum values list by parsing the range definitions and return a list of integer values.
		
			Args:
				evalues: A list of integer values or range definitions (e.g. "1..10") to expand.
				typeShortname: The type and attribute name (for logging purposes).
				fn: The filename where the enum values are defined (for logging purposes).

			Return:
				A list of integer values, or *None* in case of an error.
		"""

		#	Check and get enum definitions
		_evalues:list[int] = []
		for each in evalues:
			if isinstance(each, int):
				_evalues.append(each)
				continue
			if isinstance(each, str):
				s, found, e = each.partition('..')
				if not found:
					L.logErr(f'Error in evalue range definition: {each} for enum attribute: {typeShortname} in file: {fn}', showStackTrace=False)
					return None
				try:
					si = int(s)
					ei = int(e)
				except ValueError:
					L.logErr(f'Error in evalue range definition: {each} (range shall consist of integer numbers) for enum attribute: {typeShortname} in file: {fn}', showStackTrace=False)
					return None
				if not si < ei:
					L.logErr(f'Error in evalue range definition: {each} (begin >= end) for enum attribute: {typeShortname} in file: {fn}', showStackTrace=False)
					return None
				_evalues.extend(list(range(si, ei+1)))
				continue
			L.logErr(f'Unsupported value: {each} for enum attribute: {typeShortname} in file: {fn}', showStackTrace=False)
			return None

		return _evalues
