#
#	DVCAnnc.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	DVC : Announceable variant
#

from .MgmtObj import *
from Types import ResourceTypes as T
import Utils


class DVCAnnc(MgmtObjAnnc):

	def __init__(self, jsn: dict = None, pi: str = None, create: bool = False) -> None:
		super().__init__(jsn, pi, mgd=T.DVC, create=create)

