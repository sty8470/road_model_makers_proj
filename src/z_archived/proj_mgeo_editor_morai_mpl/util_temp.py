import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))

import numpy as np
import matplotlib.pyplot as plt
from tkinter import filedialog
import json

# MGeo Module
from lib.mgeo.class_defs import *
from save_load import *
from mesh_gen import * 
from utils import error_fix, file_io, lane_change_link_creation
from mesh_gen.generate_mesh import make_road, write_obj
from edit.funcs import edit_node, edit_link, edit_mgeo_planner_map


# NGII Library
from lib_ngii_shp1 import ngii_shp1_to_mgeo
from lib_ngii_shp_ver2 import ngii_shp2_to_mgeo, morai_sim_build_data_exporter
from lib.lib_42dot import hdmap_42dot_importer

from lib.common.coord_trans_srs import get_tranform_UTM52N_to_TMMid, get_tranform_UTMK_to_TMMid


def import_pangyo_aict_and_ngii_shp2():
    """
    판교 NGII SHP2 데이터를 읽어와서 UTM52N -> TM중부 좌표로 변환하여 새로 저장한다.
    
    1) 우선은 고도부터 바꾼다. UTM52N은 Ellipsoid Height이다. 이를 Orthometric Height로 변환한다. (UTM-K 데이터의 z값을 가져온다)
    2) UTM52N -> TM중부 좌표계 변환 클래스를 활용한다
    3) 새로운 MGeo 파일로 저장한다
    """
    root_dir = file_io.get_proj_root_dir()
    aict_path = os.path.normpath(os.path.join(root_dir, 'rsc/map_data/aict_shp_pangyo/1st2ndIntg_TM_Mid'))
    
    ngii_utm52n_path = os.path.normpath(os.path.join(root_dir, 'rsc/map_data/ngii_shp2_Seongnam_Pangyo/SEC01_UTM52N_ElipsoidHeight'))
    ngii_utmk_path = os.path.normpath(os.path.join(root_dir, 'rsc/map_data/ngii_shp2_Seongnam_Pangyo/SEC01_UTMK_OrthometricHeight'))

    aict = ngii_shp1_to_mgeo.import_all_data(aict_path, origin_node_id='206I10440403')        
    
    # 우선 UTM52N이 Ellipsoid height인데, 이를 UTM52N의 orthometric height로 변환한다.
    # 이는 UTMK Orthometric height 데이터를 그냥 이용하는 것으로 한다.

    ngii_utm52n = ngii_shp2_to_mgeo.import_all_data(ngii_utm52n_path, origin_node_id='A119AS305498')
    ngii_utmk = ngii_shp2_to_mgeo.import_all_data(ngii_utmk_path, origin_node_id='A119AS305498')
    
    # 우선은 origin 변경
    src_origin = ngii_utm52n.get_origin()
    src_origin[2] = ngii_utmk.get_origin()[2]
    ngii_utm52n.set_origin(src_origin)

    # node부터 변경
    for idx, node in ngii_utm52n.node_set.nodes.items():
        node.point[2] = ngii_utmk.node_set.nodes[idx].point[2]

    # link 변경
    for idx, link in ngii_utm52n.link_set.lines.items():
        for i in range(len(link.points)):
            link.points[i][2] = ngii_utmk.link_set.lines[idx].points[i][2]

    # 이제 UTM52N인 데이터를 
    ngii = ngii_utm52n 


    """ """
    trans = get_tranform_UTM52N_to_TMMid()
    # trans = get_tranform_UTMK_to_TMMid() # 이 transform은 동작하지 않는다 (QGIS에서도 마찬가지)


    """여기는 좌표 변환 제대로 되는지 확인용""" 
    aict_origin_node_global = aict.node_set.nodes['206I10440403'].point + aict.get_origin() 
    ngii_origin_node_global = ngii.node_set.nodes['A119AS305498'].point + ngii.get_origin()


    """여기가 ngii 데이터의 변환용"""
    src_origin = ngii.get_origin()
    dst_origin = trans.TransformPoint(src_origin[0], src_origin[1], src_origin[2])
    dst_origin = np.array(dst_origin)
    ngii.set_origin(dst_origin)        
    

    for idx, node in ngii.node_set.nodes.items():
        utm52n_global = node.point + src_origin
        tm_mid_global = trans.TransformPoint(utm52n_global[0], utm52n_global[1], utm52n_global[2])
        node.point = np.array(tm_mid_global) - dst_origin

    # 반대로 여기가 문제였음
    for idx, link in ngii.link_set.lines.items():
        for i in range(len(link.points)):
            utm52n_global = link.points[i] + src_origin
            tm_mid_global = trans.TransformPoint(utm52n_global[0], utm52n_global[1], utm52n_global[2])   
            link.points[i] = np.array(tm_mid_global) - dst_origin
        
        # 왜 아래와 같이 했을땐 동작이 안 되지???    
        # points = list()
        # for point in link.points:
        #     utm52n_global = point + src_origin
        #     tm_mid_global = trans.TransformPoint(utm52n_global[0], utm52n_global[1], utm52n_global[2])           
        #     points.append(tm_mid_global)
        # link.point = np.array(points) - dst_origin

    #     # 이 링크의 시작,끝 위치에 맞게 from_node, to_node 도 바꿔버린다
    #     # NOTE: 이해안됨!!! link는 좌표변환이 잘 되는 것 같은데, node는 이렇게 해주지 않으면 값이 맞지가 않는다
    #     link.from_node.point = link.points[0]
    #     link.to_node.point = link.points[-1]
    # ngii.link_set = LineSet()


    root_dir = file_io.get_proj_root_dir()
    init_save_path = os.path.join(root_dir, 'saved/') 
    init_save_path = os.path.normpath(init_save_path)
    print('[TRACE] init_save_path: {}'.format(init_save_path))
    
    save_path = filedialog.askdirectory(
        initialdir=init_save_path, 
        title='Select a folder to save MGeo data into')
    if save_path == '' or save_path == None:
        print('[ERROR] invalid save_path (your input: {})'.format(save_path))
        return

    ngii.to_json(save_path)
    print("[INFO] MGeo data successfully saved into: {}".format(save_path))


def create_new_aggregate_data():
    root_dir = file_io.get_proj_root_dir()

    aict_path = os.path.normpath(os.path.join(root_dir, 'rsc/map_data/aict_shp_pangyo/1st2ndIntg_TM_Mid'))
    print('[INFO] import NGII SHP1 from: {}'.format(aict_path))
    aict = ngii_shp1_to_mgeo.import_all_data(aict_path, origin_node_id='206I10440403')

    prev_agg_path = os.path.normpath(os.path.join(root_dir, 'saved/판교 NGII SHP2 데이터 TMMid로 변경/200914_PM0200_AICT_NGII통합_시뮬레이터로드용'))     
    print('[INFO] load mgeo from: {}'.format(prev_agg_path))
    prev_agg = MGeo.create_instance_from_json(prev_agg_path)

    ngii_path = os.path.normpath(os.path.join(root_dir, 'saved/판교 NGII SHP2 데이터 TMMid로 변경/200915_PM0325_NGII 데이터 TMMid로 변경 (2)'))     
    print('[INFO] load mgeo from: {}'.format(ngii_path))
    ngii = MGeo.create_instance_from_json(ngii_path)

    # node를 우선 검색
    for idx, node in prev_agg.node_set.nodes.items():
        if idx in aict.node_set.nodes.keys():
            # 이렇게 양쪽에 모두 있는 노드라면, 새로운 셋으로 추가되어야 한다.
            # 이 때 aict에 있는 node를 추가해야 한다.
            node_to_add = aict.node_set.nodes[idx]
            ngii.node_set.append_node(node_to_add)

    # link를 그 다음 검색
    for idx, link in prev_agg.link_set.lines.items():
        if idx in aict.link_set.lines.keys():
            # 이렇게 양쪽에 모두 있는 링크라면, 새로운 셋으로 추가되어야 한다.
            
            # # 이 때 lane ch link 정보가 있고, 이게 LN으로 시작되면 이를 없앤다
            # if link.lane_ch_link_left is not None:
            #     if 'LN' in link.lane_ch_link_left.idx:
            #         link.lane_ch_link_left = None

            # if link.lane_ch_link_right is not None:
            #     if 'LN' in link.lane_ch_link_right.idx:
            #         link.lane_ch_link_right = None

            # 이 때 좌표는 aict 데이터에서 가져온다
            link.points = aict.link_set.lines[idx].points
            ngii.link_set.append_line(link)
        
        if 'LN' in idx:
            if not link.is_it_for_lane_change():
                # LN으로 시작하는 링크는 새로 추가한 링크이므로, 추가가 되어야 한다.
                # 단, 이 링크의 포인트는 수정될 필요가 있는데,
                print('link: {} len: {}'.format(idx, len(link.points)))
                
                from_node_id = link.from_node.idx
                to_node_id = link.to_node.idx
                
                link.points = np.array([
                    ngii.node_set.nodes[from_node_id].point, 
                    ngii.node_set.nodes[to_node_id].point])

                ngii.link_set.append_line(link)


    root_dir = file_io.get_proj_root_dir()
    init_save_path = os.path.join(root_dir, 'saved/') 
    init_save_path = os.path.normpath(init_save_path)
    print('[TRACE] init_save_path: {}'.format(init_save_path))
    
    save_path = filedialog.askdirectory(
        initialdir=init_save_path, 
        title='Select a folder to save MGeo data into')
    if save_path == '' or save_path == None:
        print('[ERROR] invalid save_path (your input: {})'.format(save_path))
        return
        
    # 다시 이 데이터를 저장
    ngii.to_json(save_path)
    print("[INFO] MGeo data successfully saved into: {}".format(save_path))


def change_origin_to_pangyo_map():
    """판교 RoadMesh는 AICT 데이터 기준 (TM중부) 206I10440403 인 노드를 기준으로 되어있고, 해당 노드의 좌표계는 아래와 같다.
    [209402.0923992687, 533433.0495021925, 39.684636742713245]
    따라서, 해당 좌표를 기준으로 데이터 전체를 이동시켜야한다
    """

    root_dir = file_io.get_proj_root_dir()

    ngii_path = os.path.normpath(os.path.join(root_dir, 'saved/판교 NGII SHP2 데이터 TMMid로 변경/200915_AM0800_NGII, AICT 데이터 TM중부에서 합쳐본것 (5)'))     
    print('[INFO] load mgeo from: {}'.format(ngii_path))
    ngii = MGeo.create_instance_from_json(ngii_path)


    # 이 데이터의 원점을 변경해준다.
    new_origin = np.array([209402.0923992687, 533433.0495021925, 39.684636742713245])
    edit_mgeo_planner_map.change_origin(
        ngii, new_origin, retain_global_position=True)

    # 이 데이터를 다시 저장한다.
    root_dir = file_io.get_proj_root_dir()
    init_save_path = os.path.join(root_dir, 'saved/') 
    init_save_path = os.path.normpath(init_save_path)
    print('[TRACE] init_save_path: {}'.format(init_save_path))
    
    save_path = filedialog.askdirectory(
        initialdir=init_save_path, 
        title='Select a folder to save MGeo data into')
    if save_path == '' or save_path == None:
        print('[ERROR] invalid save_path (your input: {})'.format(save_path))
        return
        
    ngii.to_json(save_path)
    print("[INFO] MGeo data successfully saved into: {}".format(save_path))
    


if __name__ == '__main__':
    # import_pangyo_aict_and_ngii_shp2()

    create_new_aggregate_data()

    # change_origin_to_pangyo_map()