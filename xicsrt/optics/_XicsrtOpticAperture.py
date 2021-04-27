# -*- coding: utf-8 -*-
"""
.. Authors
    Novimir Pablant <npablant@pppl.gov>
    Nathan Bartlett <nbb0011@auburn.edu>
"""
import numpy as np

from xicsrt.tools.xicsrt_doc import dochelper
from xicsrt.optics._XicsrtOpticGeneric import XicsrtOpticGeneric

@dochelper

class XicsrtOpticAperture(XicsrtOpticGeneric):
    """
    An optic that can be used to set an aperture.

    Programming Notes
    -----------------

    All of the implementation for the aperture is in :any:`XicsrtOpticGeneric`,
    so nothing is needed in this subclass for the time being.
    """

    pass

