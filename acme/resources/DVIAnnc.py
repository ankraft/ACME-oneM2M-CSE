#
#	DVIAnnc.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	DVI : Announceable variant
#

from .MgmtObjAnnc import *
from Types import ResourceTypes as T
import Utils


class DVIAnnc(MgmtObjAnnc):

	def __init__(self, jsn: dict = None, pi: str = None, create: bool = False) -> None:
		super().__init__(jsn, pi, mgd=T.DVI, create=create)

