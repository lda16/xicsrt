# -*- coding: utf-8 -*-
"""
Created on Wed Sep 25 10:55:01 2019

Authors
-------
  - Yevgeniy Yakusevich <eugenethree@gmail.com>

Description
-----------
This script takes in all of the input parameters from the raytracer and makes
a 3D visualization of the X-Ray optics setup using matplotlib Axes3D
"""
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

def visualize_layout(general_input, source_input, graphite_input, crystal_input,
                     detector_input):
    ## Setup plot and axes
    fig = plt.figure()
    ax  = fig.gca(projection='3d')
    
    ax.set_xlim( 0, 4)
    ax.set_ylim(-2, 2)
    
    ax.set_zlim(-1, 1)
    plt.title("X-Ray Optics Layout")
    
    ## Setup variables, described below
    position = np.zeros([4,3], dtype = np.float64)
    normal   = np.zeros([4,3], dtype = np.float64)
    orient_x = np.zeros([4,3], dtype = np.float64)
    orient_y = np.zeros([4,3], dtype = np.float64)
    width    = np.zeros([4], dtype = np.float64)[:,np.newaxis]
    height   = np.zeros([4], dtype = np.float64)[:,np.newaxis]
    
    corners = np.zeros([4,5,3], dtype = np.float64)
    
    beamline = np.zeros([4,3], dtype = np.float64)
    
    circle_points   = np.linspace(0, np.pi * 2, 36)[:,np.newaxis]
    crystal_circle  = np.zeros([36,3], dtype = np.float64)
    rowland_circle  = np.zeros([36,3], dtype = np.float64)
    
    meridi_line = np.zeros([2,3], dtype = np.float64)
    saggit_line = np.zeros([2,3], dtype = np.float64)
    
    ## Define variables
    #for slicing puposes, each optical element now has a number
    #source = 0, graphite = 1, crystal = 2, detector = 3
    
    #position[Optical Element Number, 3D Coordinates]
    position[0,:] = source_input['source_position']
    position[1,:] = graphite_input['graphite_position']
    position[2,:] = crystal_input['crystal_position']
    position[3,:] = detector_input['detector_position']
    #normal[Optical Element Number, 3D Coordinates]
    normal[0,:] = source_input['source_normal']
    normal[1,:] = graphite_input['graphite_normal']
    normal[2,:] = crystal_input['crystal_normal']
    normal[3,:] = detector_input['detector_normal']
    #orient_x[Optical Element Number, 3D Coordinates]
    orient_x[0,:] = source_input['source_orientation']
    orient_x[1,:] = graphite_input['graphite_orientation']
    orient_x[2,:] = crystal_input['crystal_orientation']
    orient_x[3,:] = detector_input['detector_orientation']
    #orient_y[Optical Element Number, 3D Coordinates]
    orient_y[0,:] = np.cross(normal[0,:], orient_x[0,:]) 
    orient_y[1,:] = np.cross(normal[1,:], orient_x[1,:]) 
    orient_y[2,:] = np.cross(normal[2,:], orient_x[2,:]) 
    orient_y[3,:] = np.cross(normal[3,:], orient_x[3,:])
    #width[Optical Element Number]
    width[0] = source_input['source_width']
    width[1] = graphite_input['graphite_width'] 
    width[2] = crystal_input['crystal_width']
    width[3] = detector_input['pixel_size'] * detector_input['horizontal_pixels']
    #height[Optical Element Number]
    height[0] = source_input['source_height']
    height[1] = graphite_input['graphite_height']
    height[2] = crystal_input['crystal_height']
    height[3] = detector_input['pixel_size'] * detector_input['vertical_pixels']
    #crystal optical properties [Float64]
    crystal_bragg = crystal_input['crystal_bragg']
    meridi_focus  = crystal_input['meridi_focus']
    sagitt_focus  = crystal_input['sagitt_focus']
    
    ## Create Bounding Boxes
    #3D coordinates of the four corners of each optical element 
    #The 5th corner is a duplicate of the 1st, it closes the bounding box
    #corners[Optical Element Number, Corner Number, 3D Coordinates]
    corners[:,0,:] = (position[:,:] - (width[:] * orient_x[:,:] / 2) + (height[:] * orient_y[:,:] / 2))   
    corners[:,1,:] = (position[:,:] + (width[:] * orient_x[:,:] / 2) + (height[:] * orient_y[:,:] / 2))   
    corners[:,2,:] = (position[:,:] + (width[:] * orient_x[:,:] / 2) - (height[:] * orient_y[:,:] / 2))  
    corners[:,3,:] = (position[:,:] - (width[:] * orient_x[:,:] / 2) - (height[:] * orient_y[:,:] / 2))  
    corners[:,4,:] = (position[:,:] - (width[:] * orient_x[:,:] / 2) + (height[:] * orient_y[:,:] / 2))
    
    ## The line connecting the centers of all optical elements
    #beamline[Optical Element Number, 3D Coordinates]
    if general_input['backwards_raytrace'] is False:
        beamline[:,:] = position[:,:]
    
    elif general_input['backwards_raytrace'] is True:
        beamline[0,:] = position[3,:]
        beamline[1,:] = position[1,:]
        beamline[2,:] = position[2,:]
        beamline[3,:] = position[0,:]
        
    ## The crystal's radius of curvature and Rowland circle
    #crystal_center[3D Coodrinates]
    crystal_center  =(crystal_input['crystal_curvature'] 
                    * crystal_input['crystal_normal']
                    + crystal_input['crystal_position'])
    #crystal_circle[Point Number, 3D Coordinates], 36 evenly-spaced points
    crystal_circle  = crystal_input['crystal_curvature'] * (
            (orient_y[2,:] * np.cos(circle_points)) + (normal[2,:] * np.sin(circle_points)))
    crystal_circle += crystal_center
    
    rowland_circle  = crystal_input['crystal_curvature'] * np.cos(crystal_bragg) * (
            (orient_y[2,:] * np.cos(circle_points)) + (normal[2,:] * np.sin(circle_points)))
    rowland_circle += crystal_center
    
    ## The crystal's saggital and meridional foci
    inbound_vector = position[1,:] - position[2,:]
    inbound_vector/= np.linalg.norm(inbound_vector)
    #meridi_line[Point Number, 3D Coordinates], 2 points (one above, one below)
    meridi_line[0,:] = position[2,:] + meridi_focus * inbound_vector + 0.1 * orient_x[2,:]
    meridi_line[1,:] = position[2,:] + meridi_focus * inbound_vector - 0.1 * orient_x[2,:]
    saggit_line[0,:] = position[2,:] + sagitt_focus * inbound_vector + 0.1 *   normal[2,:]
    saggit_line[1,:] = position[2,:] + sagitt_focus * inbound_vector - 0.1 *   normal[2,:]
    
    ## Plot everything
    #position points
    ax.scatter(position[0,0], position[0,1], position[0,2], color = "yellow")
    ax.scatter(position[1,0], position[1,1], position[1,2], color = "grey")
    ax.scatter(position[2,0], position[2,1], position[2,2], color = "cyan")
    ax.scatter(position[3,0], position[3,1], position[3,2], color = "red")
    
    #normal vectors
    ax.quiver(position[0,0], position[0,1], position[0,2],
              normal[0,0]  , normal[0,1]  , normal[0,2]  ,
              color = "yellow", length = 0.1, arrow_length_ratio = 0.1)
    ax.quiver(position[1,0], position[1,1], position[1,2],
              normal[1,0]  , normal[1,1]  , normal[1,2]  ,
              color = "grey", length = 0.1, arrow_length_ratio = 0.1)
    ax.quiver(position[2,0], position[2,1], position[2,2],
              normal[2,0]  , normal[2,1]  , normal[2,2]  ,
              color = "cyan", length = 0.1, arrow_length_ratio = 0.1)
    ax.quiver(position[3,0], position[3,1], position[3,2],
              normal[3,0]  , normal[3,1]  , normal[3,2]  ,
              color = "red", length = 0.1 , arrow_length_ratio = 0.1)
    
    #beamline
    ax.plot3D(beamline[:,0], beamline[:,1], beamline[:,2], "black")
    
    #bounding boxes
    ax.plot3D(corners[0,:,0], corners[0,:,1], corners[0,:,2], color = "yellow")
    ax.plot3D(corners[1,:,0], corners[1,:,1], corners[1,:,2], color = "grey")
    ax.plot3D(corners[2,:,0], corners[2,:,1], corners[2,:,2], color = "cyan")
    ax.plot3D(corners[3,:,0], corners[3,:,1], corners[3,:,2], color = "red")
    
    #circles
    ax.plot3D(crystal_circle[:,0], crystal_circle[:,1], crystal_circle[:,2], color = "blue")
    ax.plot3D(rowland_circle[:,0], rowland_circle[:,1], rowland_circle[:,2], color = "blue")
    
    #foci
    ax.plot3D(meridi_line[:,0], meridi_line[:,1], meridi_line[:,2], color = "blue")
    ax.plot3D(saggit_line[:,0], saggit_line[:,1], saggit_line[:,2], color = "blue")
    
    return plt, ax
    
def visualize_vectors(output, general_input, source_input, graphite_input,
                      crystal_input, detector_input):
    ## Do all of the steps as before, but also add the output rays
    origin = output['origin']
    direct = output['direction']
    m      = output['mask']
    
    #to avoid plotting too many rays, randomly cull rays until there are 1000
    if len(m[m]) > 1000:
        cutter = np.random.randint(0, len(m[m]), len(m))
        m[m] &= (cutter[m] < 1000)
    
    plt, ax = visualize_layout(general_input, source_input, graphite_input, 
                               crystal_input, detector_input)
    plt.title("X-Ray Raytracing Results")    
    
    ax.quiver(origin[m,0], origin[m,1], origin[m,2],
              direct[m,0], direct[m,1], direct[m,2],
              length = 1.0, arrow_length_ratio = 0.1 , color = "green",
              normalize = True)
    
    return plt, ax

def visualize_model(rays_history, rays_metadata, general_input, source_input,
                    graphite_input, crystal_input, detector_input):
    ## Do all of the steps as before, but also add the ray history
    # Rays that miss have their length extended to 10 and turn red
    # Rays that hit have accurate length and turn green
    plt, ax = visualize_layout(general_input, source_input, graphite_input, 
                               crystal_input, detector_input)    
    
    for ii in range(len(rays_history)):
        origin  = rays_history[ii]['origin']
        direct  = rays_history[ii]['direction']
        dist    = rays_metadata[ii]['distance']
        
        for jj in range(len(origin)):
                if dist[jj] == 0:
                    dist[jj] = 10
                    ax.quiver(origin[jj,0], origin[jj,1], origin[jj,2],
                              direct[jj,0], direct[jj,1], direct[jj,2],
                              length = dist[jj], arrow_length_ratio = 0.01, 
                              color = "red", normalize = True)
                else:
                    ax.quiver(origin[jj,0], origin[jj,1], origin[jj,2],
                              direct[jj,0], direct[jj,1], direct[jj,2],
                              length = dist[jj], arrow_length_ratio = 0.01, 
                              color = "green", normalize = True)
                    
    return plt, ax





    