# -*- coding: utf-8 -*-
"""
Authors
-------
- Novimir A. Pablant <npblant@pppl.gov>
"""
import numpy as np
import logging
from copy import deepcopy

from xicsrt.objects._ConfigObject import ConfigObject
from xicsrt.tools import xicsrt_math as xm

class GeometryObject(ConfigObject):
    """
    The base class for any geometrical objects used in XICSRT.
    """

    def __getattr__(self, key):
        """
        Setup shortcuts for the basic object properties.
        """
        if key == 'xaxis':
            return self.orientation[0, :]
        elif key == 'yaxis':
            return self.orientation[1, :]
        elif key == 'zaxis':
            return self.orientation[2, :]
        else:
            raise AttributeError(key)

    def get_default_config(self):
        config = super().get_default_config()
        config['origin'] = np.array([0.0, 0.0, 0.0])
        config['zaxis'] = np.array([0.0, 0.0, 1.0])
        config['xaxis'] = None

        return config

    def setup(self):
        super().setup()

        self.param['origin'] = np.array(self.param['origin'])
        self.param['zaxis'] = np.array(self.param['zaxis'])
        if self.param['xaxis'] is not None:
            self.param['xaxis'] = np.array(self.param['xaxis'])

        # Location with respect to the external coordinate system.
        self.origin = self.param['origin']
        self.set_orientation(self.param['zaxis'], self.param['xaxis'])

    def set_orientation(self, zaxis, xaxis=None):
        if xaxis is None:
            xaxis = self.get_default_xaxis(zaxis)

        self.orientation = np.array([xaxis, np.cross(zaxis, xaxis), zaxis])

    def get_default_xaxis(self, zaxis):
        """
        Get the X-axis using a default definition.

        In order to fully define the orientation of a component both, a z-axis
        and an x-axis are expected.  For certain types of components the x-axis
        definition is unimportant and can be defined using a default definition.
        """

        xaxis = np.cross(np.array([0.0, 0.0, 1.0]), zaxis)
        if not np.all(xaxis == 0.0):
            xaxis /= np.linalg.norm(xaxis)
        else:
            xaxis = np.array([1.0, 0.0, 0.0])

        return xaxis

    def ray_to_external(self, ray_local, copy=False):

        if copy:
            # Programming Note:
            #   If XICSRT is ever updated to always use ray objects then the
            #   copy method should be used instead of deepcopy for speed.
            ray_external = deepcopy(ray_local)
        else:
            ray_external = ray_local

        ray_external['origin'] = self.point_to_external(ray_external['origin'])
        ray_external['direction'] = self.vector_to_external(ray_external['direction'])
        return ray_external

    def ray_to_local(self, ray_external, copy=False):
        if copy:
            ray_local = deepcopy(ray_external)
        else:
            ray_local = ray_external

        ray_local['origin'] = self.point_to_local(ray_local['origin'])
        ray_local['direction'] = self.vector_to_local(ray_local['direction'])
        return ray_local

    def point_to_external(self, point_local):
        return self.vector_to_external(point_local) + self.origin

    def point_to_local(self, point_external):
        return self.vector_to_local(point_external - self.origin)

    def vector_to_external(self, vector):
        vector = self.to_ndarray(vector)
        if vector.ndim == 2:
            vector[:] = np.einsum('ij,ki->kj', self.orientation, vector)
        elif vector.ndim == 1:
            vector[:] = np.einsum('ij,i->j', self.orientation, vector)
        else:
            raise Exception('vector.ndim must be 1 or 2')

        return vector

    def vector_to_local(self, vector):
        vector = self.to_ndarray(vector)
        if vector.ndim == 2:
            vector[:] = np.einsum('ji,ki->kj', self.orientation, vector)
        elif vector.ndim == 1:
            vector[:] = np.einsum('ji,i->j', self.orientation, vector)
        else:
            raise Exception('vector.ndim must be 1 or 2')
        return vector

    def aim_to_point(self, aim_point, xaxis=None):
        """
        Set the Z-Axis to aim at a particular point.
        """

        zaxis = aim_point - self.origin
        xm.normalize(zaxis)

        if xaxis is None:
            xaxis = self.get_default_xaxis(zaxis)

        output = {'zaxis': zaxis, 'xaxis': xaxis}

        return output

    def to_ndarray(self, vector_in):
        if not isinstance(vector_in, np.ndarray):
            vector_in = np.array(vector_in, dtype=np.float64)
        return vector_in

    def to_vector_array(self, vector_in):
        """
        Convert a vector to a numpy vector array (if needed).
        """
        vector_in = self.to_ndarray(vector_in)

        if vector_in.ndim < 2:
            return vector_in[None, :]
        else:
            return vector_in

