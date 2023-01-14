import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../../')))

import numpy as np


def create_pedestrian():    
    return 


def delete_pedestrian():  
    return 


def update_pedestrian(pedestrian, field_name, old_val, new_val):    
    if field_name == 'index':
        pedestrian.index = new_val
    elif field_name == 'UNIQUEID':
        pedestrian.unique_id = new_val
    elif field_name == 'm_eobstacleObjType':
        pedestrian.obstacle_obj_type = new_val
    elif field_name == 'pos':
        position = np.array(new_val)
        pedestrian.init_position.position.x = position[0]
        pedestrian.init_position.position.y = position[1]
        pedestrian.init_position.position.z = position[2]
    elif field_name == 'rot':
        rotation = np.array(new_val)
        pedestrian.init_position.rotation.pitch = rotation[0]
        pedestrian.init_position.rotation.yaw = rotation[1]
        pedestrian.init_position.rotation.roll = rotation[2]      
    elif field_name == 'activeDistance':
        pedestrian.active_distance = new_val
    elif field_name == 'speed':
        pedestrian.speed = new_val
    elif field_name == 'active':
        pedestrian.active = new_val
    elif field_name == 'loop':
        pedestrian.loop = new_val
    elif field_name == 'movingDistance':
        pedestrian.moving_distance = new_val
    elif field_name == 'movingDistanceAmount':
        pedestrian.moving_distance_amount = new_val