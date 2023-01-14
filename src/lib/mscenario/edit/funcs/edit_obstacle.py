import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../../')))

import numpy as np


def create_obstacle():    
    return 


def delete_obstacle():  
    return 


def update_obstacle(obstacle, field_name, old_val, new_val):    
    if field_name == 'index':
        obstacle.index = new_val
    elif field_name == 'UNIQUEID':
        obstacle.unique_id = new_val
    elif field_name == 'm_eobstacleObjType':
        obstacle.obstacle_obj_type = new_val  
    elif field_name == 'pos':
        position = np.array(new_val)
        obstacle.init_transform.position.x = position[0]
        obstacle.init_transform.position.y = position[1]
        obstacle.init_transform.position.z = position[2]
    elif field_name == 'rot':
        rotation = np.array(new_val)
        obstacle.init_transform.rotation.pitch = rotation[0]
        obstacle.init_transform.rotation.yaw = rotation[1]
        obstacle.init_transform.rotation.roll = rotation[2]   
    elif field_name == 'scale':
        scale = np.array(new_val)
        obstacle.init_transform.scale.x = scale[0]
        obstacle.init_transform.scale.y = scale[1]
        obstacle.init_transform.scale.z = scale[2] 