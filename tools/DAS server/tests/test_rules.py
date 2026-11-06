#
#	test_rules.py
#
#	(c) 2026 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for dass.Rules - run from the "DAS server" directory:
#		python3 -m unittest discover -s tests
#

import unittest, tempfile
from pathlib import Path

from dass.Rules import Rules, operationToPermission


class TestOperationToPermission(unittest.TestCase):
	""" Direct tests for the request-operation-code to permission-bit translation. """

	def test_create(self) -> None:
		self.assertEqual(operationToPermission(1), 1)

	def test_retrieve(self) -> None:
		self.assertEqual(operationToPermission(2), 2)

	def test_update(self) -> None:
		""" The specific regression case for Bug 1: op=3 (UPDATE) must map to permission bit 4,
			not be compared against the bit value 3 (which doesn't exist). """
		self.assertEqual(operationToPermission(3), 4)

	def test_delete(self) -> None:
		""" The specific regression case for Bug 1: op=4 (DELETE) must map to permission bit 8,
			not collide with the UPDATE permission bit (4). """
		self.assertEqual(operationToPermission(4), 8)

	def test_notify(self) -> None:
		self.assertEqual(operationToPermission(5), 16)

	def test_discovery(self) -> None:
		""" DISCOVERY's request-op code (-2) has no arithmetic relationship to its permission
			bit (32) - it must be an explicit table entry. """
		self.assertEqual(operationToPermission(-2), 32)

	def test_unknown(self) -> None:
		self.assertIsNone(operationToPermission(99))

	def test_none(self) -> None:
		self.assertIsNone(operationToPermission(None))


class TestRulesGetAcrs(unittest.TestCase):
	""" End-to-end tests for Rules.getAcrs() against real rule files on disk, covering the
		request-operation-code translation together with the pre-existing rule-file syntax
		(letters, numbers, bitmask sums).
	"""

	def setUp(self) -> None:
		self._tmpDir = tempfile.TemporaryDirectory()
		rulesPath = Path(self._tmpDir.name)
		(rulesPath / '_common.yaml').write_text("""
rules:
  - match:
      operation: [U]
    grant:
      acor: ["RuleLetterU"]

  - match:
      operation: 8
    grant:
      acor: ["RuleNum8"]

  - match:
      operation: [F]
    grant:
      acor: ["RuleLetterF"]

  - match:
      operation: 6
    grant:
      acor: ["RuleBitmask6"]

  - grant:
      acor: ["RuleNoOperation"]
      acop: [R]
""")
		self.rules = Rules(str(rulesPath))

	def tearDown(self) -> None:
		self._tmpDir.cleanup()

	def _acors(self, operation: int) -> set:
		""" Helper: the set of acor markers granted for a given request operation code. """
		grants = self.rules.getAcrs(cseId='id-in', originator='Ctest', resourceId='id-in/cnt-1',
									 resourceType=3, operation=operation)
		return { acor for grant in grants for acor in grant['acor'] }

	def test_letterRuleMatchesUpdate(self) -> None:
		""" op=3 (UPDATE) must now match a rule written as operation: [U]. """
		self.assertIn('RuleLetterU', self._acors(3))

	def test_numberRuleMatchesDeleteNotUpdate(self) -> None:
		""" op=4 (DELETE) must match operation: 8, and op=3 (UPDATE) must NOT - the exact
			DELETE/UPDATE collision Bug 1 caused. """
		self.assertIn('RuleNum8', self._acors(4))
		self.assertNotIn('RuleNum8', self._acors(3))

	def test_letterRuleMatchesDiscovery(self) -> None:
		""" op=-2 (DISCOVERY) must match operation: [F]. """
		self.assertIn('RuleLetterF', self._acors(-2))

	def test_bitmaskRuleMatchesRetrieveAndUpdateNotCreate(self) -> None:
		""" operation: 6 (R+U bitmask) must match op=2 (RETRIEVE) and op=3 (UPDATE), but not
			op=1 (CREATE) - confirms the rule-file bitmask feature and the request-operation
			translation compose correctly. """
		self.assertIn('RuleBitmask6', self._acors(2))
		self.assertIn('RuleBitmask6', self._acors(3))
		self.assertNotIn('RuleBitmask6', self._acors(1))

	def test_noOperationRuleMatchesAnyOperation(self) -> None:
		""" A rule with no "operation" condition at all matches regardless of the request's
			operation, including an unrecognized one. """
		for op in (1, 2, 3, 4, 5, -2, 99):
			self.assertIn('RuleNoOperation', self._acors(op))

	def test_unknownOperationOnlyMatchesNoOperationRule(self) -> None:
		""" An unrecognized request operation code must only match rules with no "operation"
			condition - never a rule with an explicit operation list. """
		acors = self._acors(99)
		self.assertEqual(acors, { 'RuleNoOperation' })

	def test_noneOperationOnlyMatchesNoOperationRule(self) -> None:
		acors = self._acors(None)
		self.assertEqual(acors, { 'RuleNoOperation' })


if __name__ == '__main__':
	unittest.main()
