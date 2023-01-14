import os 
import sys
from PyQt5.QtWidgets import QFileDialog

current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))
sys.path.append(os.path.normpath(os.path.join(current_path, '../../')))

import traceback
import numpy as np

from lib.mgeo.class_defs import *
from lib.mgeo.utils import error_fix
from lib.common.logger import Logger
from tkinter import filedialog


def get_mgeo_data(load_path):
    try:
        Logger.log_trace('load MGeo data from: {}'.format(load_path))

        if len([string for string in os.listdir(load_path) if '.json' in string]) == 0:
            new_load_path = os.path.join(load_path, os.listdir(load_path)[0])
        else:
            new_load_path = load_path

        mgeo = MGeo.create_instance_from_json(new_load_path)     

        return mgeo

    except BaseException as e:
        Logger.log_error('load_mgeo failed (traceback is down below) \n{}'.format(traceback.format_exc()))
        return None


def check_mgeo_data(file_path, log_path, log_file_name):
    '''
    Reference: https://morai.atlassian.net/wiki/spaces/CDTS/pages/611516835/
    '''
    Logger.create_instance(log_file_path=log_path)
    Logger.instance.file_name = os.path.normpath(os.path.join(log_path, log_file_name)) 

    Logger.log_trace('Called: check_mgeo_data')

    success = True
    mgeo = get_mgeo_data(file_path)

    # node 검사
    node_set = mgeo.node_set
    if node_set is None or len(node_set.nodes) < 1 :
        Logger.log_error("There is no node data.")
        return
    
    # link 검사
    link_set = mgeo.link_set
    if link_set is None or len(link_set.lines) < 1 :
        Logger.log_error("There is no link data.")
        return
    
    if check_max_speed(mgeo) is False:
        success = False

    if check_mgeo_item_type_def(mgeo) is False:
        success = False
    
    if check_related_signal(mgeo) is False:
        success = False
    
    if check_on_stop_line(mgeo) is False:
        success = False

    if check_dangling(mgeo) is False:
        success = False

    if check_lane_change(mgeo) is False:
        success = False

    if check_mismatch(mgeo) is False:
        success = False
    
    if check_link_point_interval(mgeo) is False:
        success = False

    """검사 항목 #1"""
    # 모든 링크 검사해서, max_speed = 0 인 링크가 있으면 오류 출력하기
    # 오류 메세지: 'link idx:{} >> max_speed == 0'
    # error_msg = 'link idx:{} >> max_speed == 0'.format(link)

    """검사 항목 #2"""
    # 모든 링크 검사해서, link가 참조하는 신호등이 있는데 related_signal이 None인 링크가 있으면 오류 출력하기
    # error_msg = 'link idx:{} >> is reference by TL (idx: {}), but has related_signal as None'.format(link.idx, traffic_light_idx)
    result = {'success': success, 'result_log': Logger.instance.file_name} 
    return result



def check_max_speed(mgeo):
    result = True
    for link_idx in mgeo.link_set.lines:
        link = mgeo.link_set.lines[link_idx]
        
        # 차선변경링크유무
        if link.__dict__.__contains__('lane_ch_link_path'):
            if link.lane_ch_link_path is not None:
                continue
        
        if link.__dict__.__contains__('lazy_point_init'):
            if bool(link.lazy_point_init):
                continue
        

        if link.max_speed == '0' or link.max_speed == None or  link.max_speed == 0:
            error_msg = 'link idx:{} >> max_speed == 0'.format(link_idx)
            Logger.log_error(error_msg)
            result = False
    return result
            

def check_related_signal(mgeo):
    result = True
    for tl in mgeo.light_set.signals:
        if mgeo.light_set.signals[tl].type == 'pedestrian':
            continue
        if mgeo.light_set.signals[tl].link_list is not None or len(mgeo.light_set.signals[tl].link_list) > 0 :
            for link in mgeo.light_set.signals[tl].link_list:
               
                if link.related_signal is None or link.related_signal == '':
                    error_msg = 'link idx:{} >> is reference by TL (idx: {}), but has related_signal as None'.format(link.idx, tl)
                    Logger.log_error(error_msg)
                    result = False
                else:
                    if mgeo.light_set.signals[tl].type is not 'car':
                        continue
                    
                    if mgeo.light_set.signals[tl].sub_type == None:
                        Logger.log_error('신호등 subtype이 None입니다. tl_idx : {}'.format(tl))
                        result = False
                        continue

                    if link.related_signal not in mgeo.light_set.signals[tl].sub_type:
                        result = False
                        Logger.log_error('링크의 related signal 과 signal 의 sub type 이 맞지않음 (link : {}, tl_idx : {}) '.format(link.idx, tl))
                
                    

    
    return result


def check_on_stop_line(mgeo):
    result = True

    #lane boundary check
    if mgeo.lane_boundary_set is None:
        Logger.log_warning('Lane Boundary Set이 없다')

    for tl in mgeo.light_set.signals:
        traffic_light = mgeo.light_set.signals[tl]
        
        if traffic_light.type == 'pedestrian': # 보행자 신호등 제외
            continue
        
        if traffic_light.type_def == 'mgeo' and traffic_light.type == 'car' and 'misc' in traffic_light.sub_type:
            continue

        for link in traffic_light.link_list:
            if link.related_signal == 'uturn_normal' or link.related_signal == 'lowerleft' or link.related_signal == 'uturn' or link.related_signal == 'uturn_misc': # uturn 제외
                continue
            on_stop_node = link.from_node
            
            if on_stop_node is not None:
                if not bool(on_stop_node.on_stop_line):
                    error_msg = 'node (idx: {}) should have on_stop_line=True (currently False). The node is from_node of link (idx: {}), refrenced by TLs'.format(on_stop_node.idx, link.idx)
                    
                    Logger.log_error(error_msg)
                    result = False
    
    return result


def check_node_on_stop_line(lane_boundary_set):
    # for lane_boundary in lane_boundary_set.lanes:
    return
        

def check_dangling(mgeo):
    result = True
    dangling_nodes = error_fix.find_dangling_nodes(mgeo.node_set)
    dangling_links = error_fix.find_dangling_links(mgeo.link_set)
    
    if len(dangling_nodes) > 0:
        result = False
        Logger.log_error("exist dangling nodes")
    
    if len(dangling_links) > 0:
        result = False
        Logger.log_error("exist dangling links")
    
    return result

def check_mismatch(mgeo):
    result = True

    mismatch_lane_change_links_list = error_fix.find_mismatch_lane_change_links(mgeo.link_set)

    # mismatch = error_fix.find_mi

    if len(mismatch_lane_change_links_list)>0:
        result = False
        Logger.log_error("mismatch lane change links")

    return result    


def check_lane_change(mgeo):
    result = True
    
    for link_idx in mgeo.link_set.lines:
        link = mgeo.link_set.lines[link_idx]

        if link.can_move_left_lane:
            if link.lane_ch_link_left == '' or link.lane_ch_link_left == None:
                result = False
                Logger.log_error("lane_ch_link_left of link(link id : {}) is None".format(link_idx))
        
        if link.can_move_right_lane:    
            if link.lane_ch_link_right == '' or link.lane_ch_link_right == None:
                result = False
                Logger.log_error("lane_ch_link_right of link(link id : {}) is None".format(link_idx))
        
    
    return result



def check_mgeo_item_type_def(mgeo):
    result = True
    
    for link_idx in mgeo.link_set.lines:
         # 차선변경링크유무
        if mgeo.link_set.lines[link_idx].__dict__.__contains__('lane_ch_link_path'):
            if mgeo.link_set.lines[link_idx].lane_ch_link_path is not None:
                continue
        
        if mgeo.link_set.lines[link_idx].__dict__.__contains__('lazy_point_init'):
            if bool(mgeo.link_set.lines[link_idx].lazy_point_init):
                continue

        if mgeo.link_set.lines[link_idx].link_type_def == '' or mgeo.link_set.lines[link_idx].link_type_def == None:
            result = False
            Logger.log_error('link idx : {} >> type_def is empty.'.format(link_idx))
    
    for lane_boundary_idx in mgeo.lane_boundary_set.lanes:
        if mgeo.lane_boundary_set.lanes[lane_boundary_idx].lane_type_def == '' or mgeo.lane_boundary_set.lanes[lane_boundary_idx].lane_type_def == None:
            result = False
            Logger.log_error('laneboundary idx : {} >> type_def is empty.'.format(lane_boundary_idx))

    for signal_idx in mgeo.sign_set.signals:
        if mgeo.sign_set.signals[signal_idx].type_def == '' or mgeo.sign_set.signals[signal_idx].type_def == None:
            result = False
            Logger.log_error('signal idx : {} >> type_def is empty'.format(signal_idx)) 
    
    return result


def check_link_point_interval(mgeo):
    result = True
    for link_idx in mgeo.link_set.lines:
        # 차선변경링크제외
        if mgeo.link_set.lines[link_idx].__dict__.__contains__('lane_ch_link_path'):
            if mgeo.link_set.lines[link_idx].lane_ch_link_path is not None:
                continue
        
        if mgeo.link_set.lines[link_idx].__dict__.__contains__('lazy_point_init'):
            if bool(mgeo.link_set.lines[link_idx].lazy_point_init):
                continue

        link_points = mgeo.link_set.lines[link_idx].points
        # link를 구성하는 포인트가 아래와 같이 3개라고 하자
        # link_points = np.array([ [0, 0],  [3, 4], [-3, -4]])

        # 아래와 같이 결과가 나와야 한다
        # [0,0] ~ [3, 4] 까지의 거리는 5
        # [3,4] ~ [-3,-4] 까지의 거리는 10
        # answer = [5, 10]

        # 계산 방법: 우선 x 좌표 벡터 , y 좌표 벡터를 나눈다
        x = link_points[:,0]
        y = link_points[:,1]

        # 각 벡터의 인접한 element 끼리의 차를 계산하는 함수를 사용
        dx = np.ediff1d(x)
        dy = np.ediff1d(y)

        # 이렇게 처리해주면 끝
        dist = np.sqrt(dx**2 + dy**2)

        if any(dist >= 1):
            result = False
            Logger.log_error('link id : {} >> link point interval greater than 1m '.format(link_idx)) 

    return result


            
def test_main_case1():
    '''
    File Browser 통해서 mgeo 데이터 path 받고, 테스트 수행 
    '''
    log_file_path = os.path.normpath(os.path.join(current_path, 'log'))
    Logger.create_instance(log_file_path=log_file_path)

    Logger.log_trace('Called: mgeo load')
       
    # init_load_path = self.get_path_from_config('MGEO_LOAD')
    # Logger.log_trace('init_load_path: {}'.format(init_load_path))
 
    # mgeo_file_path = QFileDialog.getExistingDirectory(self, 'Select a folder that contains MGeo data', 
    #              QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)
    input_path = '../../../saved/'
    input_path = os.path.join(current_path, input_path)
    input_path = os.path.normpath(input_path)

    mgeo_file_path = filedialog.askdirectory(initialdir = input_path, 
        title = 'Load files from')

    # mgeo_file_path = 'C:\\Users\\HI\\Desktop\\test\\mgeo\\mgeo_kcity_210806_AM1000'
    
    if (mgeo_file_path == '' or mgeo_file_path == None):
        Logger.log_error('invalid mgeo_file_path (your input: {})'.format(mgeo_file_path))
        return
    
    log_path = os.path.normpath(os.path.join(mgeo_file_path, 'log'))
    log_file_name = 'log.log'
    
    """ 경로 넘겨줘서 mgeo 데이터 읽어오기 """
    mgeo = get_mgeo_data(mgeo_file_path)

    """ 검사하고 결과 출력하기 """
    result = check_mgeo_data(mgeo_file_path, log_path, log_file_name) 
    # result = {'success': True or False, 'result_log': log 파일 경로}

    result = check_on_stop_line(mgeo)

    return result


def test_main_case2():
    # mgeo_file_path 에는 S3 에서 다운 받은 데이터의 경로를 입력할 수도 있다
    # 이렇게 쓸 경우에는,
    # MGeo 데이터는 임시 경로에 다운 받도록 하고, (예: 현재 코드 위치에 temp/맵이름_다운로드시간 같은 형식으로 경로 생성)
    # 해당 경로를 넘겨준다


    """ S3 에서 KCity 데이터를 다운로드 받는다 """
    # 임시 경로 하나 생성하기 (temp/맵이름_다운로드시간)

    # 다운로드 받기

    # 압축 풀기

    """ 경로 넘겨줘서 mgeo 데이터 읽어오기 """
    mgeo = get_mgeo_data(mgeo_file_path)

    """ 검사하고 결과 출력하기 """
    result = check_mgeo_data(mgeo)

    return result




if __name__ == u'__main__':
    result = test_main_case1()

    

    
