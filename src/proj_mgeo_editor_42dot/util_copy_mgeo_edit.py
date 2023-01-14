import os 
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))

from lib.common.logger import Logger

import json

from lib.mgeo.class_defs.mgeo import MGeo


"""
전체 작업 순서를 어떻게 해야할까
1) 새로 받은 데이터로 mgeo 데이터를 우선 다시 생성

2) overlapped node를 fix하여 저장
   => 전체 MGeo = Dst

3) 기존 mgeo 파일을 불러와서, junction id를 변경하고, 새로 저장한다
   => 각각의 src 1~6

4) dst => src로 다음을 옮긴다 
   
   [Node]
   - node에 있는 junction 정보
   
   [Link]
   - from_node, to_node
   - points
   - geometry point

   - 만일 src쪽에서 삭제한 link가 있다면??
     이는 알아차리기 어렵다. 왜냐하면 src는 dst 맵의 subset이기 때문에,
     애초에 src에는 존재하지만 dst에는 존재하지 않는 데이터가 굉장히 많기 때문.

   - src에는 존재하고, dst에는 존재하지 않는 데이터
     >> 새로 생성한 노드 또는 링크이다.
     >> 그대로 복사하고, 이를 기록해준다
     >> mgeo editor로 어디에 그러한 데이터가 있는지 확인해봐야 한다. 
"""


def util_copy_signal_coordinate():
    """dst에 있는 signal의 좌표를 src에 있는 같은 signal의 좌표로 대체한다"""

    src_path = '../../saved/42dot_yangjae_maps/yangjae_v2p7_0_all_data'
    dst_path = '../../saved/42dot_yangjae_maps/yangjae_v2p7_6_citizenforeststn_intscn'

    src_path = os.path.normpath(os.path.join(current_path, src_path))
    dst_path = os.path.normpath(os.path.join(current_path, dst_path))
    
    src_mgeo = MGeo.create_instance_from_json(src_path)
    dst_mgeo = MGeo.create_instance_from_json(dst_path)

    for idx, dst in dst_mgeo.sign_set.signals.items():
        src = src_mgeo.sign_set.signals[idx]
        dst.point = src.point
        Logger.log_info('TS idx: {}'.format(idx))

    for idx, dst in dst_mgeo.light_set.signals.items():
        src = src_mgeo.light_set.signals[idx]
        dst.point = src.point
        Logger.log_info('TL idx: {}'.format(idx))

    dst_mgeo.to_json(dst_path)



def util_copy_node_attribute():
    Logger.log_info('util_copy_node_attribute called.')
    src_path = '../../saved/42dot_yangjae_maps/yangjae_v2p7_1_yangjae_station'
    dst_path = '../../saved/42dot_yangjae_maps/yangjae_v2p7_0_all_data'

    src_path = os.path.normpath(os.path.join(current_path, src_path))
    dst_path = os.path.normpath(os.path.join(current_path, dst_path))

    src_mgeo = MGeo.create_instance_from_json(src_path)
    dst_mgeo = MGeo.create_instance_from_json(dst_path)

    # src가 subset이므로, src로 iterate 해야함
    for idx, src in src_mgeo.node_set.nodes.items():
        dst = dst_mgeo.node_set.nodes[idx]
        dst.junctions = src.junctions

    # dst_mgeo 파일에 저장
    dst_mgeo.to_json(dst_path)

    Logger.log_info('util_copy_node_attribute done OK.')


def util_copy_link_attribute_geometry():
    Logger.log_info('util_copy_link_attribute_geometry called.')
    src_path = '../../saved/42dot_yangjae_maps/yangjae_v2p7_6_citizenforeststn_intscn'
    dst_path = '../../saved/42dot_yangjae_maps/yangjae_v2p7_0_all_data'

    src_path = os.path.normpath(os.path.join(current_path, src_path))
    dst_path = os.path.normpath(os.path.join(current_path, dst_path))

    src_mgeo = MGeo.create_instance_from_json(src_path)
    dst_mgeo = MGeo.create_instance_from_json(dst_path)

    # src가 subset이므로, src로 iterate 해야함
    for idx, src in src_mgeo.link_set.lines.items():
        dst = dst_mgeo.link_set.lines[idx]
        dst.geometry = src.geometry

    # dst_mgeo 파일에 저장
    dst_mgeo.to_json(dst_path)

    Logger.log_info('util_copy_link_attribute_geometry done OK.')


def util_copy_link_attribute_complex():
    Logger.log_info('util_copy_link_attribute_complex called.')
    src_path = '../../saved/42dot_yangjae_maps/yangjae_v2p7_1_yangjae_station'
    dst_path = '../../saved/42dot_yangjae_maps/yangjae_v2p7_0_all_data'

    src_path = os.path.normpath(os.path.join(current_path, src_path))
    dst_path = os.path.normpath(os.path.join(current_path, dst_path))

    src_mgeo = MGeo.create_instance_from_json(src_path)
    dst_mgeo = MGeo.create_instance_from_json(dst_path)

    # src가 subset이므로, src로 iterate 해야함
    for idx, src in src_mgeo.link_set.lines.items():
        # src에서 생성한 경우, 없을 수도 있다. 
        if idx in dst_mgeo.link_set.lines.keys():
            
            dst = dst_mgeo.link_set.lines[idx]
            
            # 복사해야 할 값
            dst.lane_ch_link_left = src.lane_ch_link_left
            dst.lane_ch_link_right = src.lane_ch_link_right
            dst.road_id = src.road_id
            dst.ego_lane = src.ego_lane
            dst.geometry = src.geometry
        else:
            Logger.log_info('Maybe a newly created link: (not in dst_mgeo) id: {}'.format(idx))

    # dst_mgeo 파일에 저장
    dst_mgeo.to_json(dst_path)

    Logger.log_info('util_copy_link_attribute_complex done OK.')


def util_copy_link_type():
    Logger.log_info('util_copy_link_type called.')
    src_path = '../../saved/rename_link_type'
    dst_path = '../../saved/saved_pangyo_ALL_rename'

    src_path = os.path.normpath(os.path.join(current_path, src_path))
    dst_path = os.path.normpath(os.path.join(current_path, dst_path))

    src_mgeo = MGeo.create_instance_from_json(src_path)
    dst_mgeo = MGeo.create_instance_from_json(dst_path)

    # src가 subset이므로, src로 iterate 해야함
    for idx, src in src_mgeo.link_set.lines.items():
        if idx in dst_mgeo.link_set.lines.keys():
            dst = dst_mgeo.link_set.lines[idx]
            dst.link_type = src.link_type
        else:
            Logger.log_info('Maybe a newly created link: (not in dst_mgeo) id: {}'.format(idx))
    # dst_mgeo 파일에 저장
    dst_mgeo.to_json(dst_path)

    Logger.log_info('util_copy_link_type done OK.')


if __name__ == '__main__':
    util_copy_link_type()
    # util_copy_node_attribute()
    # util_copy_link_attribute_geometry()
    # util_copy_link_attribute_complex()