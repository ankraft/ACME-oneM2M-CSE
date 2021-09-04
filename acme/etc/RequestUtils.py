#
#	RequestUtils.py
#
#	(c) 2021 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	This module contains various utilty functions that are used to work with requests and responses
#


from __future__ import annotations
import cbor2, json
from typing import cast
from .Types import ContentSerializationType, JSON
from ..helpers import TextTools


def serializeData(data:JSON, ct:ContentSerializationType) -> str|bytes|JSON:
	"""	Serialize a dictionary, depending on the serialization type.
	"""
	if ct == ContentSerializationType.PLAIN:
		return data
	encoder = json if ct == ContentSerializationType.JSON else cbor2 if ct == ContentSerializationType.CBOR else None
	if not encoder:
		return None
	return encoder.dumps(data)	# type:ignore[no-any-return]


def deserializeData(data:bytes, ct:ContentSerializationType) -> JSON:
	"""	Deserialize data into a dictionary, depending on the serialization type.
		If the len of the data is 0 then an empty dictionary is returned. 
	"""
	if len(data) == 0:
		return {}
	if ct == ContentSerializationType.JSON:
		return cast(JSON, json.loads(TextTools.removeCommentsFromJSON(data.decode('utf-8'))))
	elif ct == ContentSerializationType.CBOR:
		return cast(JSON, cbor2.loads(data))
	return None
