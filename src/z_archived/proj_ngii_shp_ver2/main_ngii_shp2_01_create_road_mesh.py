"""
국토지리정보원 Shape Ver2 모델의 파일로부터 road mesh를 생성한다
"""
import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))
sys.path.append(current_path + '/../lib/common/')
sys.path.append(current_path + '/../lib_ngii_shp_ver2/')

from shp_common import *
import shapefile
import csv

import numpy as np
import matplotlib.pyplot as plt

# import lib_ngii_shp_ver2.shp_data_proc_funcs as proc_funcs
from lib_ngii_shp_ver2.shp_data_proc_funcs import proc_c3_vehicle_protection_safety
from lib_ngii_shp_ver2.shp_data_proc_lane import proc_lane
from lib_ngii_shp_ver2.shp_edit_funcs import UserInput, scr_zoom, create_mesh_creation_tool
from lib.mgeo.class_defs import *


def _append_list_of_points(list_to_append, shp_rec, relative_loc, origin=None):
    for i in range(len(shp_rec.points)):
        e = shp_rec.points[i][0]
        n = shp_rec.points[i][1]
        z = shp_rec.z[i]

        if relative_loc:
            e = e - origin[0]
            n = n - origin[1]
            z = z - origin[2]
        
        list_to_append.append([e,n,z])    


def main():
    input_path = '../../rsc/map_data/ngii_shp_ver2_191226_모라이_제공자료/서울_자율주행테스트베드/SEC01_서울자율주행테스트베드'
    output_path = '../../saved/'
    relative_loc = True

    # 절대 경로로 변경
    # input_path = os.path.normcase(input_path)
    input_path = os.path.join(current_path, input_path)
    input_path = os.path.normpath(input_path)   

    # 절대 경로로 변경
    # output_path = os.path.normcase(output_path)
    output_path = os.path.join(current_path, output_path)
    output_path = os.path.normpath(output_path)

    print('[INFO] input  path:', input_path)
    print('[INFO] output path:', output_path)

    # Get Map Information
    map_info = read_shp_files(input_path)

    # Disable a few keyboard shotcuts
    # NOTE: 다른 keymap 찾으려면 다음을 참고:
    # https://matplotlib.org/tutorials/introductory/customizing.html
    plt.rcParams['keymap.home'] = ''
    plt.rcParams['keymap.back'] = ''
    plt.rcParams['keymap.forward'] = ''
    plt.rcParams['keymap.pan'] = ''
    plt.rcParams['keymap.save'] = 'ctrl+s' # 원래 s, ctrl+s로 동작하는데 s만 사용하도록
    plt.rcParams['keymap.quit'] = ''
    plt.rcParams['keymap.quit_all'] = ''
    plt.rcParams['keymap.yscale'] = ''
    plt.rcParams['keymap.xscale'] = ''
    plt.rcParams['keymap.copy'] = 'ctrl+c' # alt+c 해제

    # Figure 생성
    fig_lane = plt.figure(1) # 차선 가장 바깥 선을 도시하는 figure는 1번으로 설정


    """
    Origin이 되는 Point를 찾는다
    Origin은 현재는 A1_NODE에서 검색되는 첫번째 포인트로한다
    """
    origin = get_first_shp_point(map_info['A1_NODE'])
    origin = np.array(origin)
    print('[INFO] Origin =', origin)


    """ 사용자 입력에 따른 콜백을 처리하기 위한 클래스 인스턴스 """
    ui = create_mesh_creation_tool()
    ui.pass_down(output_path)

    """ 안전 시설을 기준으로 만든다 (가드레일, 연석 등) """
    # link_lines = map_info['A2_LINK'] # TEMP
    # link_set_obj = proc_c3_vehicle_protection_safety(link_lines, origin)

    # surface_lines = map_info['B2_SURFACELINEMARK'] # TEMPORARY
    # line_set_cent = proc_lane(surface_lines, origin)

    safety_structures = map_info['C3_VEHICLEPROTECTIONSAFETY']
    line_set_obj = proc_c3_vehicle_protection_safety(safety_structures, origin)
    # test code to add surface lines to main lineset
    # for line in line_set_cent.lines:
    #     line_set_obj.append_line(line, create_new_key=True)
    # end test code
    node_set_obj = line_set_obj.create_node_set_for_all_lines()
    # node_set_obj = link_set_obj.create_node_set_for_all_lines()


    ui.set_geometry_obj(line_set_obj, node_set_obj)
    # ui.set_geometry_obj(link_set_obj, node_set_obj)
    ui.update_plot(plt.gcf(), plt.gca(), enable_node=ui.enable_node, draw=True)

        
    """ 사용자 입력에 따른 콜백 모음 """
    cid_click = fig_lane.canvas.mpl_connect('button_press_event', ui.on_click)
    cid_press = fig_lane.canvas.mpl_connect('key_press_event', ui.on_key)
    cid_scroll = fig_lane.canvas.mpl_connect('scroll_event', scr_zoom)

    # 지도 도시
    fig_lane.set_size_inches(12,12)
    # fig_lane.set_tight_layout(True)
    plt.show()
    print('[INFO] Ended successfully.')


if __name__ == u'__main__':
    main()