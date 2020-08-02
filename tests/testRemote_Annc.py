#
#	tesRemote_Annc.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for Announcementfunctionality to a remote CSE. Tests are
#	skipped if there is no remote CSE.
#

import unittest, sys
sys.path.append('../acme')
from Constants import Constants as C
from Types import ResourceTypes as T
from init import *


# The following code must be executed before anything else because it influences
# the collection of skipped tests.
# It checks whether there actually is a remote CSE.
_, rsc = RETRIEVE(REMOTEcseURL, REMOTEORIGINATOR)
noRemote = rsc != C.rcOK

class TestRemote_Annc(unittest.TestCase):

	@classmethod
	def setUpClass(cls):
		# check connection to CSE's
		cls.cse, rsc = RETRIEVE(cseURL, ORIGINATOR)
		assert rsc == C.rcOK, 'Cannot retrieve CSEBase: %s' % cseURL


	@classmethod
	def tearDownClass(cls):
		pass


	# Retrieve the CSR on the local CSE
	@unittest.skipIf(noRemote, 'No remote CSEBase')
	def test_todo(self):
		pass

# add ae with AT and AA
# add ae with AT, AA later
# add ae without AT, with AA, AT later
# update ae
# add to AA
# remove from AA
# remove whole AA
# remove from AT
# remove whole ATs


def run():
	suite = unittest.TestSuite()
	suite.addTest(TestRemote_Annc('test_todo'))
	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=True).run(suite)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped)


if __name__ == '__main__':
	_, errors, _ = run()
	sys.exit(errors)
