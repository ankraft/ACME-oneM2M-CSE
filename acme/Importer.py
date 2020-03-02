#
#	Importer.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Entity to import various resources into the CSE. It is mainly run before 
#	the CSE is actually started.
#

import json, os, fnmatch
from Utils import *
from Configuration import Configuration
from Constants import Constants as C
import CSE
from Logging import Logging
from resources import Resource


class Importer(object):

	# List of "priority" resources that must be imported first for correct CSE operation
	_firstImporters = [ 'csebase.json', 'acp.admin.json', 'acp.default.json' ]

	def __init__(self):
		Logging.log('Importer initialized')


	def importResources(self, path=None):

		# Only when the DB is empty else don't imports
		if CSE.dispatcher.countResources() > 0:
			Logging.log('Resources already imported, skipping importing')
			# But we still need the CSI etc of the CSE
			rss = CSE.dispatcher.retrieveResourcesByType(C.tCSEBase)
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
				with open(fn) as jfile:
					r = resourceFromJSON(json.load(jfile), create=True)
			# Check resource creation
			if not CSE.registration.checkResourceCreation(r, originator):
				continue
			CSE.dispatcher.createResource(r)
			ty = r.ty
			if ty == C.tCSEBase:
				Configuration.set('cse.csi', r.csi)
				Configuration.set('cse.ri', r.ri)
				Configuration.set('cse.rn', r.rn)
				hasCSE = True
			elif ty == C.tACP:
				hasACP = True

		# Check presence of CSE and at least one ACP
		if not (hasCSE and hasACP):
			Logging.logErr('CSE and/or default ACP missing during import')
			self._finishImporting()
			return False


		# then get the filenames of all other files and sort them. Process them in order

		filenames = sorted(os.listdir(path))
		for fn in filenames:
			if fn not in self._firstImporters:
				Logging.log('Importing resource from file: %s' % fn)
				with open(path + '/' + fn) as jfile:

					# update an existing resource
					if 'update' in fn:
						j = json.load(jfile)
						keys = list(j.keys())
						if len(keys) == 1 and (k := keys[0]) and 'ri' in j[k] and (ri := j[k]['ri']) is not None:
							(r, _) = CSE.dispatcher.retrieveResource(ri)
							if r is not None:
								CSE.dispatcher.updateResource(r, j)

					# create a new cresource
					else:
						r = resourceFromJSON(json.load(jfile), create=True)
						# Try to get parent resource
						if r is not None:
							parent = None
							if (pi := r.pi) is not None:
								(parent, _) = CSE.dispatcher.retrieveResource(pi)
							# Check resource creation
							if not CSE.registration.checkResourceCreation(r, originator):
								continue
							# Add the resource
							CSE.dispatcher.createResource(r, parent)
						else:
							Logging.logWarn('Unknown resource in file: %s' % fn)

		self._finishImporting()
		return True


	def _prepareImporting(self):
		# temporarily disable access control
		self._oldacp = Configuration.get('cse.enableACPChecks')
		Configuration.set('cse.enableACPChecks', False)


	def _finishImporting(self):
		Configuration.set('cse.enableACPChecks', self._oldacp)

