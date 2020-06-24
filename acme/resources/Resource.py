#
#	Resource.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Base class for all resources
#

from Logging import Logging
from Constants import Constants as C
from Configuration import Configuration
import Utils, CSE
import datetime, random

# Future TODO: Check RO/WO etc for attributes (list of attributes per resource?)



class Resource(object):
	_rtype 				= '__rtype__'
	_srn				= '__srn__'
	_node				= '__node__'
	_createdInternally	= '__createdInternally__'
	_imported			= '__imported__'
	_isVirtual 			= '__isVirtual__'
	_isInstantiated		= '__isInstantiated__'
	_originator			= '__originator__'

	internalAttributes	= [ _rtype, _srn, _node, _createdInternally, _imported, _isVirtual, _isInstantiated, _originator ]

	def __init__(self, tpe, jsn=None, pi=None, ty=None, create=False, inheritACP=False, readOnly=False, rn=None, attributePolicies=None, isVirtual=False):
		self.tpe = tpe
		self.readOnly = readOnly
		self.inheritACP = inheritACP
		self.json = {}
		self.attributePolicies = attributePolicies

		if jsn is not None: 
			self.isImported = jsn.get(C.jsnIsImported)
			if tpe in jsn:
				self.json = jsn[tpe].copy()
			else:
				self.json = jsn.copy()
			self._originalJson = jsn.copy()	# keep for validation later
		else:
			# no JSON, so the resource is instantiated programmatically
			self.setAttribute(self._isInstantiated, True)


		if self.json is not None:
			if self.tpe is None: # and _rtype in self:
				self.tpe = self.__rtype__
			self.setAttribute('ri', Utils.uniqueRI(self.tpe), overwrite=False)

			# override rn if given
			if rn is not None:
				self.setAttribute('rn', rn, overwrite=True)
	
			# Check uniqueness of ri. otherwise generate a new one. Only when creating
			# TODO: could be a BAD REQUEST?
			if create:
				while Utils.isUniqueRI(ri := self.attribute('ri')) == False:
					Logging.logWarn("RI: %s is already assigned. Generating new RI." % ri)
					self.setAttribute('ri', Utils.uniqueRI(self.tpe), overwrite=True)

			# Indicate whether this is a virtual resource
			if isVirtual:
				self.setAttribute(self._isVirtual, isVirtual)
	
			# Create an RN if there is none
			self.setAttribute('rn', Utils.uniqueRN(self.tpe), overwrite=False)
			
			# Set some more attributes
			ts = Utils.getResourceDate()
			self.setAttribute('ct', ts, overwrite=False)
			self.setAttribute('lt', ts, overwrite=False)
			self.setAttribute('et', Utils.getResourceDate(Configuration.get('cse.expirationDelta')), overwrite=False) 
			if pi is not None:
				self.setAttribute('pi', pi, overwrite=False)
			if ty is not None:
				if ty in C.stateTagResourceTypes:	# Only for allowed resources
					self.setAttribute('st', 0, overwrite=False)
				self.setAttribute('ty', ty)

			#
			## Note: ACPI is set in activate()
			#

			# Remove empty / null attributes from json
			self.json = {k: v for (k, v) in self.json.items() if v is not None }

			# determine and add the srn
			self[self._srn] = Utils.structuredPath(self)
			self[self._rtype] = self.tpe




	# Default encoding implementation. Overwrite in subclasses
	def asJSON(self, embedded=True, update=False, noACP=False):
		# remove (from a copy) all internal attributes before printing
		jsn = self.json.copy()
		for k in self.internalAttributes:
			if k in jsn: 
				del jsn[k]

		if noACP:
			if 'acpi' in jsn:
				del jsn['acpi']
		if update:
			for k in [ 'ri', 'ty', 'pi', 'ct', 'lt', 'st', 'rn', 'mgd']:
				jsn.pop(k, None) # instead of using "del jsn[k]" this doesn't throw an exception if k doesn't exist

		return { self.tpe : jsn } if embedded else jsn


	# This method is called to to activate a resource. This is not always the
	# case, e.g. when a resource object is just used temporarly.
	# NO notification on activation/creation!
	# Implemented in sub-classes.
	# Note: CR and ACPI are set in RegistrationManager
	def activate(self, parentResource, originator):
		Logging.logDebug('Activating resource: %s' % self.ri)

		# validate the attributes but only when the resource is not instantiated.
		# We assume that an instantiated resource is always correct
		# Also don't validate virtual resources
		if (self[self._isInstantiated] is None or not self[self._isInstantiated]) and not self[self._isVirtual] :
			if not (result := CSE.validator.validateAttributes(self._originalJson, self.tpe, self.attributePolicies, isImported=self.isImported))[0]:
				return result

		# validate the resource logic
		if not (result := self.validate(originator, create=True))[0]:
			return result

		# increment parent resource's state tag
		if parentResource is not None and parentResource.st is not None:
			parentResource = parentResource.dbReload()	# Read the resource again in case it was updated in the DB
			parentResource['st'] = parentResource.st + 1
			if (res := parentResource.dbUpdate())[0] is None:
				return False, res[1]

		self.setAttribute(self._originator, originator, overwrite=False)
		self.setAttribute(self._rtype, self.tpe, overwrite=False) 

		return True, C.rcOK


	# Deactivate an active resource.
	# Send notification on deletion
	def deactivate(self, originator):
		Logging.logDebug('Deactivating and removing sub-resources: %s' % self.ri)
		# First check notification because the subscription will be removed
		# when the subresources are removed
		CSE.notification.checkSubscriptions(self, C.netResourceDelete)
		
		# Remove directChildResources
		rs = CSE.dispatcher.directChildResources(self.ri)
		for r in rs:
			self.childRemoved(r, originator)
			CSE.dispatcher.deleteResource(r, originator)


	# Update this resource with (new) fields.
	# Call validate() afterward to react on changes.
	def update(self, jsn=None, originator=None):
		if jsn is not None:
			if self.tpe not in jsn:
				Logging.logWarn("Update types don't match")
				return False, C.rcContentsUnacceptable

			# validate the attributes
			if not (result := CSE.validator.validateAttributes(jsn, self.tpe, self.attributePolicies, create=False))[0]:
				return result

			j = jsn[self.tpe] # get structure under the resource type specifier
			for key in j:
				# Leave out some attributes
				if key in ['ct', 'lt', 'pi', 'ri', 'rn', 'st', 'ty']:
					continue
				value = j[key]
				# Special handling for et when deleted: set a new et
				if key == 'et' and value is None:
					self['et'] = Utils.getResourceDate(Configuration.get('cse.expirationDelta'))
					continue
				self[key] = value	# copy new value

		# - state and lt
		if 'st' in self.json:	# Update the state
			self['st'] += 1
		if 'lt' in self.json:	# Update the lastModifiedTime
			self['lt'] = Utils.getResourceDate()

		# Remove empty / null attributes from json
		self.json = {k: v for (k, v) in self.json.items() if v is not None }

			# Do some extra validations, if necessary
		if not (res := self.validate(originator))[0]:
			return res

		# Check subscriptions
		CSE.notification.checkSubscriptions(self, C.netResourceUpdate)

		return True, C.rcOK


	def childWillBeAdded(self, childResource, originator):
		""" Called before a child will be added to a resource.
			This method return True, or False in kind the adding should be rejected, and an error code."""
		return True, C.rcOK

	def childAdded(self, childResource, originator):
		""" Called when a child resource was added to the resource. """
		CSE.notification.checkSubscriptions(self, C.netCreateDirectChild, childResource)


	def childRemoved(self, childResource, originator):
		""" Call when child resource was removed from the resource. """
		CSE.notification.checkSubscriptions(self, C.netDeleteDirectChild, childResource)


	def canHaveChild(self, resource):
		""" MUST be implemented by each class."""
		raise NotImplementedError('canHaveChild()')


	def _canHaveChild(self, resource, allowedChildResourceTypes):
		""" It checks whether a fresource may have a certain child resources. This is called from child class. """
		from .Unknown import Unknown # Unknown imports this class, therefore import only here
		return resource['ty'] in allowedChildResourceTypes or isinstance(resource, Unknown)


	def validate(self, originator=None, create=False):
		""" Validate a resource. Usually called within activate() or update() methods. """
		Logging.logDebug('Validating resource: %s' % self.ri)
		if (not Utils.isValidID(self.ri) or
			not Utils.isValidID(self.pi) or
			not Utils.isValidID(self.rn)):
			Logging.logDebug('Invalid ID ri: %s, pi: %s, rn: %s)' % (self.ri, self.pi, self.rn))
			return False, C.rcContentsUnacceptable
		return True, C.rcOK


	def validateExpirations(self):
		"""	Validate possible expirations, of self or child resources.
			MAY be implemented by child class.
		"""
		pass


	#########################################################################

	#
	#	Attribute handling
	#


	def setAttribute(self, name, value, overwrite=True):
		Utils.setXPath(self.json, name, value, overwrite)


	def attribute(self, key, default=None):
		if '/' in key:	# search in path
			return Utils.findXPath(self.json, key, default)
		if self.hasAttribute(key):
			return self.json[key]
		return default


	def hasAttribute(self, key):
		# TODO check sub-elements as well
		return key in self.json


	def delAttribute(self, key):
		if self.hasAttribute(key):
			del self.json[key]


	def __setitem__(self, key, value):
		self.setAttribute(key, value)


	def __getitem__(self, key):
		return self.attribute(key)

	def __delitem__(self, key):
		self.delAttribute(key)


	def __contains__(self, key):
		return self.hasAttribute(key)

	def __getattr__(self, name):
		return self.attribute(name)


	#########################################################################

	#
	#	Attribute specific helpers
	#

	def normalizeURIAttribute(self, attributeName):
		""" Normalie the URLs in the poa, nu etc. """
		if (attribute := self[attributeName]) is not None:
			if isinstance(attribute, list):	# list of uris
				result = []
				for uri in attribute:
					result.append(Utils.normalizeURL(uri))
				self[attributeName] = result
			else: 							# single uri
				self[attributeName] = Utils.normalizeURL(attribute)


	#########################################################################

	#
	#	Database functions
	#

	def dbDelete(self):
		""" Delete the Resource from the database. """
		return CSE.storage.deleteResource(self)


	def dbUpdate(self):
		""" Update the Resource in the database. """
		return CSE.storage.updateResource(self)


	def dbCreate(self, overwrite : bool = False):
		return CSE.storage.createResource(self, overwrite)

	def dbReload(self):
		"""  Load a new copy from the database. The current resource is NOT changed. """
		return CSE.storage.retrieveResource(ri=self.ri)




	#########################################################################

	#
	#	Misc utilities
	#

	def __str__(self):
		""" String representation. """
		return str(self.asJSON())


	def __repr__(self):
		""" Object representation as string. """
		return '%s(ri=%s)' % (self.tpe, self.ri)


	def __eq__(self, other):
		return self.ri == other.ri


	def isModifiedSince(self, other):
		return self.lt > other.lt


	def retrieveParentResource(self):
		(parentResource, _) = CSE.dispatcher.retrieveResource(self.pi)
		return parentResource

