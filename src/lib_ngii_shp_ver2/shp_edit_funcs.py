import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))

import numpy as np
import matplotlib.pyplot as plt
from tkinter import filedialog
import pickle

from lib.mgeo.class_defs import *
from lib.mgeo.edit.funcs import edit_line
import lib.mgeo.save_load.mgeo_load as mgeo_load
import lib.mgeo.save_load.mgeo_save as mgeo_save
import lib.mgeo.utils.error_fix as mgeo_error_fix
import lib.mgeo.utils.version as mgeo_utils

from generate_mesh import make_road, make_road_delaunay, make_road_gmsh,\
    plot_vtkPolyData, unify_normal, smooth_mesh
from lib.common import display, file_io, vtk_utils

from lib.mgeo.path_planning.dijkstra import Dijkstra


def create_link_editor():
    return UserInput(1)


def create_mesh_creation_tool():
    return UserInput(0, 2)


class UserInput:
    def __init__(self, edit_mode=0, mesh_mode=1):
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

        # Edit Mode
        self.edit_mode = edit_mode
        # edit_mode = 0 : Mesh 편집하는 모드
        # edit_mode = 1 : Link 편집하는 모드
        # TODO: 리팩토링할 것. UserInput 클래스는 UserInput만 받아주고
        # 내부에서는 편집 기능을 담고 있는 eventHandler에 대한 reference만 있도록한다
        # 그렇게해서, Mesh 편집 시에는 Mesh 편집 기능을 갖고 있는 클래스의 인스턴스를 참조하고
        # Link 편집 시에는 Link 편집 기능을 갖고 있는 클래스의 인스턴스를 참조하게 한다
        
        self.annotation_text = None
        self.annotation_id = None
        self.selected_point_mark = None
        self.selected_line_mark = None

        # 항상 이 값이 관리된다
        self.selected_node = None # Node로 선택할 때
        self.selected_point = None
        self.selected_line = None
        self.start_node = None
        self.start_point = None
        self.start_line = None
        self.start_point_mark = None 
        self.end_node = None
        self.end_point = None
        self.end_line = None
        self.end_point_mark = None
        self.origin = None

        # Editor Status
        self.selected_mesh_method = mesh_mode
        self.ORIGINAL = 1
        self.DELAUNAY = 2
        self.TEST_GMSH = 3
        self.connector_length = 1

        # Geometry Sets
        self.line_set = None
        self.node_set = NodeSet()
        self.plane_set = PlaneSet()
        self.plane_set.create_a_new_empty_plane()
        self.junction_set = None

        # Plot 관련
        self.enable_node = False
        self.abs_xlim = None # Plot할 때 해당 범위에 있지 않으면 아예 제외 
        self.abs_ylim = None # Plot할 때 해당 범위에 있지 않으면 아예 제외 

        # Mouse Right Click 시 옵션
        self.select_by_node = True
        self.mouse_right_click_vis_option_node_idx = True
        self.mouse_right_click_vis_option_point_idx = False
        self.mouse_right_click_vis_option_line_idx_text = False

        self.plane_display = list()
        self.eliminated_list = list()


    def set_origin(self, origin):
        self.origin = origin

    def pass_down(self, _handout):
        self.linedata_path = _handout


    def set_geometry_obj(self, _line_set, _node_set, _origin=None):
        self.line_set = _line_set 
        
        self.ref_points = self.line_set.get_ref_points()
        self.current_selected_point_idx_in_ref_point = None

        self.node_set = _node_set
        
        # if self.origin has not already been set by self.set_origin()
        if self.origin is None:
            self.set_origin(_origin)

    def set_junction_obj(self, _junction_set):
        self.junction_set = _junction_set


    def _find_nearest_point_node_base(self, search_coord):
        if self.node_set is None:
            print_warn('[ERROR] There is no node_set')
            return

        min_dist = np.inf
        nearest_node = None
        for var in self.node_set.nodes:
            if isinstance(self.node_set.nodes, dict):
                node = self.node_set.nodes[var] # key로서 동작한다
            else: # 이 경우 list이다.
                node = var 

            if node.point[0:2].shape != (2,) :
                raise BaseException('[ERROR] @ _find_nearest_point_node_base: node.point.shape is not what is expected.')

            pos_vector = node.point[0:2] - search_coord
            dist = np.linalg.norm(pos_vector, ord=2)
            if dist < min_dist and dist > 0:
                min_dist = dist
                nearest_node = node

        return min_dist, nearest_node


    def _find_nearest_point_node_auto(self, search_node, search_node_links):
        if self.node_set is None:
            print_warn('[ERROR] There is no node_set')
            return

        min_dist = np.inf
        nearest_node = None
        for var in self.node_set.nodes:
            if isinstance(self.node_set.nodes, dict):
                node = self.node_set.nodes[var] # key로서 동작한다
            else: # 이 경우 list이다.
                node = var 

            # 거리 계산할 node들이 점검조건을 만족하는지 확인
            # (search_node는 이미 윗단에서 수행)
            node_links = node.get_to_links() + node.get_from_links()
            if (len(node_links) > 1
                or node in self.eliminated_list
                or node_links[0] is search_node_links[0]):
                continue

            if node.point[0:2].shape != (2,):
                raise BaseException('[ERROR] @ _find_nearest_point_node_base: node.point.shape is not what is expected.')

            pos_vector = node.point[0:2] - search_node.point[0:2]
            dist = np.linalg.norm(pos_vector, ord=2)
            if dist < min_dist and dist > 0:
                min_dist = dist
                nearest_node = node

        return min_dist, nearest_node


    def _find_nearest_point_ref_point_base(self, search_coord):
        if self.ref_points is None:
            print_warn('[ERROR] ref_points must be initialized using set_geometry_obj method')
            return

        # search for nearest node coordinates
        closest_dist = np.inf
        point_found = False
        dist_click = np.sqrt(search_coord[0]**2 + search_coord[1]**2)
        
        for i in range(len(self.ref_points)):
            # 현재 선택된 포인트는 다시 선택하지 않도록 Skip한다
            if self.current_selected_point_idx_in_ref_point != None:
                if i == self.current_selected_point_idx_in_ref_point:
                    print('[DEBUG] Skipping currently selected point ({})'.format(i))
                    continue

            x_diff = self.ref_points[i]['coord'][0] - search_coord[0]
            y_diff = self.ref_points[i]['coord'][1] - search_coord[1]
            dist_candidate = np.sqrt(x_diff**2 + y_diff**2)

            if dist_candidate < closest_dist:
                closest_dist = dist_candidate
                selected_point = self.ref_points[i]
                selected_point_idx_in_ref_point = i
                point_found = True

        if point_found is False:
            print_warn('[ERROR] Reference point not found! Try clicking away from\
                the graphs\'s origin')
            return

        # 반드시 리턴하기 전에 별도로 저장해주어야 한다
        # For loop 내에서 이를 업데이트하면 정상적으로 동작할 수 없다
        self.current_selected_point_idx_in_ref_point = selected_point_idx_in_ref_point
        return closest_dist, selected_point


    def _update_point_display(self, fig, ax):
        # 아래에서 사용할 로컬 변수를 업데이트한다
        line_idx = self.selected_point['idx_line'] 
        line_idx_text = idx = self.selected_point['idx_text_line'] 
        point_idx = self.selected_point['idx_point'] 

        point_type = self.selected_point['type']
        x = self.selected_point['coord'][0]
        y = self.selected_point['coord'][1]
        z = self.selected_point['coord'][2]

        if point_type == 'start':
            node_ref = self.selected_point['line_ref'].get_from_node()
            node_str = 'node={}'.format(node_ref.idx)
        elif point_type == 'end':
            node_ref = self.selected_point['line_ref'].get_to_node()
            node_str = 'node={}'.format(node_ref.idx)
        else:
            node_str = ""
        
        # print(
        #     '[INFO] line id={}, type={} (node id = {}), '.format(line_idx, point_type) +
        #     'loc=[{:.1f}, {:.1f}, {:.1f}] '.format(x,y,z))

        # [STEP #2] show text around the selected node
        if self.annotation_text != None:
            self.annotation_text.remove()
            fig.canvas.draw()

        if self.mouse_right_click_vis_option_line_idx_text:
            display_str = point_type + ', line=({}, {})'.format(line_idx, line_idx_text)
        else:
            display_str = point_type + ', line={}'.format(line_idx)


        if self.mouse_right_click_vis_option_point_idx:
            display_str += ', point={}'.format(point_idx)


        if self.mouse_right_click_vis_option_node_idx and node_str != "":
            display_str += ", " + node_str

    
        self.annotation_text = ax.text(x + 1, y + 1, display_str)


        # [STEP #3] Draw a mark on the selected node
        if self.selected_point_mark != None:
            for prev_selected_point in self.selected_point_mark:
                prev_selected_point.remove()
            # self.selected_point_mark[0].remove()

            # NOTE: [VERY IMPORTANT]
            # https://stackoverflow.com/questions/4981815/how-to-remove-lines-in-a-matplotlib-plot
            # Vorticity의 답변 참조. self.selected_point_mark에 대한 reference가 다른 장소에 남아있다면
            # 마우스 우클릭을 할 때마다 생성되는 point 객체가 메모리 상에 상주하고 garbage collected 되지 않는다.
            # 따라서 self.selected_point_mark = [] 이를 명시적으로 호출해주어야 한다.
            # 물론, 이 글이 오래된 글이라 현재의 Matplotlib에서 같은 동작일지는 모르겠으나 일단 따라해놓는다.
            # ax.lines.remove(self.selected_point_mark)
            # self.selected_point_mark = []


        if point_type == 'start': # start
            self.selected_point_mark = ax.plot(x, y,
                marker='^',
                markersize=10,
                color='g')
            fig.canvas.draw()

        elif point_type == 'mid':
            self.selected_point_mark = ax.plot(x, y,
                marker='d',
                markersize=10,
                color='g')
            fig.canvas.draw()

        else: # end
            self.selected_point_mark = ax.plot(x, y,
                marker='v',
                markersize=10,
                color='g')
            fig.canvas.draw()


    def update_plot(self, fig, ax, enable_node, draw=False):
        '''
        현재 공간에서 xlim, ylim을 찾아서, 근처 범위에 있는 line, node만 그려준다
        '''
        if draw:               
            if self.abs_xlim is None or self.abs_ylim is None:
                # 설정이 안 되어 있으면 그냥 다 그린다

                self.node_set.erase_plot()
                self.line_set.erase_plot()

                self.node_set.draw_plot(ax)
                self.line_set.draw_plot(ax)

            else:
                # 설정이 되어 있으면, 해당 구간에 있는 것만 그린다

                # nodes가 list이든 dict이든 상관없이 적용할 수 있다.
                for var in self.node_set.nodes:

                    if  isinstance(self.node_set.nodes, list):
                        node = var
                    elif isinstance(self.node_set.nodes, dict):                 
                        node = self.node_set.nodes[var]
                    else:
                        raise BaseException('[ERROR] Unexpected type for node_set.nodes')

                    if self._is_out_of_bbox_point(
                        self.abs_xlim, self.abs_ylim,
                        node.point[0], node.point[1]):
                        continue

                    node.erase_plot()
                    node.draw_plot(ax)


                for var in self.line_set.lines:
                    if  isinstance(self.line_set.lines, list):
                        line = var
                    elif isinstance(self.line_set.lines, dict):                    
                        line = self.line_set.lines[var]
                    else:
                        raise BaseException('[ERROR] Unexpected type for line_set.lines')

                    if self._is_out_of_bbox(
                        self.abs_xlim, self.abs_ylim,
                        line.bbox_x, line.bbox_y):
                        continue

                    line.erase_plot()
                    line.draw_plot(ax)
                
            # ax.set_aspect('equal')

        # node disable이면 일단 전체를 disable 시킨다
        if not enable_node:
            if isinstance(self.node_set.nodes, list):
                for node in self.node_set.nodes:   # TEMP(list->dict)
                    node.hide_plot()

            elif isinstance(self.node_set.nodes, dict):
                for idx, node in self.node_set.nodes.items(): # TEMP(list->dict)
                    node.hide_plot()
            else:
                raise BaseException('[ERROR] self.node_set.nodes must be either a dict or a list')

        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        
        # 현재 공간에서 margin을 준다
        margin = 2


        def _add_margin(lim, margin):
            mid = (lim[1] + lim[0])/2
            dist_from_mid = (lim[1] - lim[0])/2

            new_min = mid - dist_from_mid * margin
            new_max = mid + dist_from_mid * margin
            return (new_min, new_max)

        xlim = _add_margin(xlim, margin)
        ylim = _add_margin(ylim, margin)

        # 해당 라인에 있는
        if isinstance(self.line_set.lines, list):
            for line in self.line_set.lines:   # TEMP(list->dict)
                
                # NOTE: VERY_UGLY 아래쪽 dict 일때 코드와 같은 작업. 리팩토링할 것
                line_xlim = line.bbox_x
                line_ylim = line.bbox_y
                
                if self._is_out_of_bbox(xlim, ylim, line_xlim, line_ylim):
                    line.hide_plot()
                    # 관련 node에도 적용
                    if line.from_node is not None: # line 또는 link에 문제가 있는 경우 none일 수 있다.
                        line.from_node.hide_plot()
                    if line.to_node is not None: # line 또는 link에 문제가 있는 경우 none일 수 있다.
                        line.to_node.hide_plot()
                    continue
                else:
                    line.unhide_plot()

                if enable_node:
                    if line.from_node is not None: # line 또는 link에 문제가 있는 경우 none일 수 있다.
                        line.from_node.unhide_plot()
                    if line.to_node is not None: # line 또는 link에 문제가 있는 경우 none일 수 있다.
                        line.to_node.unhide_plot()

        elif isinstance(self.line_set.lines, dict):
            for idx, line in self.line_set.lines.items(): # TEMP(list->dict)
                
                # NOTE: VERY_UGLY 위쪽 list 일때 코드와 같은 작업. 리팩토링할 것
                line_xlim = line.bbox_x
                line_ylim = line.bbox_y

                if self._is_out_of_bbox(xlim, ylim, line_xlim, line_ylim):
                    line.hide_plot()
                    # 관련 node에도 적용
                    if line.from_node is not None: # line 또는 link에 문제가 있는 경우 none일 수 있다.
                        line.from_node.hide_plot()
                    if line.to_node is not None: # line 또는 link에 문제가 있는 경우 none일 수 있다.
                        line.to_node.hide_plot()
                    continue
                else:
                    line.unhide_plot()
                
                if enable_node:
                    if line.from_node is not None: # line 또는 link에 문제가 있는 경우 none일 수 있다.
                        line.from_node.unhide_plot()
                    if line.to_node is not None: # line 또는 link에 문제가 있는 경우 none일 수 있다.
                        line.to_node.unhide_plot()
        else:
            raise BaseException('[ERROR] self.line_set.line must be either a dict or a list')
        

        
        # plt.draw를 쓰면 동작하지 않는다.
        # 참조: https://stackoverflow.com/questions/30880358/matplotlib-figure-not-updating-on-data-change
        fig.canvas.draw()


    def set_absolute_bbox_for_plot(self, xlim, ylim):
        self.abs_xlim = xlim
        self.abs_ylim = ylim


    def _is_out_of_bbox(self, xlim, ylim, line_xlim, line_ylim):
        # x축에 대해
        if line_xlim[1] < xlim[0] or line_xlim[0] > xlim[1]:
            return True

        # y축에 대해
        if line_ylim[1] < ylim[0] or line_ylim[0] > ylim[1]:
            return True
        
        return False


    def _is_out_of_bbox_point(self, xlim, ylim, x_pos, y_pos):
        # x축에 대해
        if x_pos < xlim[0] or x_pos > xlim[1]:
            return True

        # y축에 대해
        if y_pos < ylim[0] or y_pos > ylim[1]:
            return True
        
        return False


    def _connect_lines(self, start_node, end_node, mode):
        '''
        2개의 node 간의 여러 점으로 이뤄진 선을 잇는다
        입력 1: 시작 노드의 좌표
        입력 2: 끝 노드의 좌표
        출력: return 없음
        '''
        if mode == 0:
            ''' Mesh Creation Mode'''
            # unit vector로 fill line 만들면 점의 숫자가 너무 많아져 vector 크기를 조정
            # 가능하도록 step_len 변수 추가
            step_len = self.connector_length

            vect_s_to_e = end_node.point - start_node.point
            mag = np.linalg.norm(vect_s_to_e, ord=2) # 벡터의 크기 계산
            unit_vect = vect_s_to_e / mag
            step_vect = step_len * unit_vect
            cnt = (int)(np.floor(mag / step_len))

            connecting_line = Line()
            edit_line.create_the_first_point(connecting_line, start_node.point)
            edit_line.create_points_from_current_pos_using_step(
                connecting_line,
                xyz_step_size=step_vect,
                step_num=cnt)
            
            # new_end point는 mag와 step_len 관계에 따라 추가하지 않아도 되는 경우가 있다
            if mag % step_len == 0:
                # 우연히 magnitude가 step_len의 배수인 경우이다.
                # 이 경우, 이미 create_points_from... 메소드에 의해
                # new_end에 해당하는 point가 linkLine에 추가되었다
                pass
            else:
                connecting_line.add_new_points(end_node.point)        

            # 이 라인의 from_node, to_node 설정해주기
            connecting_line.set_from_node(start_node)
            connecting_line.set_to_node(end_node)
        
        else:
            """ Link Edit Mode """
            # 가정: 두 점이 충분히 가까워서, 중간에 point를 생성할 필요가 없다.
            connecting_line = Link()
            points = np.vstack((start_node.point,end_node.point))
            connecting_line.set_points(points)

            # 이 라인의 from_node, to_node 설정해주기
            connecting_line.set_from_node(start_node)
            connecting_line.set_to_node(end_node)

        # line_set_object에 저장해주기 
        self.line_set.append_line(connecting_line, create_new_key=True)
        if isinstance(self.line_set.lines, list):
            self.line_set.reorganize()
        self.ref_points = self.line_set.get_ref_points()


    def on_click(self, event):
        '''
        Constants:
        MouseButton.LEFT = 1
        MouseButton.MIDDLE = 2
        MouseButton.RIGHT = 3
        '''
        fig = plt.gcf()

        # save clicked location
        if event.button == 3:  # MouseButton.RIGHT = 3
            ax = event.inaxes
            
            # [STEP #1] 클릭한 Point와 해당 Point가 포함된 Line을 찾아 업데이트한다
            if self.select_by_node:
                """ 
                self.node_set를 이용하여 선을 선택한다.
                단, node가 아닌, 선의 중심을 선택하고 싶을 때는 사용하지 못하는 문제가 있다.
                """
                search_coord = np.array([event.xdata, event.ydata])
                closest_dist, selected_node =\
                    self._find_nearest_point_node_base(search_coord)

                # 같은 노드를 다시 선택한거면, 현재 링크에 있는 다른 링크를 선택해준다
                if self.selected_node is selected_node:
                    # 검색해야할 링크의 종류를 만든다
                    to_links = selected_node.get_to_links()
                    from_links = selected_node.get_from_links()
                    related_links = to_links + from_links # 해당 노드에서 출발하는 링크를 먼저 검색

                    def get_next_link(related_links, current_link):
                        for i in range(len(related_links)):
                            if current_link is related_links[i]:
                                next_i = i + 1
                                if next_i == len(related_links):
                                    next_i = 0
                                return related_links[next_i]

                        # current_link가 None이거나 해서 related_link 내에서 못 찾으면
                        # 그냥 첫번째 값으로
                        next_i = 0
                        return related_links[next_i]

                    # 현재 선택되어 있던 링크 말고, 다음 링크를 선택해준다    
                    self.selected_line = get_next_link(related_links, self.selected_line)
                    

                    #print('selected_line: {}'.format(self.selected_line.idx))
                else:
                    # 그냥 다른 노드를 선택한 것이었으면,
                    # 해당 노드에 있는 related_link 중 아무거나를 선택
                    # to_links 또는 from_links 둘 중 하나가 [] 일 수 있기 때문에 이렇게 함
                    to_links = selected_node.get_to_links()
                    from_links = selected_node.get_from_links()
                    related_links = to_links + from_links
                    if len(related_links) == 0:
                        print_warn('[ERROR] There are no links connected to this node')
                        return 
                    self.selected_line = related_links[0]

                # 선택된 노드를 업데이트해준다
                # self.selected_node = selected_node

                if self.selected_node is selected_node:
                    # 루프의 경우 무조건 같은 포인트 선택되는걸 막을려한다
                    if self.selected_point['type'] == 'end':
                        self.selected_point = self.selected_line.get_point_dict(0)
                    elif self.selected_point['type'] == 'start':
                        self.selected_point = self.selected_line.get_point_dict(-1)
                    else:
                        print_warn('[ERROR] Loop identification failed')
                        return
                elif self.selected_line.get_from_node() is selected_node:
                    self.selected_point = self.selected_line.get_point_dict(0)
                elif self.selected_line.get_to_node() is selected_node:
                    self.selected_point = self.selected_line.get_point_dict(-1)
                else:
                    raise BaseException('[ERROR] selected_node is not linked to the selected_line! (Not intended code flow)')

                # 선택된 노드를 업데이트해준다
                self.selected_node = selected_node

            else:
                """ 
                self.ref_points를 이용하여 선을 선택한다.
                단, 1개 노드에서 여러 개의 선이 나오는 경우, 선을 돌아가면서 선택하지 못하는 문제가 있다
                """
                search_coord = [event.xdata, event.ydata]

                closest_dist, self.selected_point =\
                    self._find_nearest_point_ref_point_base(search_coord)

                idx_line = self.selected_point['idx_line']

                if self.line_set == None:
                    print_warn('[ERROR] line_set must be set first!')
                    return

                self.selected_line = self.line_set.lines[idx_line]


            self._update_point_display(fig, ax)
                
            # [STEP #4] 선택한 point가 포함된 선을 표시해줌
            if self.selected_line_mark != None:
                for prev_selected_line in self.selected_line_mark:
                    prev_selected_line.remove()
            self.selected_line_mark = ax.plot(self.selected_line.points[:,0], self.selected_line.points[:,1],
                marker='d',
                markersize=3,
                color='r',
                linewidth=1)

            fig.canvas.draw()


    def on_key(self, event):
        '''
        [Key Mapping]
        
        [Node & Line Edit]
        q:      Start point
        w:      End point
        c:      Connect q->w
        alt+c:  Change spacing b/n connecting line points
        s:      Save (depreciated)
        alt+s:  Save as JSON
        l:      Load (depreciated)
        alt+l:  Load JSON
        ctrl+z: Delete selected line
        ctrl+p: Simplify Node/Line data
        ctrl+o: Simplify point data (decimation)
        b:      Line bisection
        r:      Change right click selection mode
        ctrl+i  Connect lines automatically

        [View Control]
        v:      Change current view
        alt+v:  Toggle node ID on/off

        [Plane Edit]
        ,:      Enter  Plane Making Mode
        TODO: 이거 대신 't' 키에 toggle로 할당하고, 
              Node/Line 편집 모드 <-> Plane 편집 모드 토글링되도록
              => Title 같은 텍스트에 상태를 표시해주는 형태로

        n:      Load a PlaneSet object from a file
        m:      Select a node for a plane
        alt+m:  Reset selected node list for plane creation
        ,:      Register the plane (a set of nodes) to the set of planes 
        .:      Save the PlaneSet object as a file
        /:      Create meshes from set of planes
        ctrl+/: Change mesh creation method
        ctrl+d: Delete a selected plane
        k:      Add centerline to a plane boundary

        [Debug Mode]
        ctrl+alt+d: Enter debug mode
        d:      Delete overlapping nodes
        h:      Highlight lines
        alt+h:  Reset highlighting
        alt+d:  Enter fix mode
        '''
        
        # NOTE: 기존에는 ax = event.inaxes 를 사용하고 있었음
        #       현재는 그냥 gca를 사용하도록 한다.
        #       그 이유는 편집한 정보를 load하여 plot을 할 때
        #       axes가 선택이 안 되어, event.inaxes가 None이 반환되어
        #       ax.plot 에서 오류가 발생할 수 있기 때문이다. 
        # TODO: 향후 여러 종류의 axes를 사용해야하면 axes를 매니징하는
        #       클래스를 두고, 해당 클래서 받아오게 해야한다.
        #       또 그러한 경우에는 이벤트 별로 ax를 달리 받아와야 한다.
        fig = plt.gcf()
        ax = plt.gca()
        
        if event.key != 'up' or event.key != 'down':
            print('[DEBUG] Key pressed: ', event.key)

        if event.key == 'up' or event.key == 'down':
            if self.line_set is None:
                print_warn('[ERROR] line_set must be set first!')
                return

            if self.selected_point != None:
                # line을 먼저 찾는다
                idx_line = self.selected_point['idx_line']
                self.selected_line = self.line_set.lines[idx_line]

                line_idx_text = self.selected_point['idx_text_line']

                # idx point 값을 이동
                idx_point = self.selected_point['idx_point'] 
                if event.key == 'up':
                    idx_point = idx_point + 1
                else:
                    idx_point = idx_point - 1
                
                # idx limiter
                if idx_point < 0:
                    idx_point = 0
                if idx_point > self.selected_line.get_last_idx():
                    idx_point = self.selected_line.get_last_idx()
                
                self.selected_point = self.selected_line.get_point_dict(idx_point)               
                self._update_point_display(fig, ax)
        

        elif event.key == 'q':
            if self.selected_point == None or self.selected_line_mark  == None:
                print_warn('[ERROR] A point must be selected!')
                return

            self.start_node = self.selected_node
            self.start_point = self.selected_point
            self.start_line = self.selected_line
            
            if self.start_point_mark != None and self.start_point_mark != []:
                ax.lines.remove(self.start_point_mark[0])
            
            x = self.start_point['coord'][0]
            y = self.start_point['coord'][1]
            self.start_point_mark = ax.plot(x, y,
                marker='o',
                markersize=15,
                color='b')
            fig.canvas.draw()
            print('[INFO] Start point selected.')


        elif event.key == 'w':
            if self.selected_point == None or self.selected_line_mark  == None:
                print_warn('[ERROR] A point must be selected!')
                return

            self.end_node = self.selected_node
            self.end_point = self.selected_point
            self.end_line = self.selected_line

            if self.end_point_mark != None and self.end_point_mark != []:
                ax.lines.remove(self.end_point_mark[0])

            x = self.end_point['coord'][0]
            y = self.end_point['coord'][1]
            self.end_point_mark = ax.plot(x, y,
                marker='P',
                markersize=15,
                color='b')
            fig.canvas.draw()
            print('[INFO] End point selected.')
                

        elif event.key == 'alt+c':
            self.connector_length = float(input(
                'Set connecting line length (unit vector x input): '))
            print('Connector line length set to {}'.format(self.connector_length))


        elif event.key == 'c' or event.key == 'C':
            if self.start_point == None or self.start_line == None:
                print_warn('[ERROR] A start point must be specified!')
                return

            if self.end_point == None or self.end_line == None:
                print_warn('[ERROR] An end point must be specified!')
                return

            
            # link 수정모드인 경우에는 
            # 방향이 맞는지 체크한다
            # 방향이 틀리면 오류를 발생시킨다.
                
            # 원하는 상황은
            # start_point가 end이고
            # end_point가 start인 경우이다
            if self.edit_mode == 1:
                if self.start_point['type'] != 'end' or self.end_point['type'] != 'start':
                    print_warn('[ERROR] A new connecting link cannot be created. Check the direction again!')
                    return

            # start_point에 해당하는 node 찾아오기 
            if self.start_point['type'] == 'start':
                # 현재 start_point로 설정된 점이, 해당 라인에서 start이면,
                # 우리가 연결해야하는 노드는 해당 라인의 from_node이다.
                start_node = self.start_point['line_ref'].get_from_node()
            elif self.start_point['type'] == 'end':
                # 현재 start_point로 설정된 점이, 해당 라인에서 end이면,
                # 우리가 연결해야하는 노드는 해당 라인의 to_node이다.
                start_node = self.start_point['line_ref'].get_to_node()
            else:
                print_warn('[ERROR] @ UserInput.on_key: Unexpected type of start_point: {}'.format(self.start_point['type']))
                return
            

            # end_point에 해당하는 node 찾아오기
            if self.end_point['type'] == 'start':
                # 현재 start_point로 설정된 점이, 해당 라인에서 start이면,
                # 우리가 연결해야하는 노드는 해당 라인의 from_node이다.
                end_node = self.end_point['line_ref'].get_from_node()
                pass
            elif self.end_point['type'] == 'end':
                # 현재 start_point로 설정된 점이, 해당 라인에서 end이면,
                # 우리가 연결해야하는 노드는 해당 라인의 to_node이다.
                end_node = self.end_point['line_ref'].get_to_node()
                pass
            else:
                print_warn('[ERROR] @ UserInput.on_key: Unexpected type of start_point: {}'.format(self.start_point['type']))
                return

            
            # (hjpark): vtk mesh 생성을 위해서 두 점 사이 다수의 점 배치
            new_start = start_node.point
            new_end = end_node.point

            if self.edit_mode == 0:
                """ Mesh Creation Mode """

                # unit vector로 fill line 만들면 점의 숫자가 너무 많아져 vector 크기를 조정
                # 가능하도록 step_len 변수 추가
                step_len = self.connector_length


                # new_start -> new_end로 향하는 선을 구성하는 점을 만들기 위한 값들
                vect_s_to_e = new_end - new_start
                mag = np.linalg.norm(vect_s_to_e, ord=2) # 벡터의 크기 계산
                unit_vect = vect_s_to_e / mag
                step_vect = step_len * unit_vect
                cnt = (int)(np.floor(mag / step_len))
            

                # new_start -> new_end로 향하는 정의
                connecting_line = Line()
                edit_line.create_the_first_point(connecting_line, new_start)
                edit_line.create_points_from_current_pos_using_step(
                    connecting_line,
                    xyz_step_size=step_vect,
                    step_num=cnt)
                

                # new_end point는 mag와 step_len 관계에 따라 추가하지 않아도 되는 경우가 있다
                if mag % step_len == 0:
                    # 우연히 magnitude가 step_len의 배수인 경우이다.
                    # 이 경우, 이미 create_points_from... 메소드에 의해
                    # new_end에 해당하는 point가 linkLine에 추가되었다
                    pass
                else:
                    connecting_line.add_new_points(new_end)
                

                # 이 라인의 from_node, to_node 설정해주기
                connecting_line.set_from_node(start_node)
                connecting_line.set_to_node(end_node)
            
            else:
                """ Link Edit Mode """
                # 가정: 두 점이 충분히 가까워서, 중간에 point를 생성할 필요가 없다.

                connecting_line = Link()
                points = np.vstack((new_start,new_end))
                connecting_line.set_points(points)

                # 이 라인의 from_node, to_node 설정해주기
                connecting_line.set_from_node(start_node)
                connecting_line.set_to_node(end_node)



            # line_set_object에 저장해주기 
            self.line_set.append_line(connecting_line, create_new_key=True)
            if isinstance(self.line_set.lines, list):
                self.line_set.reorganize()
            self.ref_points = self.line_set.get_ref_points()


            # connecting line 그린 후 start/end 마커 지우기
            ax.lines.remove(self.start_point_mark[0])
            ax.lines.remove(self.end_point_mark[0])
            del self.end_point_mark[0]
            del self.start_point_mark[0]

            self.update_plot(fig, ax, enable_node=self.enable_node, draw=True)

            print('[INFO] Connecting line created')
        

        elif event.key == 'r':
            if self.select_by_node is True:
                self.select_by_node = False
                _mode = 'point mode'
            elif self.select_by_node is False:
                self.select_by_node = True
                _mode = 'node mode'
            print('[INFO] Node selection mode changed: {}'.format(
                _mode))


        elif event.key == 's' or event.key == 'S':
            if self.edit_mode == 1:
                print_warn('[ERROR] Invalid input for link edit mode')
                return

            savefile_name = filedialog.asksaveasfilename(
                initialdir = self.linedata_path, 
                title = 'Save as') # defaultextension = 'json') 과 같은거 사용 가능

            if savefile_name == '' or savefile_name == None:
                print_warn('[WARN] Save operation cancelled')
                return

            with open(savefile_name, 'wb') as savefile_obj_pickle:
                # pickle.dump([self.node_set, self.line_set], savefile_obj_pickle)
                pickle.dump([self.node_set, self.line_set, self.plane_set],
                    savefile_obj_pickle)

            print('[INFO] Data saved as binary')
        

        elif event.key == 'alt+s':
            save_path = filedialog.askdirectory(
                initialdir = self.linedata_path, 
                title = 'Save files as') # defaultextension = 'json') 과 같은거 사용 가능    

            if save_path == '' or save_path == None:
                print_warn('[WARN] Load operation cancelled')
                return
            
            if self.edit_mode == 0:
                # 평면 편집 모드
                # 지금 편집 중인게 평면이면?
                mgeo_save.save(save_path, self.node_set, self.line_set, self.plane_set)
            
            elif self.edit_mode == 1:
                # 링크 편집 모드
                mgeo_planner_map = MGeo(self.node_set, self.line_set)
                mgeo_planner_map.set_origin(self.origin)
                mgeo_planner_map.to_json(save_path)
            
            else:
                print_warn('[ERROR] self.edit_mode is invalid!! (value = {}) This instance might be initialized in an unexpected way'.format(self.edit_mode))

            print('[INFO] Data saved as json files')


        elif event.key == 'alt+l':

            load_path = filedialog.askdirectory(
                initialdir = self.linedata_path, 
                title = 'Load files from') # defaultextension = 'json') 과 같은거 사용 가능    
            
            if load_path == '' or load_path == None:
                print_warn('[WARN] Load operation cancelled')
                return

            # 현재 라인셋의 draw 설정 백업
            # line_set 인스턴스를 받은 다음 이 값을 설정해주어야 하기 때문
            if len(self.line_set.lines) > 0: # empty인 workspace에서 load하려고 하면, 이 값이 0이므로
                if isinstance(self.line_set.lines, list):
                    vis_mode_all_different_color =\
                        self.line_set.lines[0].get_vis_mode_all_different_color()
                else:
                    for key in self.line_set.lines: # dict이다
                        line = self.line_set.lines[key]
                        vis_mode_all_different_color =\
                            line.get_vis_mode_all_different_color()
                        break # 한번만 실행하면 되기 때문
            else:
                vis_mode_all_different_color = False

            # 로드해온다
            if self.edit_mode == 0:
                node_set, line_set, plane_set = mgeo_load.load(load_path, random_search=True)

                line_set.set_vis_mode_all_different_color(vis_mode_all_different_color)

                # 기존에 있던 node_set, line_set 정리
                self.node_set.erase_plot()
                self.line_set.erase_plot()
                
                # 새로 로드한 node_set, line_set으로 변경
                self.set_geometry_obj(line_set, node_set)
                self.plane_set = plane_set
                self.update_plot(fig, ax, enable_node=self.enable_node, draw=True)

            elif self.edit_mode == 1:
                mgeo_planner_map = MGeo.create_instance_from_json(load_path)
                self.set_origin(mgeo_planner_map.local_origin_in_global)
                line_set = mgeo_planner_map.link_set
                node_set = mgeo_planner_map.node_set
                junction_set = mgeo_planner_map.junction_set

                line_set.set_vis_mode_all_different_color(vis_mode_all_different_color)
                
                # 기존에 있던 node_set, line_set 정리
                self.node_set.erase_plot()
                self.line_set.erase_plot()

                # 새로 로드한 node_set, line_set으로 변경
                self.set_geometry_obj(line_set, node_set)
                self.set_junction_obj(junction_set)
                self.update_plot(fig, ax, enable_node=self.enable_node, draw=True)

            else:
                print_warn('[ERROR] self.edit_mode is invalid!! (value = {}) This instance might be initialized in an unexpected way'.format(self.edit_mode))

            print('[INFO] Loaded data from json files')

        elif event.key == 'l' or event.key == 'L':
            if self.edit_mode == 1:
                print_warn('[ERROR] Invliad input for link edit mode')
                return

            loadfile_name = filedialog.askopenfilename(
                initialdir = self.linedata_path, 
                title = 'Select data file')

            if loadfile_name == '' or loadfile_name == None:
                print_warn('[WARN] Load operation cancelled')
                return

            self.line_set.erase_plot()
            self.node_set.erase_plot()

            with open(loadfile_name, 'rb') as loadfile_obj_pickle:
                # node_set, line_set = pickle.load(loadfile_obj_pickle)
                node_set, line_set, plane_set = pickle.load(loadfile_obj_pickle)
                self.set_geometry_obj(line_set, node_set)
                self.plane_set = plane_set

            # NOTE: 매우 중요! plt.gca()를 쓰면 동작하지 않는다. 
            # 아마도 askopenfilename과 관련이 있는 듯함
            self.update_plot(fig, ax, enable_node=self.enable_node, draw=True)

            print('[INFO] Loaded data from binary')


        elif event.key == 'ctrl+z': # delete a single line
            if self.selected_line == None:
                print_warn('[ERROR] A line must be selected')
                return


            if self.selected_line.included_plane:
                print_warn('[ERROR] This line has a plane associated to it\
                    please delete the plane first')
                return

            to_node = self.selected_line.get_to_node()
            from_node = self.selected_line.get_from_node()

            to_node.remove_from_links(self.selected_line)
            from_node.remove_to_links(self.selected_line)

            self.selected_line.erase_plot() # don't we have to remove the plotted_obj from ax.lines?
            self.line_set.remove_line(self.selected_line)


            # 만일 link edit 모드이면, 좀 더 수행해야 할 작업이 있다.
            # dst link로 설정되어 있으면 dst link를 없애야 한다
            if self.edit_mode == 1:
                for var in self.line_set.lines:
                    if  isinstance(self.line_set.lines, list):
                        line = var
                    elif isinstance(self.line_set.lines, dict):                    
                        line = self.line_set.lines[var]
                    else:
                        raise BaseException('[ERROR] Unexpected type for line_set.lines')
                    
                    # 차선 변경이 아닌 링크에 대해서만 검사하면 된다.
                    if not line.is_it_for_lane_change():
                        if line.get_left_lane_change_dst_link() is self.selected_line:
                            line.lane_ch_link_left = None
                        if line.get_right_lane_change_dst_link() is self.selected_line:
                            line.lane_ch_link_right = None

            # selected_line 이 존재하지 않으므로 정리해준다
            self.selected_line = None

            # 선이 삭제되었으므로, line_set을 reorganize해준다
            if isinstance(self.line_set.lines, list):
                self.line_set.reorganize()

            self.ref_points = self.line_set.get_ref_points()

            # ax.lines.remove(self.conn_lines_obj[-1][0])
            # del self.conn_lines_obj[-1]

            ax.lines.remove(self.selected_line_mark[0])
            ax.lines.remove(self.selected_point_mark[0])
            del self.selected_line_mark[0]
            del self.selected_point_mark[0]
            self.annotation_text.remove()
            self.annotation_text = None

            self.update_plot(fig, ax, enable_node=self.enable_node, draw=True)

            # print('[INFO] Most recent line deleted')
            print('[INFO] Selected line deleted')


        elif event.key == 'n':
            print('[INFO] Load a PlaneSet object from a file')

            loadfile_name = filedialog.askopenfilename(
                initialdir = self.linedata_path, 
                title = 'Select PlaneSet object')

            # 현재 plane_set 내부의 planes 들을 삭제하고
            # JSON 파일에서 읽은 값으로 새로운 plane을 생성
            self.plane_set.load_from_json(self.node_set, loadfile_name)
            print('[INFO] Loaded a PlaneSet object from file: {}'.format(loadfile_name))
            self.plane_set.print()


        elif event.key == 'm':
            print('[INFO] Add this node for a plane creation node set')
            # 최신 Plane에 대해 편집 진행
            if self.selected_point == None:
                print_warn('[ERROR] A point must be selected!')
                return
            
            if self.selected_point['type'] == 'start':
                _selected_node = self.selected_point['line_ref'].get_from_node()
            elif self.selected_point['type'] == 'end':
                _selected_node = self.selected_point['line_ref'].get_to_node()
            else:
                print_warn('[ERROR] Either a start or end node must be selected!')
                return


            # 최신 Plane의 node에 append
            try:
                _selected_node.included_in_plane = True
                self.plane_set.get_last_plane().append_node(_selected_node)
            except BaseException as e:
                print_warn(e)
                return

            print('[INFO] Plane creation node added successsfully.')


        elif event.key == 'alt+m':
            if self.plane_set.get_last_plane() == []:
                print_warn('[ERROR] There are no planes')
                return

            self.plane_set.get_last_plane().reset_plane()

            print('[INFO] Reset current plane creation node set')


        elif event.key == ',':
            print('[INFO] Register the current set of nodes as a plane')
            # 현재 작업 중인 plane의 작업을 종료
            if self.plane_set.get_last_plane().is_closed():

                plane_registered = self.plane_set.get_last_plane()

                for line in plane_registered.line_connection:
                    line['line'].add_included_plane(plane_registered)

                self.update_plot(fig, ax, enable_node=self.enable_node, draw=True)

                # 새로운 plane을 만들도록 한다
                self.plane_set.create_a_new_empty_plane()

            else:
                # TODO(sglee): warning function 구현
                print('[ERROR] You need to choose more nodes to create a plane correctly!')
                return
                # print_warn('[ERROR] You need to choose more nodes to create a plane correctly!') 
            print('[INFO] Plane registered successfully.')


        elif event.key == '.':
            print('[INFO] Save the current PlaneSet object as a file') 
            
            # [TEMP] For Test
            # self.plane_set.get_last_plane().init_from_node_idx_list(self.node_set, [10, 7, 4, 1, 10])
            # self.plane_set.create_a_new_empty_plane()
            # self.plane_set.get_last_plane().init_from_node_idx_list(self.node_set, [1, 4, 3, 2, 1])
            # self.plane_set.create_a_new_empty_plane()
            # self.plane_set.get_last_plane().init_from_node_idx_list(self.node_set, [4, 7, 6, 5, 4])
            # self.plane_set.create_a_new_empty_plane()
            # self.plane_set.get_last_plane().init_from_node_idx_list(self.node_set, [0, 11, 10]) # incomplete

            savefile_name = filedialog.asksaveasfilename(
                initialdir = self.linedata_path, 
                title = 'Save Mesh as',
                defaultextension = 'json') # defaultextension = 'json') 과 같은거 사용 가능
            
            # JSON 파일로 저장
            self.plane_set.save_as_json(savefile_name)   

            print('[INFO] Saved a PlaneSet object to the file: {}'.format(savefile_name)) 


        elif event.key == '/':
            print('[INFO] Create an 3d mesh (.obj) file from plane set')
            
            # [TEMP] For Test
            # self.plane_set.get_last_plane().init_from_node_idx_list(self.node_set, [10, 7, 4, 1, 10])
            # self.plane_set.create_a_new_empty_plane()
            # self.plane_set.get_last_plane().init_from_node_idx_list(self.node_set, [1, 4, 3, 2, 1])

            
            # [STEP #1] line_set에 있는 모든 line을 구성하는 point를 모은다
            all_points = list() # 모든 line을 구성하는 point
            line_position = [] # 각 line의 시작하는 점, 끝 점이 all_points 안에서 존재하는 위치

            for line in self.line_set.lines:
                start_id = len(all_points)
                all_points += line.points.tolist()
                end_id = len(all_points) - 1
                line_position.append({
                    'start': start_id, 
                    'end': end_id,
                    'line': line})
                print('line={:<5} | start_id={:<5}, end_id = {:<5}'.format(line.idx, start_id, end_id))

            # [STEP #2] 각 면을 구성할 point가 all_points에서 어디서 존재하는지, 그 index값을 plane별로 찾아주어야 함
            faces = []

            if self.selected_mesh_method == self.DELAUNAY or self.TEST_GMSH:
                delaunay_pt_list = list() # delaunay 함수를 위해 별도 포인트 목록 구성
                persistent_idx = 0
                tolerance_del = 0 # NOTE: 사용자가 설정할 수 있도록 별도 시스템 필요

            for plane in self.plane_set.planes:
                # closed 된 plane이 아니면 skip
                if not plane.is_closed():
                    continue

                # 현재 plane의 상태를 출력해준다
                print(plane.to_string())

                # 현재 plane을 구성할 point들의 index (all_points 안에서 존재하는 위치) 들이 아래 저장된다
                face = []
                new_face = []
                same_point_idx = list()
                same_point_all_idx = list()
                for conn in plane.line_connection:
                    for line_pos in line_position:
                        if conn['line'] == line_pos['line']:
                            p1 = line_pos['start']
                            p2 = line_pos['end']
                            break

                    # plane을 구성할 각 선에 대해 idx 와 방향 여부를 찾는다
                    reverse = conn['reverse']
                    
                    if reverse:
                        # 반대 방향으로 가야하면, p2 -> p1 방향으로. 
                        # NOTE: arange는 마지막 값을 포함하지 않기 때문에, 끝 값(p1)을 포함하려면
                        # 끝값에 -1이 필요 (step=-1인 경우)
                        face += np.arange(p2, p1 - 1, step=-1, dtype=np.int32).tolist()
                    else:
                        # 정방향으로 가야하면, p1 -> p2 방향으로. 
                        # NOTE: arange는 마지막 값을 포함하지 않기 때문에, 끝 값(p2)을 포함하려면
                        # 끝값에 +1이 필요 (step=1인 경우)
                        face += np.arange(p1, p2 + 1, step=1, dtype=np.int32).tolist()
                
                # Delaunay 함수 사용 시 모든 point가 독립(unique)이어야 오류 없이 알고리즘이 동작한다
                # 중복이 되는 face 및 all_points point를 식별하여, 삭제하도록 한다
                if self.selected_mesh_method == self.DELAUNAY or self.TEST_GMSH:
                    for idx, point in enumerate(face):
                        if idx + 1 == len(face):
                            next_point = face[0] # 마지막 face point일 경우 첫번째 face point와 비교
                        else:
                            next_point = face[idx+1]

                        _x_diff = abs(all_points[point][0] - all_points[next_point][0])
                        _y_diff = abs(all_points[point][1] - all_points[next_point][1])
                        
                        # if all_points[point] == all_points[next_point]:
                        if _x_diff < 0.1 and _y_diff < 0.1:
                            same_point_idx.append(idx)

                    same_point_idx.reverse()

                    for entry in same_point_idx:
                        face.pop(entry)

                    for idx, pt in enumerate(face):
                        delaunay_pt_list.append(all_points[pt])
                        new_face.append(idx + persistent_idx)

                    # for loop 돌면서 리스트가 확장되므로 기준 index를 계속 더한다    
                    persistent_idx = idx + 1
                
                if plane.internal_nodes != []:
                    for each_node in plane.internal_nodes:
                        delaunay_pt_list.append(each_node)

                # 이를 전체 면을 구성할 index 리스트에 넣는다
                if self.selected_mesh_method == self.ORIGINAL:
                    faces.append(face)
                elif self.selected_mesh_method == self.DELAUNAY or self.TEST_GMSH:
                    faces.append(new_face)

            # [STEP #3] Mesh를 생성한다
            savefile_name = filedialog.asksaveasfilename(
                initialdir = self.linedata_path, 
                title = 'Save Mesh as:') # defaultextension = 'json') 과 같은거 사용 가능

            if self.selected_mesh_method == self.ORIGINAL:
                poly_obj = make_road(all_points, faces)
                file_io.write_stl_and_obj(poly_obj, savefile_name)
            elif self.selected_mesh_method == self.DELAUNAY:
                delny_obj = make_road_delaunay(delaunay_pt_list, faces, tolerance_del,
                print_log=False)
                poly_smooth = smooth_mesh(delny_obj)
                poly_normal = unify_normal(poly_smooth)
                file_io.write_obj(poly_normal, savefile_name)
            elif self.selected_mesh_method == self.TEST_GMSH:
                make_road_gmsh(delaunay_pt_list, faces, savefile_name)
                print_warn('[WARN] GMSH functionality is depreciated')
                return
            else:
                print_warn('[ERROR] No mesh method selected')
                return

            print('[INFO] Mesh successfully created')


        elif event.key == 'ctrl+/':
            self.selected_mesh_method += 1
            if self.selected_mesh_method > 3: # change number value here to len(dict)
                self.selected_mesh_method = self.ORIGINAL
            
            # if self.selected_mesh_method == self.method_directory.get('ORIGINAL'):
            #     self.selected_mesh_method = self.method_directory.get('DELAUNAY')
            #     method_print = 'DELAUNAY'

            print('[INFO] Mesh creation method changed: {}'.format(
                self.selected_mesh_method))


        elif event.key == 'alt+v':
            print('[INFO] Toggle node view')
            
            # Toggle
            self.enable_node = not self.enable_node

            # Then, update
            self.update_plot(fig, ax, enable_node=self.enable_node, draw=False)


        elif event.key == 'v':
            print('[INFO] Update line & node plot')
            self.update_plot(fig, ax, enable_node=self.enable_node, draw=False)
                

        elif event.key == 'ctrl+p': # simplify data
            simplify_candidate = list()

            # [DEBUG ONLY CODE]
            for var in self.node_set.nodes:
                if isinstance(self.node_set.nodes, dict):
                    node = self.node_set.nodes[var]
                else:
                    node = var
                for link in node.get_to_links() + node.get_from_links():
                    if link.idx not in self.line_set.lines:
                        print('link.idx = {} not in self.link_set.links'.format(link.idx))

            # [STEP] simplify를 적용해야할 candidate note를 계산한다
            # 아래 for문을 함수 전환 시 'only find straight lines' 라고 이름 붙이면 정확
            for var in self.node_set.nodes:
                # node_set.nodes는 구현에 따라 list일수도, dict일 수도 있다
                if isinstance(self.node_set.nodes, dict):
                    node = self.node_set.nodes[var]
                else:
                    node = var

                # Plane 구성하는 핵심 node일 경우 삭제 안되도록 처리
                if node.included_in_plane is True:
                    continue
                
                if len(node.get_to_links()) == 1 and len(node.get_from_links()) == 1:
                    simplify_candidate.append(node)

            # [STEP] simplify를 적용할 candidate note 각각에 대해 처리 
            if len(simplify_candidate) == 0:
                print_warn('[ERROR] There are no nodes to simplify!')
                return
            else:
                # 이미 삭제한 라인의 idx를 저장 >> 중복으로 삭제 요청하는 걸 막기 위함
                removed_line_idx = []

                for sc_node in simplify_candidate:
                    # for each node, connect its from_link and to_link together
                    # then, update each from_node and to_node
                    # NOTE: (hjpark) 아직 여러 경우에 수에 대해 테스팅이 필요함
                    #       특히 to_node, from_node를 여러 개 소유하는 node의 경우
                    #       for문 대신 index[0]를 explicit하게 처리하여 (구현 편의 위해)
                    #       충분히 예외가 발생할 여지가 있음 
                    current_node_to_link = sc_node.get_to_links()[0]
                    current_node_from_link = sc_node.get_from_links()[0]

                    # 선 2개로 이뤄진 circular line 예외처리
                    if current_node_from_link == current_node_to_link:
                        continue

                    # closed plane들은 최소 2개의 line으로 구성되도록 조치
                    # 시험용으로 도입하였으나, 롤백하는걸로 결정
                    # if current_node_to_link.get_to_node() == \
                    #     current_node_from_link.get_from_node():
                    #     continue

                    # 새로운 라인/링크 생성
                    new_line = Line()
                    
                    new_line.set_points(np.vstack((sc_node.point, current_node_to_link.points)))
                    new_line.set_points(np.vstack((current_node_from_link.points, new_line.points)))

                    to_node = sc_node.get_to_nodes()[0]
                    from_node = sc_node.get_from_nodes()[0]
                    
                    to_node.remove_from_links(current_node_to_link)
                    from_node.remove_to_links(current_node_from_link)

                    new_line.set_to_node(to_node)
                    new_line.set_from_node(from_node)

                    self.line_set.append_line(new_line, create_new_key=True)                       

                    # 기존 라인/링크 삭제 (이미 삭제한 라인을 또 삭제하라고 할 수 있어 다음과 같이 처리)
                    # if current_node_to_link.idx not in removed_line_idx:
                    #     print('[TRACE] Removing {}'.format(current_node_to_link.idx))
                    #     current_node_to_link.erase_plot()
                    #     removed_line_idx.append(current_node_to_link.idx)
                    #     self.line_set.remove_line(current_node_to_link)
                    # if current_node_from_link.idx not in removed_line_idx:
                    #     print('[TRACE] Removing {}'.format(current_node_from_link.idx))
                    #     current_node_from_link.erase_plot()                        
                    #     removed_line_idx2.append(current_node_from_link.idx)
                    #     self.line_set.remove_line(current_node_from_link)

                    self.line_set.remove_line(current_node_to_link)
                    self.line_set.remove_line(current_node_from_link)

                    sc_node.erase_plot()
                    self.node_set.remove_node(sc_node)

            # line과 node를 삭제했으므로, reorganize해준다
            if isinstance(self.line_set.lines, list):
                self.line_set.reorganize()
            if isinstance(self.node_set.nodes, list):
                self.node_set.reorganize()
            self.ref_points = self.line_set.get_ref_points()

            # Plot 다시 그리기
            self.line_set.erase_plot()
            self.node_set.erase_plot()
            self.update_plot(fig, ax, enable_node=self.enable_node, draw=True)
            
            print('[INFO] Node simplification process complete')


        elif event.key == 'ctrl+o':
            print('[INFO] Point decimation process - Only use after importing data')
            if len(self.line_set.lines) < 1:
                print_warn('[WARN] No lines are loaded, cannot perform decimation')
                return

            # TODO(hjpark) add a way to modify this number
            decimation = 2

            for line in self.line_set.lines:
                line.decimate_points(decimation)

            self.ref_points = self.line_set.get_ref_points()
            self.line_set.erase_plot()
            self.node_set.erase_plot()
            self.update_plot(fig, ax, enable_node=self.enable_node, draw=True)
            
            print('[INFO] Point decimation complete')


        elif event.key == 'ctrl+i':
            print('[INFO] Automatic point connection system')

            for var in self.node_set.nodes:
                if isinstance(self.node_set.nodes, dict):
                    node = self.node_set.nodes[var] # key로서 동작한다
                else: # 이 경우 list이다
                    node = var

                node_links = node.get_to_links() + node.get_from_links()

                if len(node_links) == 1:
                    if node in self.eliminated_list:
                        continue

                    _distance, closest_node = self._find_nearest_point_node_auto(
                        node, node_links)

                    self._connect_lines(node, closest_node, self.edit_mode)
                    
                    self.eliminated_list.append(node)
                    self.eliminated_list.append(closest_node)
            
            # 모든 node에 대한 확인 작업 완료 후 전체 plot 다시 그리기
            self.update_plot(fig, ax, enable_node=self.enable_node, draw=True)

            print('[INFO] Point connection completed')


        elif event.key == 'b' or event.key == 'B': # line bisection
            if self.selected_point is None or self.selected_line_mark is None:
                print_warn('[ERROR] A point must be selected!')
                return
            if self.selected_point['type'] == 'start' or self.selected_point['type'] == 'end':
                print_warn('[ERROR] Cannot divide the line at an endpoint!')
                return

            # identify what line we're on
            to_node = self.selected_line.get_to_node()
            from_node = self.selected_line.get_from_node()

            # divide the current line wrt the selected cut point
            idx_point = self.selected_point['idx_point'] 

            # create a new node
            new_node = Node()
            new_node.point = self.selected_line.points[idx_point]

            if self.edit_mode == 0:
                # create two new lines
                new_to_line = Line()
                new_from_line = Line()

            elif self.edit_mode == 1:
                # create two new lines
                new_to_line = Link()
                new_from_line = Link()
            else:
                raise BaseException('[ERROR] Unexpected edit_mode')
            
            new_to_line.set_points(self.selected_line.points[idx_point:])
            new_from_line.set_points(self.selected_line.points[0:idx_point+1])

            to_node.remove_from_links(self.selected_line)
            from_node.remove_to_links(self.selected_line)

            new_to_line.set_to_node(to_node)
            new_to_line.set_from_node(new_node)
            new_from_line.set_to_node(new_node)
            new_from_line.set_from_node(from_node)

            # add new objects to set lists
            self.node_set.append_node(new_node, create_new_key=True)
            self.line_set.append_line(new_to_line, create_new_key=True)
            self.line_set.append_line(new_from_line, create_new_key=True)

            # delete old objects from set lists
            self.selected_line.erase_plot()
            self.line_set.remove_line(self.selected_line)

            # clear selection markings from canvas
            ax.lines.remove(self.selected_point_mark[0])
            del self.selected_point_mark[0]
            self.annotation_text.remove()
            self.annotation_text = None           

            # rearrange set lists to prevent out of range errors
            if isinstance(self.line_set.lines, list):
                self.line_set.reorganize()
            
            self.ref_points = self.line_set.get_ref_points()

            self.update_plot(fig, ax, enable_node=self.enable_node, draw=True)

            print('[INFO] Line bisection complete')


        elif event.key == 'ctrl+d':
            if self.selected_point is None:
                print_warn('[ERROR] A point must be selected!')
                return
            if self.plane_set == []:
                print_warn('[ERROR] No plane objects to delete!')
                return

            del_plane_list = list()
            associated_lines = list()

            if self.selected_point['type'] == 'start':
                _source_node = self.selected_point['line_ref'].get_from_node()
            elif self.selected_point['type'] == 'end':
                _source_node = self.selected_point['line_ref'].get_to_node()
            else:
                # TODO(hjpark) 중간점에서 판단할 수 있도록 기능 확장
                print_warn('[ERROR] Must select a vertex point')
                return

            associated_lines += _source_node.get_to_links()
            associated_lines += _source_node.get_from_links()
            
            # get plane object, and if unique, add to list
            flag_repeat = False
            for line in associated_lines:
                associated_planes = line.get_included_planes()

                for plane in associated_planes:
                    if del_plane_list == []:
                        del_plane_list.append(plane)    

                    for entry in del_plane_list:
                        if plane == entry:
                            flag_repeat = True
                        
                    if flag_repeat is False:
                        del_plane_list.append(plane)
                    
                    flag_repeat = False

            plane_node = list()
            
            # extract plane points and display idx on the map
            for plane in del_plane_list:
                for node in plane.get_plane_nodes():
                    plane_node.append(node.point)

                plane_coord = (np.mean(plane_node, axis=0))

                disp_plane_str = 'Plane #{}'.format(plane.idx)
                disp_plane_obj = ax.text(plane_coord[0], plane_coord[1], disp_plane_str)
                self.plane_display.append(disp_plane_obj)

                plane_node.clear()

            # update map
            fig.canvas.draw()

            # throw up user input
            user_plane_selection = int(input('Choose which plane to delete (ID #): '))

            # delete selected plane
            flag_deleted = False
            for plane in del_plane_list:
                if user_plane_selection == plane.idx:
                    print('Deleting plane #{}'.format(plane.idx))
                    self.plane_set.remove_plane(plane)

                    for line in self.line_set.lines:
                        if plane in line.included_plane:
                            line.remove_included_plane(plane)
                    flag_deleted = True
                    
            for display_entry in self.plane_display:
                ax.texts.remove(display_entry)
            self.plane_display.clear()

            if flag_deleted is False:
                print_warn('[ERROR] Please input a valid plane id')
                return
                        
            # redraw lines
            self.update_plot(fig, ax, enable_node=self.enable_node, draw=True)

            print('[INFO] Plane removed')
        

        elif event.key == 'k':
            if self.selected_point == None:
                print_warn('[ERROR] A point must be selected!')
                return
            if self.plane_set == []:
                print_warn('[ERROR] No plane objects to change!')
                return

            # Plane 내 centerline을 mesh 생성 시 기준점으로 추가하는 기능 구현
            line_ref = self.selected_point['line_ref']
            from_node_ref = self.selected_point['line_ref'].get_from_node()
            to_node_ref = self.selected_point['line_ref'].get_to_node()

            for plane in self.plane_set.planes:
                plane.determine_bbox()

                if self._is_out_of_bbox_point(
                    plane.bbox_x, plane.bbox_y,
                    from_node_ref.point[0], from_node_ref.point[1]):
                    continue

                if self._is_out_of_bbox_point(
                    plane.bbox_x, plane.bbox_y,
                    to_node_ref.point[0], to_node_ref.point[1]):
                    continue

                # 선 전체가 plane 안에 속했을 시, 일부 point를 저장한다
                for idx, pts in enumerate(line_ref.points):
                    # if idx % 4 == 0:
                    #     plane.internal_nodes.append(pts)
                    plane.internal_nodes.append(pts)
                break

            print('[INFO] Centerline added to plane')

            
        elif event.key == 'd':
            # 같은 위치에 있는 node fix
            overlapped_node_sets = mgeo_error_fix.search_overlapped_node(self.node_set, 0.1)
            nodes_of_no_use = mgeo_error_fix.repair_overlapped_node(overlapped_node_sets)
            mgeo_error_fix.delete_nodes_from_node_set(self.node_set, nodes_of_no_use)


            # Djikstra 풀기
            # dijkstra_obj = Dijkstra(self.node_set.nodes, self.line_set.lines)
            # result, global_path = dijkstra_obj.find_shortest_path(start_node_id, end_node_id)
            

        elif event.key == 'ctrl+alt+d':
            print('[DEBUG] Entered Debug Mode')
            print('[DEBUG] Exiting Debug Mode')


        elif event.key == 'j': # Dijkstra
            print('[INFO] Entered Dijkstra Mode')

            if self.start_node == None:
                print_warn('[ERROR] A start node must be specified!')
                return

            if self.end_node == None:
                print_warn('[ERROR] An end node must be specified!')
                return

            # dijkstra로 경로 찾기
            dijkstra_obj = Dijkstra(self.node_set.nodes, self.line_set.lines)
            result, global_path = dijkstra_obj.find_shortest_path(self.start_node.idx, self.end_node.idx)
            if not result:
                print_warn('[ERROR] Failed to find path Node[{}] -> Node[{}]'.format(self.start_node.idx, self.end_node.idx))
                return

            # 기존에 그려둔 경로 plot이 있으면 지우기
            if hasattr(self, 'path_plot'):
                # 있으면 지우기
                if self.path_plot is not None:
                    for obj in self.path_plot:
                        if obj.axes is not None:
                            obj.remove()

            # 새로 찾은 경로 그리기
            global_path = np.array(global_path)
            x = global_path[:,0]
            y = global_path[:,1]
            self.path_plot = ax.plot(x, y, 
                linewidth=3,
                marker='',
                markersize=4,
                color='g')
        
            fig.canvas.draw()
            print('[INFO] Exiting Dijkstra Mode')


        elif event.key == 'h':
            # highlight를 쳐줘서 찾아준다 (line or link)
            # NOTE: 디버그 모드에서만 현재는 사용한다
            
            def _highlight_line(highlight_obj_idx_list):
                for var in self.line_set.lines:
                    if isinstance(self.line_set.lines, dict):
                        line = self.line_set.lines[var]
                    else:
                        line = var
                    if line.idx in highlight_obj_idx_list:
                        line.set_vis_mode_manual_appearance(3, 'b')
                    else:
                        line.set_vis_mode_manual_appearance(1, 'k')
            
            def _highlight_node(highlight_obj_idx_list):
                for var in self.node_set.nodes:
                    if isinstance(self.node_set.nodes, dict):
                        node = self.node_set.nodes[var]
                    else:
                        node = var
                    if node.idx in highlight_obj_idx_list:
                        node.set_vis_mode_manual_appearance(7, 'r', no_text=False)
                    else:
                        node.set_vis_mode_manual_appearance(3, 'g', no_text=True)

            # [사용 방법]
            ## _highlight_line(['A219BA000137'])
            ## _highlight_node(['A119BA000142'])

            # redraw
            self.update_plot(fig, ax, enable_node=self.enable_node, draw=True)


        elif event.key == 'alt+h':
            # reset highlight
            for var in self.line_set.lines:
                if isinstance(self.line_set.lines, dict):
                    line = self.line_set.lines[var]
                else:
                    line = var
                line.reset_vis_mode_manual_appearance()

            for var in self.node_set.nodes:
                if isinstance(self.node_set.nodes, dict):
                    node = self.node_set.nodes[var]
                else:
                    node = var
                node.reset_vis_mode_manual_appearance()

            # redraw
            self.update_plot(fig, ax, enable_node=self.enable_node, draw=True)


    def _temp_find_node(self, idx):
        for node in self.node_set.nodes:
            if node.idx == idx:
                return node

        return False


def scr_zoom(event):
    # reference:
    # https://stackoverflow.com/questions/11551049/matplotlib-plot-zooming-with-scroll-wheel

    # get current axis limits
    ax = event.inaxes
    fig = plt.gcf()

    if ax.get_xlim() == None:
        raise Exception('[ERROR] Scroll with the mouse cursor on the axes')

    cur_xlim = ax.get_xlim()
    cur_ylim = ax.get_ylim()
    cur_xrange = (cur_xlim[1] - cur_xlim[0])*0.5
    cur_yrange = (cur_ylim[1] - cur_xlim[0])*0.5

    # recognize scroll event
    if event.button == 'up':
        # zoom in
        sf = 0.5
    elif event.button == 'down':
        # zoom out
        sf = 2
    else:
        # error
        raise Exception('Scroll error')

    # set new axis limits
    # ax.set_xlim([event.xdata - cur_xrange*sf, event.xdata + cur_xrange*sf])
    # ax.set_ylim([event.ydata - cur_yrange*sf, event.ydata + cur_yrange*sf])
    ax.set_xlim([event.xdata - (event.xdata - cur_xlim[0])*sf, event.xdata + (cur_xlim[1] - event.xdata)*sf])
    ax.set_ylim([event.ydata - (event.ydata - cur_ylim[0])*sf, event.ydata + (cur_ylim[1] - event.ydata)*sf])

    # redraw plot
    # plt.draw()
    fig.canvas.draw()


def print_warn(msg):
    print(msg)