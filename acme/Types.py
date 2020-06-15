#
#	Types.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Various CSE and oneM2M types
#

from enum import IntEnum, auto


class BasicType(IntEnum):
	""" Basic resource types """
	positiveInteger	= auto()
	nonNegInteger	= auto()
	unsignedInt		= auto()
	unsignedLong	= auto()
	string 			= auto()
	timestamp		= auto()
	list 			= auto()
	dict 			= auto()
	anyURI			= auto()
	boolean			= auto()
	geoCoordinates	= auto()


class Cardinality(IntEnum):
	""" Resource attribute cardinalities """
	car1			= auto()
	car01			= auto()
	car01L			= auto()


class RequestOptionality(IntEnum):
	""" request optionalities """
	NP				= auto()
	O 				= auto()
	M 				= auto()


class Announced(IntEnum):
	""" anouncent attribute indications """
	NA				= auto()
	MA				= auto()
	OA				= auto()
