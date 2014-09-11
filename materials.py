#!/usr/bin/python

"""
Copyright 2014, University of Bremen & DFKI GmbH Robotics Innovation Center

This file is part of Phobos, a Blender Add-On to edit robot models.

Phobos is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License
as published by the Free Software Foundation, either version 3
of the License, or (at your option) any later version.

Phobos is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with Phobos.  If not, see <http://www.gnu.org/licenses/>.

File materials.py

Created on 7 Jan 2014

@author: Kai von Szadkowski
"""

import bpy

def makeMaterial(name, diffuse, specular, alpha, diffuse_intensity=1.0):
    """Returns a Blender material specified by the input parameters"""
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = diffuse
    mat.diffuse_shader = 'LAMBERT'
    mat.diffuse_intensity = diffuse_intensity
    mat.specular_color = specular
    mat.specular_shader = 'COOKTORR'
    mat.specular_intensity = 0.5
    mat.alpha = alpha
    mat.ambient = 1
    return mat

def createMARSMaterials():
    """Uses makeMaterial() to create a list of standard materials used in MARStools"""
    materials = bpy.data.materials.keys()
    #if not 'joint_sphere' in materials:
    #    makeMaterial('joint_sphere', (0, 1, 0), (1, 1, 1), 1)
    if not 'joint' in materials:
        makeMaterial('joint', (0, 0, 1), (1, 1, 1), 1)
    if not 'name' in materials:
        makeMaterial('name', (1, 1, 1), (1, 1, 1), 1)
    if not 'laserscanner' in materials:
        makeMaterial('laserscanner', (1.0, 0.08, 0.08), (1, 1, 1), 0.3)
    if not 'camera' in materials:
        makeMaterial('camera', (0.13, 0.4, 1), (1, 1, 1), 0.3, 0.8)
    if not 'tof-camera' in materials:
        makeMaterial('tof-camera', (0.44, 1, 0.735), (1, 1, 1), 0.3, 0.7)
    if not 'inertial' in materials:
        makeMaterial('inertial', (1, 0.18, 0), (1, 1, 1), 0.3, 0.7)
    if not 'sensor' in materials:
        makeMaterial('sensor', (0.8, 0.75, 0), (1, 1, 1), 0.3, 0.7)
    if not 'controller' in materials:
        makeMaterial('controller', (0.518, 0.364, 0.8), (1, 1, 1), 0.3, 0.7)
    if not 'indicator1' in materials:
        makeMaterial('indicator1', (1, 0, 0), (1, 1, 1), 1)
    if not 'indicator2' in materials:
        makeMaterial('indicator2', (0, 1, 0), (1, 1, 1), 1)
    if not 'indicator3' in materials:
        makeMaterial('indicator3', (0, 0, 1), (1, 1, 1), 1)
    if not 'indicator4' in materials:
        makeMaterial('indicator4', (1, 0, 1), (1, 1, 1), 1)
    if not 'indicator5' in materials:
        makeMaterial('indicator5', (1, 1, 0), (1, 1, 1), 1)
    if not 'indicator6' in materials:
        makeMaterial('indicator6', (0, 1, 1), (1, 1, 1), 1)
