'''
Phobos - a Blender Add-On to work with MARS robot models

File joints.py

Created on 7 Jan 2014

@author: Kai von Szadkowski

Copy this add-on to your Blender add-on folder and activate it
in your preferences to gain instant (virtual) world domination.
You may use the provided install shell script.
'''

import bpy
from bpy.types import Operator
from bpy.props import FloatProperty, EnumProperty
import math
import mathutils
import warnings
from . import defs

def register():
    print("Registering joints...")

def unregister():
    print("Unregistering joints...")

def deriveJointType(joint, adjust = False):
    ''' Derives the type of the joint defined by the armature object 'joint' based on the constraints defined in the joint.
    The parameter 'adjust' decides whether or not the type of the joint is adjusted after detecting (without checking whether
    the property "type" was previously defined in the armature or not).'''
    jtype = 'floating' # 'universal' in MARS nomenclature
    cloc = None
    crot = None
    limrot = None
    # we pick the first bone in the armature as there is only one
    for c in joint.pose.bones[0].constraints:
        if c.type == 'LIMIT_LOCATION':
            cloc = [c.use_min_x and c.min_x == c.max_x,
                    c.use_min_y and c.min_y == c.max_y,
                    c.use_min_z and c.min_z == c.max_z]
        elif c.type == 'LIMIT_ROTATION':
            limrot = c
            crot = [c.use_limit_x and (c.min_x != 0 or c.max_x != 0),
                    c.use_limit_y and (c.min_y != 0 or c.max_y != 0),
                    c.use_limit_z and (c.min_z != 0 or c.max_z != 0)]
    ncloc = sum(cloc) if cloc else None
    ncrot = sum((limrot.use_limit_x, limrot.use_limit_y, limrot.use_limit_z,)) if limrot else None
    if cloc: # = if there is any constraint at all, as all joints but floating ones have translation limits
        if ncloc == 3: # fixed or revolute
            if ncrot == 3:
                if sum(crot) > 0:
                    jtype = 'revolute'
                else:
                    jtype = 'fixed'
            elif ncrot == 2:
                jtype = 'continuous'
        elif ncloc == 2:
            jtype = 'prismatic'
        elif ncloc == 1:
            jtype = 'planar'
    if 'jointType' in joint and joint['jointType'] != jtype:
        warnings.warn("Type of joint "+joint.name+" does not match constraints!", Warning) #TODO: this goes to sys.stderr, i.e. nirvana
        if(adjust):
            joint['jointType'] = jtype
            print("Changed type of joint'" + joint.name, 'to', jtype + "'.")
    return jtype, crot

def getJointConstraints(joint):
    ''' Returns the constraints defined in the joint as a combination of two lists, 'axis' and 'limits'.'''
    jt, crot = deriveJointType(joint, adjust = True)
    axis = None
    limits = None
    if jt not in ['floating', 'fixed']:
        if jt in ['revolute', 'continuous'] and crot:
            c = getJointConstraint(joint, 'LIMIT_ROTATION')
            #axis = (joint.matrix_local * -bpy.data.armatures[joint.name].bones[0].vector).normalized() #we cannot use joint for both as the first is a Blender 'Object', the second an 'Armature'
            #axis = (joint.matrix_local * -joint.data.bones[0].vector).normalized() #joint.data accesses the armature, thus the armature's name is not important anymore
            axis = joint.data.bones[0].vector.normalized() #vector along axis of bone (Y axis of pose bone) in object space
            if crot[0]:
                limits = (c.min_x, c.max_x)
            elif crot[1]:
                limits = (c.min_y, c.max_y)
            elif crot[2]:
                limits = (c.min_z, c.max_z)
        else:
            c = getJointConstraint(joint, 'LIMIT_LOCATION')
            if not c:
                raise Exception("JointTypeError: under-defined constraints in joint ("+joint.name+").")
            freeloc = [c.use_min_x and c.use_max_x and c.min_x == c.max_x,
                    c.use_min_y and c.use_max_y and c.min_y == c.max_y,
                    c.use_min_z and c.use_max_z and c.min_z == c.max_z]
            if jt == 'prismatic':
                if sum(freeloc) == 2:
                    #axis = mathutils.Vector([int(not i) for i in freeloc])
                    axis = joint.data.bones[0].vector.normalized() #vector along axis of bone (Y axis of pose bone) in obect space
                    if freeloc[0]:
                        limits = (c.min_x, c.max_x)
                    elif freeloc[1]:
                        limits = (c.min_y, c.max_y)
                    elif freeloc[2]:
                        limits = (c.min_z, c.max_z)
                else:
                    raise Exception("JointTypeError: under-defined constraints in joint ("+joint.name+").")
            elif jt == 'planar':
                if sum(freeloc) == 1:
                    axis = mathutils.Vector([int(i) for i in freeloc])
                    if axis[0]:
                        limits = (c.min_y, c.max_y, c.min_z, c.max_z)
                    elif axis[1]:
                        limits = (c.min_x, c.max_x, c.min_z, c.max_z)
                    elif axis[2]:
                        limits = (c.min_x, c.max_x, c.min_y, c.max_y)
                else:
                    raise Exception("JointTypeError: under-defined constraints in joint ("+joint.name+").")
    return axis, limits

def getJointConstraint(joint, ctype):
    con = None
    for c in joint.pose.bones[0].constraints:
        if c.type == ctype:
            con = c
    return con


class DefineJointConstraintsOperator(Operator):
    """DefineJointConstraintsOperator"""
    bl_idname = "object.define_joint_constraints"
    bl_label = "Adds Bone Constraints to the joint (link)"
    bl_options = {'REGISTER', 'UNDO'}

    joint_type = EnumProperty(
        name = 'joint_type',
        default = 'revolute',
        description = "type of the joint",
        items = defs.jointtypes)

    lower = FloatProperty(
        name = "lower",
        default = 0.0,
        description = "lower constraint of the joint")

    upper = FloatProperty(
        name = "upper",
        default = 0.0,
        description = "upper constraint of the joint")

    maxeffort = FloatProperty(
        name = "max effort (N or Nm)",
        default = 0.0,
        description = "maximum effort of the joint")

    maxvelocity = FloatProperty(
        name = "max velocity (m/s or rad/s",
        default = 0.0,
        description = "maximum velocity of the joint")

    def execute(self, context):
        lower = math.radians(self.lower)
        upper = math.radians(self.upper)
        for link in bpy.context.selected_objects:
            bpy.context.scene.objects.active = link
            bpy.ops.object.mode_set(mode='POSE')
            for c in link.pose.bones[0].constraints:
                link.pose.bones[0].constraints.remove(c)
            if link.MARStype == 'link':
                if self.joint_type == 'revolute':
                    # fix location
                    bpy.ops.pose.constraint_add(type='LIMIT_LOCATION')
                    cloc = getJointConstraint(link, 'LIMIT_LOCATION')
                    cloc.use_min_x = True
                    cloc.use_min_y = True
                    cloc.use_min_z = True
                    cloc.use_max_x = True
                    cloc.use_max_y = True
                    cloc.use_max_z = True
                    cloc.owner_space = 'LOCAL'
                    # fix rotation x, z and limit y
                    bpy.ops.pose.constraint_add(type='LIMIT_ROTATION')
                    crot = getJointConstraint(link, 'LIMIT_ROTATION')
                    crot.use_limit_x = True
                    crot.min_x = 0
                    crot.max_x = 0
                    crot.use_limit_y = True
                    crot.min_y = lower
                    crot.max_y = upper
                    crot.use_limit_z = True
                    crot.min_z = 0
                    crot.max_z = 0
                    crot.owner_space = 'LOCAL'
                elif self.joint_type == 'continuous':
                    # fix location
                    bpy.ops.pose.constraint_add(type='LIMIT_LOCATION')
                    cloc = getJointConstraint(link, 'LIMIT_LOCATION')
                    cloc.use_min_x = True
                    cloc.use_min_y = True
                    cloc.use_min_z = True
                    cloc.use_max_x = True
                    cloc.use_max_y = True
                    cloc.use_max_z = True
                    cloc.owner_space = 'LOCAL'
                    # fix rotation x, z
                    bpy.ops.pose.constraint_add(type='LIMIT_ROTATION')
                    crot = getJointConstraint(link, 'LIMIT_ROTATION')
                    crot.use_limit_x = True
                    crot.min_x = 0
                    crot.max_x = 0
                    crot.use_limit_z = True
                    crot.min_z = 0
                    crot.max_z = 0
                    crot.owner_space = 'LOCAL'
                elif self.joint_type == 'prismatic':
                    # fix location except for y axis
                    bpy.ops.pose.constraint_add(type='LIMIT_LOCATION')
                    cloc = getJointConstraint(link, 'LIMIT_LOCATION')
                    cloc.use_min_x = True
                    cloc.use_min_y = True
                    cloc.use_min_z = True
                    cloc.use_max_x = True
                    cloc.use_max_y = True
                    cloc.use_max_z = True
                    if self.lower == self.upper:
                        cloc.use_min_y = False
                        cloc.use_max_y = False
                    else:
                        cloc.min_y = self.lower
                        cloc.max_y = self.upper
                    cloc.owner_space = 'LOCAL'
                    # fix rotation
                    bpy.ops.pose.constraint_add(type='LIMIT_ROTATION')
                    crot = getJointConstraint(link, 'LIMIT_ROTATION')
                    crot.use_limit_x = True
                    crot.min_x = 0
                    crot.max_x = 0
                    crot.use_limit_y = True
                    crot.min_y = 0
                    crot.max_y = 0
                    crot.use_limit_z = True
                    crot.min_z = 0
                    crot.max_z = 0
                    crot.owner_space = 'LOCAL'
                elif self.joint_type == 'fixed':
                    # fix location
                    bpy.ops.pose.constraint_add(type='LIMIT_LOCATION')
                    cloc = getJointConstraint(link, 'LIMIT_LOCATION')
                    cloc.use_min_x = True
                    cloc.use_min_y = True
                    cloc.use_min_z = True
                    cloc.use_max_x = True
                    cloc.use_max_y = True
                    cloc.use_max_z = True
                    cloc.owner_space = 'LOCAL'
                    # fix rotation
                    bpy.ops.pose.constraint_add(type='LIMIT_ROTATION')
                    crot = getJointConstraint(link, 'LIMIT_ROTATION')
                    crot.use_limit_x = True
                    crot.min_x = 0
                    crot.max_x = 0
                    crot.use_limit_y = True
                    crot.min_y = 0
                    crot.max_y = 0
                    crot.use_limit_z = True
                    crot.min_z = 0
                    crot.max_z = 0
                    crot.owner_space = 'LOCAL'
                elif self.joint_type == 'floating':
                    # 6DOF
                    pass
                elif self.joint_type == 'planar':
                    # fix location
                    bpy.ops.pose.constraint_add(type='LIMIT_LOCATION')
                    cloc = getJointConstraint(link, 'LIMIT_LOCATION')
                    cloc.use_min_y = True
                    cloc.use_max_y = True
                    cloc.owner_space = 'LOCAL'
                    # fix rotation
                    bpy.ops.pose.constraint_add(type='LIMIT_ROTATION')
                    crot = getJointConstraint(link, 'LIMIT_ROTATION')
                    crot.use_limit_x = True
                    crot.min_x = 0
                    crot.max_x = 0
                    crot.use_limit_y = True
                    crot.min_y = 0
                    crot.max_y = 0
                    crot.use_limit_z = True
                    crot.min_z = 0
                    crot.max_z = 0
                    crot.owner_space = 'LOCAL'
                else:
                    print("Error: Unknown joint type")
                link['jointType'] = self.joint_type
                if self.joint_type != 'fixed':
                    link['joint/maxeffort'] = self.maxeffort
                    link['joint/maxvelocity'] = self.maxvelocity
        return{'FINISHED'}

class AttachMotorOperator(Operator):
    """AttachMotorOperator"""
    bl_idname = "object.attach_motor"
    bl_label = "Attaches motor values to selected joints"
    bl_options = {'REGISTER', 'UNDO'}

    P = FloatProperty(
        name = "P",
        default = 0.0,
        description = "P-value")

    I = FloatProperty(
        name = "I",
        default = 0.0,
        description = "I-value")

    D = FloatProperty(
        name = "D",
        default = 0.0,
        description = "D-value")

    vmax = FloatProperty(
        name = "maximum velocity [rpm]",
        default = 1.0,
        description = "maximum turning velocity of the motor")

    taumax = FloatProperty(
        name = "maximum torque [Nm]",
        default = 0.1,
        description = "maximum torque a motor can apply")

    motortype = EnumProperty(
        name = 'motor_type',
        default = 'servo',
        description = "type of the motor",
        items = defs.motortypes)

    def execute(self, context):
        for joint in bpy.context.selected_objects:
            if joint.MARStype == "link":
                #TODO: these keys have to be adapted
                joint['motor/p'] = self.P
                joint['motor/i'] = self.I
                joint['motor/d'] = self.D
                joint['motor/motorMaxSpeed'] = self.vmax*2*math.pi
                joint['motor/motorMaxForce'] = self.taumax
                joint['type'] = 1 if self.motortype == 'servo' else 2
        return{'FINISHED'}


class Store_Pose_Operator(bpy.types.Operator):
	"""
	"""
	'''
	'''
	bl_idname = 'object.mt_store_armas_pose'
	bl_label = 'Store Armature Poses'
	bl_description = 'Store the pose of all armatures in the scene.'
	bl_options = {'REGISTER'}
	
	def execute(self, context):
		print('actions:')
		for action in bpy.data.actions:
			print(action.name)
		print()
		objects = bpy.context.scene.objects
		counter = 1
		store_arma = None
		for obj in objects:
			if obj.type == 'ARMATURE':
				arma = obj
				
				arma.select = True
				bpy.context.scene.objects.active = arma
				
				bpy.ops.object.mode_set(mode='POSE')
				arma_name = arma.name
				bpy.ops.poselib.new()
				poselib = bpy.data.actions['PoseLib']
				poselib.name = 'poselib_' + arma_name
				bpy.ops.poselib.pose_add(name='pose_' + arma_name + '_0')
				
		return {'FINISHED'}
		

class Load_Pose_Operator(bpy.types.Operator):
    """
    """
    '''
    '''
    bl_idname = 'object.mt_load_armas_pose'
    bl_label = 'Load Armature Poses'
    bl_description = 'Load the pose of all armatures in the scene.'
    bl_options = {'REGISTER'}
	
    def execute(self, context):
        objects = bpy.context.scene.objects
        armature_objects = []
        counter = 1
        for obj in objects:
            if obj.type == 'ARMATURE':
                arma = obj
                arma_name = arma.name
                print(arma_name)
                bpy.ops.object.mode_set(mode='OBJECT')
                bpy.ops.object.select_all(action='DESELECT')
                arma.select = True
                bpy.context.scene.objects.active = arma
                
                bpy.ops.object.mode_set(mode='POSE')
                
                poselib = bpy.data.actions['poselib_' + arma.name]
                if poselib:
                    print('here is a lib!')
                    poses = poselib.pose_markers
                    wanted_pose = None
                    #print('pose_' + arma_name + '_0')
                    for pose in poses:
                        print('\t', pose.name)
                        if pose.name == 'pose_' + arma_name + '_0':
                            wanted_pose = pose
                            break
                    if wanted_pose:
                        poselib.pose_markers.active = wanted_pose
                        #bpy.ops.object.mode_set(mode='POSE')
                        
                        print('area:', bpy.context.area.type)
                        print('blend_data:')
                        for object in bpy.context.blend_data.objects:
                            print('\t', object.name)
                        print('mode:', bpy.context.mode)
                        print('region:', bpy.context.region.type)
                        #print('window:', bpy.context.window.name)
                        
                        bpy.ops.poselib.apply_pose()
                    else:
                        print('no pose')
                        # TODO
                        pass
                else:
                    print('no lib')
                    # TODO
                    pass
        print('ok')
        return {'FINISHED'}
