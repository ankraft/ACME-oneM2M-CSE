#
#	Storage.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Store, retrieve and manage resources in the database. It currently relies on
#	the document database TinyDB. It is possible to store resources either on disc
#	or just in memory.
#

from tinydb import TinyDB, Query, where
from tinydb.storages import MemoryStorage
from tinydb.operations import delete
import os, json, re
from threading import Lock
from Configuration import Configuration
from Constants import Constants as C
from Logging import Logging
from resources.Resource import Resource
import Utils

class Storage(object):

	def __init__(self):

		# create data directory
		path = None
		if not Configuration.get('db.inMemory'):
			if Configuration.has('db.path'):
				path = Configuration.get('db.path')
				Logging.log('Using data directory: ' + path)
				os.makedirs(path, exist_ok=True)
			else:
				Logging.logErr('db.path not set')
				raise RuntimeError('db.path not set')

		self.db = TinyDBBinding(path)
		self.db.openDB()

		# Reset dbs?
		if Configuration.get('db.resetAtStartup') is True:
			self.db.purgeDB()

		Logging.log('Storage initialized')


	def shutdown(self):
		self.db.closeDB()
		Logging.log('Storage shut down')


	#########################################################################
	##
	##	Resources
	##


	def createResource(self, resource, overwrite=True):
		if resource is None:
			Logging.logErr('resource is None')
			raise RuntimeError('resource is None')

		ri = resource.ri

		# Logging.logDebug('Adding resource (ty: %d, ri: %s, rn: %s)' % (resource['ty'], resource['ri'], resource['rn']))
		did = None
		srn = resource.__srn__
		if overwrite:
			Logging.logDebug('Resource enforced overwrite')
			self.db.upsertResource(resource)
		else: 
			# if not self.db.hasResource(ri=ri) and not self.db.hasResource(srn=srn):	# Only when not resource does not exist yet
			if not self.hasResource(ri, srn):	# Only when not resource does not exist yet
				self.db.insertResource(resource)
			else:
				Logging.logWarn('Resource already exists (Skipping)')
				return (False, C.rcAlreadyExists)

		# Add path to identifiers db
		self.db.insertIdentifier(resource, ri, srn)
		return (True, C.rcCreated)


	# Check whether a resource with either the ri or the srn already exists
	def hasResource(self, ri, srn):
		return self.db.hasResource(ri=ri) or self.db.hasResource(srn=srn)


	# Return a resource via different addressing methods
	def retrieveResource(self, ri=None, csi=None, srn=None, ty=-1):
		resources = []

		if ri is not None:		# get a resource by its ri
			# Logging.logDebug('Retrieving resource ri: %s' % ri)
			resources = self.db.searchResources(ri=ri)

		elif srn is not None:	# get a resource by its structured rn
			# Logging.logDebug('Retrieving resource srn: %s' % srn)
			# get the ri via the srn from the identifers table
			resources = self.db.searchResources(srn=srn)

		elif csi is not None:	# get the CSE by its csi
			# Logging.logDebug('Retrieving resource csi: %s' % csi)
			resources = self.db.searchResources(csi=csi)

		elif ty != -1:	# get all resources of a specific type
			# Logging.logDebug('Retrieving all resources ty: %d' % ty)
			return self.db.searchResources(ty=ty)

		return Utils.resourceFromJSON(resources[0].copy()) if len(resources) == 1 else None


	def discoverResources(self, rootResource, handling, conditions, attributes, fo):
		# preparations
		rootSRN = rootResource.__srn__
		handling['__returned__'] = 0
		handling['__matched__'] = 0
		if 'lvl' in handling:
			handling['__lvl__'] = rootSRN.count('/') + handling['lvl']

		# a bit of optimization. This length stays the same.
		allLen = ((len(conditions) if conditions is not None else 0) +
		  (len(attributes) if attributes is not None else 0) +
		  (len(conditions['ty']) if conditions is not None else 0) - 1 +
		  (len(conditions['cty']) if conditions is not None else 0) - 1 
		 )

		rs = self.db.discoverResources(lambda r: _testDiscovery(r,
																rootSRN,
																handling,
																conditions,
																attributes,
																fo,
																handling['lim'] if 'lim' in handling else None,
																handling['ofst'] if 'ofst' in handling else None,
																allLen))
		
		# transform JSONs to resources
		result = []
		for r in rs:
			result.append(Utils.resourceFromJSON(r))

		# sort resources by type and then by lowercase rn
		if Configuration.get('cse.sortDiscoveredResources'):
			result.sort(key=lambda x:(x.ty, x.rn.lower()))
		return result


	def updateResource(self, resource):
		if resource is None:
			Logging.logErr('resource is None')
			raise RuntimeError('resource is None')
		ri = resource.ri
		# Logging.logDebug('Updating resource (ty: %d, ri: %s, rn: %s)' % (resource['ty'], ri, resource['rn']))
		resource = self.db.updateResource(resource)
		return (resource, C.rcUpdated)


	def deleteResource(self, resource):
		if resource is None:
			Logging.logErr('resource is None')
			raise RuntimeError('resource is None')
		# Logging.logDebug('Removing resource (ty: %d, ri: %s, rn: %s)' % (resource['ty'], ri, resource['rn']))
		self.db.deleteResource(resource)
		self.db.deleteIdentifier(resource)
		return (True, C.rcDeleted)



	def subResources(self, pi, ty=None):
		rs = self.db.searchResources(pi=pi, ty=ty)

		# if ty is not None:
		# 	rs = self.tabResources.search((Query().pi == pi) & (Query().ty == ty))
		# else:
		# 	rs = self.tabResources.search(Query().pi == pi)			
		result = []
		for r in rs:
			result.append(Utils.resourceFromJSON(r.copy()))
		return result


	def countResources(self):
		return self.db.countResources()


	def identifier(self, ri):
		return self.db.searchIdentifiers(ri=ri)


	def searchByTypeFieldValue(self, ty, field, value):
		"""Search and return all resources of a specific type and a value in a field,
		and return them in an array."""
		result = []
		for j in self.db.searchByTypeFieldValue(ty, field, value):
			result.append(Utils.resourceFromJSON(j))
		return result


	#########################################################################
	##
	##	Subscriptions
	##

	def getSubscription(self, ri):
		# Logging.logDebug('Retrieving subscription: %s' % ri)
		subs = self.db.searchSubscriptions(ri=ri)
		if subs is None or len(subs) != 1:
			return None
		return subs[0]


	def getSubscriptionsForParent(self, pi):
		# Logging.logDebug('Retrieving subscriptions for parent: %s' % pi)
		return self.db.searchSubscriptions(pi=pi)


	def addSubscription(self, subscription):
		# Logging.logDebug('Adding subscription: %s' % ri)
		return self.db.upsertSubscription(subscription)


	def removeSubscription(self, subscription):
		# Logging.logDebug('Removing subscription: %s' % subscription.ri)
		return self.db.removeSubscription(subscription)


	def updateSubscription(self, subscription):
		# Logging.logDebug('Updating subscription: %s' % ri)
		return self.db.upsertSubscription(subscription)


	#########################################################################
	##
	##	Statistics
	##

	def getStatistics(self):
		return self.db.searchStatistics()


	def updateStatistics(self, stats):
		return self.db.upsertStatistics(stats)



	#########################################################################
	##
	##	App Support
	##

	def getAppData(self, id):
		return self.db.searchAppData(id)


	def updateAppData(self, data):
		return self.db.upsertAppData(data)


	def removeAppData(self, data):
		return self.db.removeData(data)


#########################################################################
##
##	internal utilities
##


# handler function for discovery search and matching resources
def _testDiscovery(r, rootSRN, handling, conditions, attributes, fo, lim, ofst, allLen):

	# check limits
	# TinyDB doesn't support pagination. So we need to implement it here. See also offset below.
	if lim is not None and handling['__returned__'] >= lim:
		return False

	# check for SRN first
	# Add / to the "startswith" check to terminate the search string 
	if (srn := r['__srn__']) is not None and rootSRN.count('/') >= srn.count('/') or not srn.startswith(rootSRN+'/') or srn == rootSRN:
		return False

	# Ignore virtual resources TODO: correct?
	# if (ty := r.get('ty')) and ty in C.tVirtualResources:
		# return False
	ty = r.get('ty')

	# ignore some resource types
	if ty in [ C.tGRP_FOPT ]:
		return False


	# check level
	if (h_lvl := handling.get('__lvl__')) is not None and srn.count('/') > h_lvl:
		return False

	# check conditions
	if conditions is not None:
		found = 0
		# found += 1 if (c_ty := conditions.get('ty')) is not None and (str(ty) == c_ty) else 0

		if (ct := r.get('ct')) is not None:
			found += 1 if (c_crb := conditions.get('crb')) is not None and (ct < c_crb) else 0
			found += 1 if (c_cra := conditions.get('cra')) is not None and (ct > c_cra) else 0

		if (lt := r.get('lt')) is not None:
			found += 1 if (c_ms := conditions.get('ms')) is not None and (lt > c_ms) else 0
			found += 1 if (c_us := conditions.get('us')) is not None and (lt < c_us) else 0

		if (st := r.get('st')) is not None:
			found += 1 if (c_sts := conditions.get('sts')) is not None and (str(st) > c_sts) else 0
			found += 1 if (c_stb := conditions.get('stb')) is not None and (str(st) < c_stb) else 0

		if (et := r.get('et')) is not None:
			found += 1 if (c_exb := conditions.get('exb')) is not None and (et < c_exb) else 0
			found += 1 if (c_exa := conditions.get('exa')) is not None and (et > c_exa) else 0

		# special handling of label-list
		if (lbl := r.get('lbl')) is not None and (c_lbl := conditions.get('lbl')) is not None:
			lbla = c_lbl.split()
			fnd = 0
			for l in lbla:
				fnd += 1 if l in lbl else 0
			found += 1 if (fo == 1 and fnd == len(lbl)) or (fo == 2 and fnd > 0) else 0	# fo==or -> find any label

		if ty in [ C.tCIN, C.tFCNT ]:	# special handling for CIN, FCNT
			if (cs := r.get('cs')) is not None:
				found += 1 if (sza := conditions.get('sza')) is not None and (str(cs) >= sza) else 0
				found += 1 if (szb := conditions.get('szb')) is not None and (str(cs) < szb) else 0

		if ty in [ C.tCIN ]:	# special handling for CIN
			if (cnf := r.get('cnf')) is not None:
				found += 1 if cnf in conditions['cty'] else 0

	# TODO labelsQuery
	# TODO childLabels
	# TODO parentLabels
	# TODO childResourceType
	# TODO parentResourceType


	# Attributes:
	if attributes is not None:
		for name in attributes:
			val = attributes[name]
			if '*' in val:
				val = val.replace('*', '.*')
				found += 1 if (rval := r.get(name)) is not None and re.match(val, str(rval)) else 0
			else:
				found += 1 if (rval := r.get(name)) is not None and str(val) == str(rval) else 0

	# TODO childAttribute
	# TODO parentAttribute

	# Test Types
	found += 1 if str(ty) in conditions['ty'] else 0

	# Test whether the OR or AND criteria is fullfilled
	if not ((fo == 2 and found > 0) or 		# OR and found something
			(fo == 1 and allLen == found)	# AND and found everything
	   	   ): 
		return False


	# Check offset. Dont match if offset not reached
	handling['__matched__'] += 1
	if ofst is not None and handling['__matched__'] <= ofst:
		return False

	handling['__returned__'] += 1
	return True



#########################################################################
#
#	DB class that implements the TinyDB binding
#
#	This class may be moved later to an own module.


class TinyDBBinding(object):

	def __init__(self, path=None):
		self.path = path
		self.cacheSize = Configuration.get('db.cacheSize')
		Logging.log('Cache Size: %s' % self.cacheSize)

		# create transaction locks
		self.lockResources = Lock()
		self.lockIdentifiers = Lock()
		self.lockSubscriptions = Lock()
		self.lockStatistics = Lock()
		self.lockAppData = Lock()


	def openDB(self):
		if Configuration.get('db.inMemory'):
			Logging.log('DB in memory')
			self.dbResources = TinyDB(storage=MemoryStorage)
			self.dbIdentifiers = TinyDB(storage=MemoryStorage)
			self.dbSubscriptions = TinyDB(storage=MemoryStorage)
			self.dbStatistics = TinyDB(storage=MemoryStorage)
			self.dbAppData = TinyDB(storage=MemoryStorage)
		else:
			Logging.log('DB in file system')
			self.dbResources = TinyDB(self.path + '/resources.json')
			self.dbIdentifiers = TinyDB(self.path + '/identifiers.json')
			self.dbSubscriptions = TinyDB(self.path + '/subscriptions.json')
			self.dbStatistics = TinyDB(self.path + '/statistics.json')
			self.dbAppData = TinyDB(self.path + '/appdata.json')
		self.tabResources = self.dbResources.table('resources', cache_size=self.cacheSize)
		self.tabIdentifiers = self.dbIdentifiers.table('identifiers', cache_size=self.cacheSize)
		self.tabSubscriptions = self.dbSubscriptions.table('subsriptions', cache_size=self.cacheSize)
		self.tabStatistics = self.dbStatistics.table('statistics', cache_size=self.cacheSize)
		self.tabAppData = self.dbAppData.table('appdata', cache_size=self.cacheSize)


	def closeDB(self):
		Logging.log('Closing DBs')
		self.dbResources.close()
		self.dbIdentifiers.close()
		self.dbSubscriptions.close()
		self.dbStatistics.close()
		self.dbAppData.close()


	def purgeDB(self):
		Logging.log('Purging DBs')
		self.tabResources.purge()
		self.tabIdentifiers.purge()
		self.tabSubscriptions.purge()
		self.tabStatistics.purge()
		self.tabAppData.purge()


	#
	#	Resources
	#


	def insertResource(self, resource):
		with self.lockResources:
			self.tabResources.insert(resource.json)
	

	def upsertResource(self, resource):
		with self.lockResources:
			self.tabResources.upsert(resource.json, Query().ri == resource.ri)	# Update existing or insert new when overwriting
	

	def updateResource(self, resource):
		ri = resource.ri
		with self.lockResources:
			self.tabResources.update(resource.json, Query().ri == ri)
			# remove nullified fields from db and resource
			for k in list(resource.json):
				if resource.json[k] is None:
					self.tabResources.update(delete(k), Query().ri == ri)
					del resource.json[k]
		return resource


	def deleteResource(self, resource):
		with self.lockResources:
			self.tabResources.remove(Query().ri == resource.ri)
	

	def searchResources(self, ri=None, csi=None, srn=None, pi=None, ty=None):

		# find the ri first and then try again recursively
		if srn is not None:
			if len((identifiers := self.searchIdentifiers(srn=srn))) == 1:
				return self.searchResources(ri=identifiers[0]['ri'])
			return []

		with self.lockResources:
			if ri is not None:
				r = self.tabResources.search(Query().ri == ri)
			elif csi is not None:
				r = self.tabResources.search(Query().csi == csi)
			elif pi is not None and ty is not None:
				r = self.tabResources.search((Query().pi == pi) & (Query().ty == ty))
			elif pi is not None:
				r = self.tabResources.search(Query().pi == pi)
			elif ty is not None:
				r = self.tabResources.search(Query().ty == ty)
		return r


	def discoverResources(self, func):
		with self.lockResources:
			rs = self.tabResources.search(func)
		return rs


	def hasResource(self, ri=None, csi=None, srn=None, ty=None):

		# find the ri first and then try again recursively
		if srn is not None:
			if len((identifiers := self.searchIdentifiers(srn=srn))) == 1:
				return self.hasResource(ri=identifiers[0]['ri'])
		ret = False
		with self.lockResources:
			if ri is not None:
				ret = self.tabResources.contains(Query().ri == ri)
			elif csi is not None:
				ret = self.tabResources.contains(Query().csi == csi)
			elif ty is not None:
				ret = self.tabResources.contains(Query().ty == ty)
		return ret


	def countResources(self):
		with self.lockResources:
			result = len(self.tabResources)
		return result


	def  searchByTypeFieldValue(self, ty, field, value):
		"""Search and return all resources of a specific type and a value in a field,
		and return them in an array."""
		with self.lockResources:
			result = self.tabResources.search((Query().ty == ty) & (where(field).any(value)))
		return result



	#
	#	Identifiers
	#


	def insertIdentifier(self, resource, ri, srn):
		with self.lockIdentifiers:
			self.tabIdentifiers.upsert(
				# ri, rn, srn 
				{'ri' : ri, 'rn' : resource.rn, 'srn' : srn, 'ty' : resource.ty}, 
				Query().ri == ri)


	def deleteIdentifier(self, resource):
		with self.lockIdentifiers:
			self.tabIdentifiers.remove(Query().ri == resource.ri)


	def searchIdentifiers(self, ri=None, srn=None):
		with self.lockIdentifiers:
			if srn is not None:
				r = self.tabIdentifiers.search(Query().srn == srn)
			elif ri is not None:
				r = self.tabIdentifiers.search(Query().ri == ri) 
		return r


	#
	#	Subscriptions
	#


	def searchSubscriptions(self, ri=None, pi=None):
		subs = None
		with self.lockSubscriptions:
			if ri is not None:
				subs = self.tabSubscriptions.search(Query().ri == ri)
			if pi is not None:
				subs = self.tabSubscriptions.search(Query().pi == pi)
		return subs


	def upsertSubscription(self, subscription):
		ri = subscription.ri
		with self.lockSubscriptions:
			result = self.tabSubscriptions.upsert(
									{	'ri'  : ri, 
										'pi'  : subscription.pi,
										'nct' : subscription.nct,
										'net' : subscription['enc/net'],
										'nus' : subscription.nu
									}, 
									Query().ri == ri)
		return result is not None


	def removeSubscription(self, subscription):
		with self.lockSubscriptions:
			result = self.tabSubscriptions.remove(Query().ri == subscription.ri)
		return result


	#
	#	Statistics
	#

	def searchStatistics(self):
		stats = None
		with self.lockStatistics:
			stats = self.tabStatistics.get(doc_id=1)
		return stats if stats is not None and len(stats) > 0 else None


	def upsertStatistics(self, stats):
		with self.lockStatistics:
			if len(self.tabStatistics) > 0:
				result = self.tabStatistics.update(stats, doc_ids=[1])
			else:
				result = self.tabStatistics.insert(stats)
		return result is not None


	#
	#	App Data
	#

	def searchAppData(self, id):
		data = None
		with self.lockAppData:
			data = self.tabAppData.get(Query().id == id)
		return data if data is not None and len(data) > 0 else None


	def upsertAppData(self, data):
		if 'id' not in data:
			return None
		with self.lockAppData:
			if len(self.tabAppData) > 0:
				result = self.tabAppData.update(data, Query().id == data['id'])
			else:
				result = self.tabAppData.insert(data)
		return result is not None


	def removeAppData(self, data):
		if 'id' not in data:
			return None
		with self.lockAppData:
			result = self.tabAppData.remove(Query().id == data['id'])
		return result
