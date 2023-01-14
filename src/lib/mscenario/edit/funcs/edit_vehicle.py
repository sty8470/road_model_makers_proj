import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../../')))

import numpy as np


def create_vehicle():    
    return 


def delete_vehicle():  
    return 


def update_vehicle(vehicle, field_name, old_val, new_val):    
    if field_name == 'DataID':
        vehicle.data_id = new_val
    elif field_name == 'isEgo':
        vehicle.is_ego = new_val
    elif field_name == 'isRandomCreation':
        vehicle.is_random_creation = new_val
    elif field_name == 'modelIndexList':
        vehicle.model_index_list = new_val
    elif field_name == 'pathGenerationMethod':
        vehicle.path_generation_method = new_val
    elif field_name == 'path':
        vehicle.path = new_val
    elif field_name == 'respawnDistance':
        vehicle.respawn_distance = new_val
    elif field_name == 'desiredVelocitiyMode':
        vehicle.desired_velocitiy_mode = new_val
    elif field_name == 'desiredVelocity':
        vehicle.desired_velocity = new_val
    elif field_name == 'pos':
        position = np.array(new_val)
        vehicle.init_position.position.x = position[0]
        vehicle.init_position.position.y = position[1]
        vehicle.init_position.position.z = position[2]
    elif field_name == 'rot':
        rotation = np.array(new_val)
        vehicle.init_position.rotation.pitch = rotation[0]
        vehicle.init_position.rotation.yaw = rotation[1]
        vehicle.init_position.rotation.roll = rotation[2]
    elif field_name == 'initLink':
        vehicle.init_position.init_link = new_val
    elif field_name == 'initLinkRatio':
        vehicle.init_position.init_link_ratio = new_val
    elif field_name == 'initPositionMode':
        vehicle.init_position.init_position_mode = new_val
    elif field_name == 'gear':
        vehicle.init_position.gear = new_val
    elif field_name == 'currentVelocity':
        vehicle.current_velocity = new_val
