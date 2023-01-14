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
from tkinter import filedialog

from lib_ngii_shp_ver2.shp_edit_funcs import UserInput, scr_zoom, create_link_editor
from lib.mgeo.class_defs import *
from lib.mgeo.utils import utils
import lib.mgeo.save_load.mgeo_load as mgeo_load
import lib.mgeo.save_load.mgeo_save as mgeo_save

import ngii_shp_ver2_importer as importer


def load_from_file_and_draw():
    input_path = '../../rsc/map_data/ngii_shp_ver2_191226_모라이_제공자료/서울_자율주행테스트베드/SEC01_서울자율주행테스트베드'
    output_path = '../../output/'
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

    """
    Origin이 되는 Point를 찾는다
    Origin은 현재는 A1_NODE에서 검색되는 첫번째 포인트로한다
    """
    origin = get_first_shp_point(map_info['A1_NODE'])
    origin = np.array(origin)
    np.set_printoptions(suppress=True)
    print('[INFO] Origin =', origin)


    # 이제 여기서 NODE, LINK 파일을 읽어준다.
    shp_node = map_info['A1_NODE']
    shp_link = map_info['A2_LINK']

    # Node, 일반 Link, 차선 변경 Link 생성하는 코드
    node_set_dict, junction_set = importer.create_node_set(shp_node, origin)
    line_set_dict = importer.create_link_set(shp_link, origin, node_set_dict)
    lane_ch_line_set_dict = importer.create_lane_change_link_set(shp_link, line_set_dict) 

    # 일반 Link, 차선 변경 Link를 합쳐서 total_line_set 생성
    total_line_set_dict = LineSet.merge_two_sets(line_set_dict, lane_ch_line_set_dict)
    
    # TEMP(sglee): 차선 변경 링크 생성 생략. 
    total_line_set_dict = line_set_dict
    
    """ 뷰어 만들어주기 """
    fig_lane = plt.figure()
    ui = create_link_editor()
    ui.pass_down(output_path)
    ui.set_geometry_obj(total_line_set_dict, node_set_dict)

    # xlim = [-50, 950]
    # ylim = [-650, 250]
    # ui.set_absolute_bbox_for_plot(xlim, ylim)
    ui.update_plot(plt.gcf(), plt.gca(), enable_node=ui.enable_node, draw=True)


    """ 사용자 입력에 따른 콜백 모음 """
    cid_click = fig_lane.canvas.mpl_connect('button_press_event', ui.on_click)
    cid_press = fig_lane.canvas.mpl_connect('key_press_event', ui.on_key)
    cid_scroll = fig_lane.canvas.mpl_connect('scroll_event', scr_zoom)

    # 그려서 확인해보기
    plt.show()

    print('[INFO] Ended Successfully.')


def load_for_xodr():
    relative_loc = True

    input_path = '../../rsc/map_data/ngii_shp_ver2_191226_모라이_제공자료/서울_자율주행테스트베드/SEC01_서울자율주행테스트베드'
    input_path = os.path.join(current_path, input_path)
    input_path = os.path.normpath(input_path)   

    output_path = '../../saved/'
    output_path = os.path.join(current_path, output_path)
    output_path = os.path.normpath(output_path)

    print('[INFO] input path:', input_path)
    print('[INFO] output path:', output_path) 
    
    # Get Map Information
    map_info = read_shp_files(input_path)

    """
    Origin이 되는 Point를 찾는다
    Origin은 현재는 A1_NODE에서 검색되는 첫번째 포인트로한다
    """
    origin = get_first_shp_point(map_info['A1_NODE'])
    origin = np.array(origin)
    np.set_printoptions(suppress=True)
    print('[INFO] Origin =', origin)


    # 이제 여기서 NODE, LINK 파일을 읽어준다.
    shp_node = map_info['A1_NODE']
    shp_link = map_info['A2_LINK']
    # shp_cent = map_info['B2_SURFACELINEMARK']

    # Node, 일반 Link, 차선 변경 Link 생성하는 코드
    node_set_dict, junction_set = importer.create_node_set(shp_node, origin)
    line_set_dict = importer.create_link_set(shp_link, origin, node_set_dict)
    # lane_ch_line_set_dict = importer.create_lane_change_link_set(shp_link, line_set_dict) 
    line_set_dict = set_all_left_right_links(line_set_dict)
    
    """ 뷰어 만들어주기 """
    fig_lane = plt.figure()
    ui = create_link_editor()
    ui.pass_down(output_path)
    ui.set_geometry_obj(line_set_dict, node_set_dict, origin)

    # xlim = [-50, 950]
    # ylim = [-650, 250]
    # ui.set_absolute_bbox_for_plot(xlim, ylim)
    ui.update_plot(plt.gcf(), plt.gca(), enable_node=ui.enable_node, draw=True)


    # 사용자 입력에 따른 콜백 등록
    cid_click = fig_lane.canvas.mpl_connect('button_press_event', ui.on_click)
    cid_press = fig_lane.canvas.mpl_connect('key_press_event', ui.on_key)
    cid_scroll = fig_lane.canvas.mpl_connect('scroll_event', scr_zoom)

    # 그려서 확인해보기
    plt.show()

    print('[INFO] Ended Successfully.')


def convert_to_listset_and_save():
    input_path = '../../rsc/map_data/ngii_shp_ver2_191226_모라이_제공자료/서울_자율주행테스트베드/SEC01_서울자율주행테스트베드'
    output_path = '../../output/'
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

    """
    Origin이 되는 Point를 찾는다
    Origin은 현재는 A1_NODE에서 검색되는 첫번째 포인트로한다
    """
    origin = get_first_shp_point(map_info['A1_NODE'])
    origin = np.array(origin)
    print('[INFO] Origin =', origin)


    # 이제 여기서 NODE, LINK 파일을 읽어준다.
    shp_node = map_info['A1_NODE']
    shp_link = map_info['A2_LINK']

    # Node, 일반 Link, 차선 변경 Link 생성하는 코드
    node_set_dict, junction_set = importer.create_node_set(shp_node, origin)
    line_set_dict = importer.create_link_set(shp_link, origin, node_set_dict)
    lane_ch_line_set_dict = importer.create_lane_change_link_set(shp_link, line_set_dict)
    
    # 일반 Link, 차선 변경 Link를 합쳐서 total_line_set 생성
    total_line_set_dict = LineSet.merge_two_sets(line_set_dict, lane_ch_line_set_dict)

    
    # dict인 set을 
    node_set = utils.node_set_dict_to_list(node_set_dict)
    total_line_set = utils.line_set_dict_to_list(total_line_set_dict)


    # save
    save_path = filedialog.askdirectory(
        initialdir = output_path, 
        title = 'Save in the folder below') # defaultextension = 'json') 과 같은거 사용 가능    
    mgeo_save.save_node_and_link(save_path, node_set, total_line_set)


def main_load():
    relative_loc = True

    input_path = '../../rsc/map_data/ngii_shp_ver2_191226_모라이_제공자료/서울_자율주행테스트베드/SEC01_서울자율주행테스트베드'
    input_path = os.path.join(current_path, input_path)
    input_path = os.path.normpath(input_path)   

    output_path = '../../output/'
    output_path = os.path.join(current_path, output_path)
    output_path = os.path.normpath(output_path)

    print('[INFO] input path:', input_path)
    print('[INFO] output path:', output_path) 

    # load_path = filedialog.askdirectory(
    #     initialdir = output_path, 
    #     title = 'Load files from') # defaultextension = 'json') 과 같은거 사용 가능    
    # node_set, line_set = mgeo_load.load_node_and_link(load_path)

    link_set = LineSet()
    node_set = NodeSet()

    """ 뷰어 만들어주기 """
    fig_lane = plt.figure()

    # Link Editor 생성
    ui = create_link_editor()
    ui.pass_down(output_path)
    ui.set_geometry_obj(link_set, node_set)

    xlim = [-50, 950]
    ylim = [-650, 250]
    ui.set_absolute_bbox_for_plot(xlim, ylim)
    ui.update_plot(plt.gcf(), plt.gca(), enable_node=ui.enable_node, draw=True)


    # 사용자 입력에 따른 콜백 등록
    cid_click = fig_lane.canvas.mpl_connect('button_press_event', ui.on_click)
    cid_press = fig_lane.canvas.mpl_connect('key_press_event', ui.on_key)
    cid_scroll = fig_lane.canvas.mpl_connect('scroll_event', scr_zoom)

    # 그려서 확인해보기
    plt.show()

    print('[INFO] Ended Successfully.')


if __name__ == u'__main__':
    # load_from_file_and_draw()
    load_for_xodr()
    # convert_to_listset_and_save()
    # main_load()