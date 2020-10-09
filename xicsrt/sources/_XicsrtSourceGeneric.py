# -*- coding: utf-8 -*-
"""
.. Authors
    Novimir Pablant <npablant@pppl.gov>
    James Kring <jdk0026@tigermail.auburn.edu>
    Yevgeniy Yakusevich <eugenethree@gmail.com>
"""

import numpy as np   
from scipy.stats import cauchy        
import scipy.constants as const

from xicsrt.tools import xicsrt_math
from xicsrt.util import profiler
from xicsrt.tools import voigt
from xicsrt.tools.xicsrt_doc import dochelper_config
from xicsrt.objects._GeometryObject import GeometryObject

@dochelper_config
class XicsrtSourceGeneric(GeometryObject):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filter_objects = []
            
    def default_config(self):
        """
        width
          The width of this element. Aligned with the x-axis.

        height
          The height of this element. Aligned with the y-axis.

        depth:
          The depth of this element. Aligned with the z-axis.

        spread: float (pi) [radians]
          The angular spread for the emission cone. The spread defines the
          half-angle of the cone. A value of `pi` results in fully isotropic
          emission (which is not generally useful in raytracing applications).

        intensity: int or float
          The number of rays for this source to emit. This should be an
          integer value unless `use_poisson = True`.

          Note: If filters are attached, this will be the number of rays
          emitted before filtering.

        use_poisson: bool (False)
          If `True` the `intenisty` will be treated as the expected value for
          a Poisson distribution and the number of rays will be randomly
          picked from a Poisson distribution. This is setting is typically
          only used internally for Plasma sources.

        wavelength_dist: str ('voigt')
          The type of wavelength distribution for this source.
          Possible values are: 'voigt', 'uniform', 'monochrome'.

        wavelength: float [angstroms]
          No documentation yet. Please help improve XICSRT!

        wavelength_range: tuple [angstroms]
          Only used if `wavelength_dist = "uniform"`
          No documentation yet. Please help improve XICSRT!

        linewidth: float [1/s]
          Only used if `wavelength_dist = "voigt"`
          No documentation yet. Please help improve XICSRT!

        temperature: float [eV]
          Only used if `wavelength_dist = "voigt"`
          No documentation yet. Please help improve XICSRT!

        velocity
          No documentation yet. Please help improve XICSRT!

        filter_list
          No documentation yet. Please help improve XICSRT!

        """
        config = super().default_config()

        config['width'] = 0.0
        config['height'] = 0.0
        config['depth'] = 0.0

        config['spread']         = np.pi

        config['wavelength_dist']  = 'voigt'
        config['mass_number']      = 1.0
        config['intensity']        = 0.0
        config['use_poisson']      = False

        # Only used for wavelength_dist == 'voigt' or 'monochrome'
        config['wavelength']       = 1.0

        # Only used for wavelength_dist == 'voigt'
        config['linewidth']        = 0.0
        config['temperature']      = 0.0
        config['velocity']         = np.array([0.0, 0.0, 0.0])

        # Only used for wavelength_dist == 'uniform'
        config['wavelength_range'] = np.array([0.0, 0.0])
        
        config['filter_list']    = []

        return config

    def initialize(self):
        super().initialize()
        
        if self.param['use_poisson']:
            self.param['intensity'] = np.random.poisson(self.param['intensity'])
        else:
            if self.param['intensity'] < 1:
                raise ValueError('intensity of less than one encountered. Turn on poisson statistics.')
        self.param['intensity'] = int(self.param['intensity'])
        
    def generate_rays(self):
        rays = dict()
        profiler.start('generate_rays')
        
        profiler.start('generate_origin')
        rays['origin'] = self.generate_origin()
        profiler.stop('generate_origin')

        profiler.start('generate_direction')
        rays['direction'] = self.generate_direction(rays['origin'])
        profiler.stop('generate_direction')

        profiler.start('generate_wavelength')
        rays['wavelength'] = self.generate_wavelength(rays['direction'])
        profiler.stop('generate_wavelength')

        profiler.start('generate_weight')
        rays['weight'] = self.generate_weight()
        profiler.stop('generate_weight')
        
        profiler.start('generate_mask')
        rays['mask'] = self.generate_mask()
        profiler.stop('generate_mask')
        
        profiler.start('filter_rays')
        rays = self.ray_filter(rays)
        profiler.stop('filter_rays')        
        
        profiler.stop('generate_rays')
        return rays
     
    def generate_origin(self):
        # generic origin for isotropic rays
        w_offset = np.random.uniform(-1 * self.param['width']/2 ,  self.param['width']/2, self.param['intensity'])
        h_offset = np.random.uniform(-1 * self.param['height']/2, self.param['height']/2, self.param['intensity'])
        d_offset = np.random.uniform(-1 * self.param['depth']/2 ,  self.param['depth']/2, self.param['intensity'])
        
        origin = (self.origin
                  + np.einsum('i,j', w_offset, self.xaxis)
                  + np.einsum('i,j', h_offset, self.yaxis)
                  + np.einsum('i,j', d_offset, self.zaxis))
        return origin

    def generate_direction(self, origin):
        normal = self.make_normal()
        D = self.random_direction(normal)
        return D

    def make_normal(self):
        array = np.empty((self.param['intensity'], 3))
        array[:] = self.param['zaxis']
        normal = array / np.linalg.norm(array, axis=1)[:, np.newaxis]
        return normal

    def random_direction(self, normal):

        rad_spread = self.param['spread']
        dir_local  = xicsrt_math.vector_dist_uniform(rad_spread, self.param['intensity'])

        # Generate some basis vectors that are perpendicular
        # to the normal. The orientation does not matter here.
        o_1  = np.cross(normal, np.array([0,0,1])) + np.cross(normal, np.array([0,1,0]))
        o_1 /=  np.linalg.norm(o_1, axis=1)[:, np.newaxis]
        o_2  = np.cross(normal, o_1)
        o_2 /=  np.linalg.norm(o_2, axis=1)[:, np.newaxis]

        R        = np.empty((self.param['intensity'], 3, 3))
        R[:,0,:] = o_1
        R[:,1,:] = o_2
        R[:,2,:] = normal
        
        direction = np.einsum('ij,ijk->ik', dir_local, R)
        return direction

    def generate_wavelength(self, direction):
        wtype = str.lower(self.param['wavelength_dist'])
        if wtype == 'monochrome':
            wavelength  = np.ones(self.param['intensity'], dtype = np.float64)
            wavelength *= self.param['wavelength']
        elif wtype == 'uniform':
            wavelength = np.random.uniform(
                self.param['wavelength_range'][0]
                ,self.param['wavelength_range'][1]
                ,self.param['intensity']
                )
        elif wtype == 'voigt':
            #random_wavelength = self.random_wavelength_normal
            #random_wavelength = self.random_wavelength_cauchy
            random_wavelength = self.random_wavelength_voigt
            wavelength = random_wavelength(self.param['intensity'])
            
            #doppler shift
            c = const.physical_constants['speed of light in vacuum'][0]
            wavelength *= 1 - (np.einsum('j,ij->i', self.param['velocity'], direction) / c)
        
        return wavelength

    def random_wavelength_voigt(self, size=None):
        #Units: wavelength (angstroms), natural_linewith (1/s), temperature (eV)
        
        # Check for the trivial case.
        if (self.param['linewidth']  == 0.0 and self.param['temperature'] == 0.0):
            return np.ones(size)*self.param['wavelength']
        # Check for the Lorentzian case.
        if (self.param['temperature'] == 0.0):
            # I need to update the cauchy routine first.
            #raise NotImplementedError('Random Lorentzian distribution not implemented.')

            # TEMPORARY:
            # The raytracer cannot currently accept a zero temperature, so just add 1eV for now.
            self.param['temperature'] += 1.0
             
        # Check for the Gaussian case.
        if (self.param['linewidth']  == 0.0):
            return self.random_wavelength_normal(size)

        c = const.physical_constants['speed of light in vacuum'][0]
        amu_kg = const.physical_constants['atomic mass unit-kilogram relationship'][0]
        ev_J = const.physical_constants['electron volt-joule relationship'][0]
        
        # Natural line width.
        gamma = (self.param['linewidth'] * self.param['wavelength']**2 / (4 * np.pi * c * 1e10))

        # Doppler broadened line width.
        sigma = (np.sqrt(self.param['temperature'] / self.param['mass_number'] / amu_kg / c**2 * ev_J)
                  * self.param['wavelength'] )

        rand_wave  = voigt.voigt_random(gamma, sigma, size)
        rand_wave += self.param['wavelength']
        return rand_wave

    def random_wavelength_normal(self, size=None):
        #Units: wavelength (angstroms), temperature (eV)
        c       = const.physical_constants['speed of light in vacuum'][0]
        amu_kg  = const.physical_constants['atomic mass unit-kilogram relationship'][0]
        ev_J    = const.physical_constants['electron volt-joule relationship'][0]
        
        # Doppler broadened line width.
        sigma = ( np.sqrt(self.param['temperature'] / self.param['mass_number'] / amu_kg / c**2 * ev_J)
                  * self.param['wavelength'] )

        rand_wave = np.random.normal(self.param['wavelength'], sigma, size)
        return rand_wave
    
    def random_wavelength_cauchy(self, size=None):
        # This function needs to be updated to use the same definitions
        # as random_wavelength_voigt.
        #
        # As currently writen natual_linewidth is not used in a way
        # consistent with physical units.
        #
        # It also may make sense to add some sort of cutoff here.
        # the extreme tails of the distribution are not really useful
        # for ray tracing.
        fwhm = self.param['linewidth']
        rand_wave = cauchy.rvs(loc=self.param['wavelength'], scale=fwhm, size=size)
        return rand_wave
    
    def generate_weight(self):
        # Weight is not currently used within XICSRT but might be useful
        # in the future.
        w = np.ones((self.param['intensity']), dtype=np.float64)
        return w
    
    def generate_mask(self):
        m = np.ones((self.param['intensity']), dtype=np.bool)
        return m
    
    def ray_filter(self, rays):
        for filter in self.filter_objects:
            rays = filter.filter(rays)
        return rays
