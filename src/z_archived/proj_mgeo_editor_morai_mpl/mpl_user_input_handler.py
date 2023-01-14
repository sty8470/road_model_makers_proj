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
from class_defs import *
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
from lib.stryx.stryx_load_geojson_lane import load_stryx_lane

class UserInputHandler:
    def __init__(self, edit_core, fig=None):
        # Disable a few keyboard shotcuts
        # NOTE: 다른 keymap 찾으려면 다음을 참고:
        # https://matplotlib.org/tutorials/introductory/customizing.html
        
        # 모든 matplotlib 단축키 해제
        for key, val in plt.rcParams.items():
            if 'keymap' in key:
                plt.rcParams[key] = ''

        # edit core
        self.edit_core = edit_core

        # 어떤 edit mode 인지 저장한다
        self.multistep_edit_mode = ''
        
        self.annotation_text = None
        self.annotation_id = None

        self.selected_point_mark = None
        self.selected_line_mark = None
        
        self.marker_start_node = None
        self.marker_end_node = None

        # Plot 관련
        self.enable_node = False
        self.enable_node_text = True # import 또는 load 시 toggle을 한번 호출해서 False로 변겨

        self.enable_signal = False
        self.enable_signal_text = True # import 또는 load 시 toggle을 한번 호출해서 False로 변겨

        self.enable_surface_marking = False
        self.enable_surface_marking_text = True # import 또는 load 시 toggle을 한번 호출해서 False로 변겨


        self.abs_xlim = None # Plot할 때 해당 범위에 있지 않으면 아예 제외 
        self.abs_ylim = None # Plot할 때 해당 범위에 있지 않으면 아예 제외 

        # Mouse Right Click 시 옵션
        self.select_by_node = True
        self.mouse_right_click_vis_option_node_idx = True
        self.mouse_right_click_vis_option_point_idx = False


        self.plane_display = list()
        self.eliminated_list = list()

        # matplotlib.pyplot 데이터
        if fig is None:
            """fig를 입력하지 않으면 임의로 생성한다"""
            fig = plt.figure()
            fig.set_size_inches(9,9)
        self.fig = fig

        # NOTE: FigureCanvas가 초기화된 다음에 connect를 해주어야만 동작한다 (mpl_canvas 참조)
        self.cid_click = self.fig.canvas.mpl_connect('button_press_event', self.on_click)
        self.cid_press = self.fig.canvas.mpl_connect('key_press_event', self.on_key)
        self.cid_scroll = self.fig.canvas.mpl_connect('scroll_event', self.on_scr_zoom)


    def start_simple_ui(self):
        self.update_plot(self.fig, plt.gca(), self.enable_node, draw=True)
        plt.show()


    def get_multistep_edit_mode(self):
        return self.multistep_edit_mode


    def set_multistep_edit_mode(self, mode):
        self.multistep_edit_mode = mode

    """MGeo 데이터셋 인스턴스에 대한 Get, Set Methods"""

    def get_node_set(self):
        return self.edit_core.mgeo_planner_map.node_set

    def get_line_set(self):
        return self.edit_core.mgeo_planner_map.link_set

    def get_ts_set(self):
        return self.edit_core.mgeo_planner_map.sign_set

    def get_tl_set(self):
        return self.edit_core.mgeo_planner_map.light_set

    def get_sm_set(self):
        return self.edit_core.mgeo_planner_map.sm_set


    """선택된 MGeo 인스턴스에 대한 Get, Set Methods"""

    def get_selected_node(self):
        return self.edit_core.select_func.selected_node
    

    def get_selected_line(self):
        return self.edit_core.select_func.selected_line


    def get_selected_point(self):
        return self.edit_core.select_func.selected_point
    

    def set_selected_line(self, line):
        self.edit_core.selected_line = line
    

    def set_selected_point(self, point):
        self.edit_core.select_func.selected_point = point


    def _update_point_display(self, fig, ax):
        # 아래에서 사용할 로컬 변수를 업데이트한다
        line_idx = self.get_selected_point()['idx_line'] 
        point_idx = self.get_selected_point()['idx_point'] 

        point_type = self.get_selected_point()['type']
        x = self.get_selected_point()['coord'][0]
        y = self.get_selected_point()['coord'][1]
        z = self.get_selected_point()['coord'][2]

        if point_type == 'start':
            node_ref = self.get_selected_point()['line_ref'].get_from_node()
            node_str = 'node={}'.format(node_ref.idx)
        elif point_type == 'end':
            node_ref = self.get_selected_point()['line_ref'].get_to_node()
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

    """UI 업데이트 핵심 기능"""

    def clear_start_end_marker(self):
        fig = plt.gcf()
        ax = plt.gca()

        # start/end 마커 지우기 (cancel시에는 marker가 None일 수 있다)        
        if self.marker_start_node is not None:
            ax.lines.remove(self.marker_start_node[0])
            del self.marker_start_node[0]
        
        if self.marker_end_node is not None:
            ax.lines.remove(self.marker_end_node[0])
            del self.marker_end_node[0]


    def clear_current_plot(self):
        # 현재 라인셋의 draw 설정 백업
        # line_set 인스턴스를 받은 다음 이 값을 설정해주어야 하기 때문
        if len(self.get_line_set().lines) > 0: # empty인 workspace에서 load하려고 하면, 이 값이 0이므로
            for idx in self.get_line_set().lines:
                line = self.get_line_set().lines[idx]
                vis_mode_all_different_color =\
                    line.get_vis_mode_all_different_color()
                break # 한번만 실행하면 되기 때문
        else:
            vis_mode_all_different_color = False

        # 기존에 있던 node_set, line_set 정리
        self.get_node_set().erase_plot()
        self.get_line_set().erase_plot()
        self.get_tl_set().erase_plot()
        self.get_ts_set().erase_plot()
        self.get_sm_set().erase_plot()


    def update_plot(self, fig, ax, draw=False):
        '''
        현재 공간에서 xlim, ylim을 찾아서, 근처 범위에 있는 line, node만 그려준다
        '''

        enable_node = self.enable_node
        enable_signal = self.enable_signal
        enable_surface_marking = self.enable_surface_marking

        if draw:               
            if self.abs_xlim is None or self.abs_ylim is None:
                # 설정이 안 되어 있으면 그냥 다 그린다

                self.get_node_set().erase_plot()
                self.get_line_set().erase_plot()
                self.get_ts_set().erase_plot()
                self.get_tl_set().erase_plot()
                self.get_sm_set().erase_plot()

                self.get_node_set().draw_plot(ax)
                self.get_line_set().draw_plot(ax)
                self.get_ts_set().draw_plot(ax)
                self.get_tl_set().draw_plot(ax)
                self.get_sm_set().draw_plot(ax)

            else:
                # 설정이 되어 있으면, 해당 구간에 있는 것만 그린다

                # nodes가 list이든 dict이든 상관없이 적용할 수 있다.
                for idx, node in self.get_node_set().nodes.items():
                    if node.is_out_of_xy_range(self.abs_xlim, self.abs_ylim):
                        continue

                    node.erase_plot()
                    node.draw_plot(ax)


                for idx, line in self.get_line_set().lines.items():
                    if line.is_out_of_xy_range(self.abs_xlim, self.abs_ylim):
                        continue

                    line.erase_plot()
                    line.draw_plot(ax)

                for idx, ts in self.get_ts_set().signals.items():
                    if ts.is_out_of_xy_range(self.abs_xlim, self.abs_ylim):
                        continue

                    ts.erase_plot() 
                    ts.draw_plot()

                for idx, tl in self.get_tl_set().signals.items():
                    if tl.is_out_of_xy_range(self.abs_xlim, self.abs_ylim):
                        continue

                    tl.erase_plot() 
                    tl.draw_plot()

                for idx, sm in self.get_sm_set().data.items():
                    if sm.is_out_of_xy_range(self.abs_xlim, self.abs_ylim):
                        continue

                    sm.erase_plot()
                    sm.draw_plot()
                    
                
            # ax.set_aspect('equal')

        """ VIEW = False인 대상은 그린 후 hide 한다 """
        if not enable_node:
            for idx, node in self.get_node_set().nodes.items():
                node.hide_plot()

        if not enable_signal:
            for idx, ts in self.get_ts_set().signals.items():
                ts.hide_plot()
            for idx, tl in self.get_tl_set().signals.items():
                tl.hide_plot()

        if not enable_surface_marking:
            for idx, sm in self.get_sm_set().data.items():
                sm.hide_plot()
            
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


        """danling node에 대한 hide/unhide 처리 별도로 함"""
        if enable_node:
            for idx, node in self.get_node_set().nodes.items():
                if node.is_dangling_node():
                    if node.is_out_of_xy_range(xlim, ylim):
                        node.hide_plot()
                    else:
                        node.unhide_plot()

                else:
                    # 특정 링크에 연결된 노드일 경우,
                    # 해당 링크의 bbox 여부로 hide/unhide 여부를 결정한다
                    continue


        """line, link 및 연결된 node에 대한 hide/unhide 처리"""
        for idx, line in self.get_line_set().lines.items():
            if line.is_out_of_xy_range(xlim, ylim):

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


        if enable_signal:
            for idx, ts in self.get_ts_set().signals.items():
                if ts.is_out_of_xy_range(xlim, ylim):
                    ts.hide_plot() 
                else:
                    ts.unhide_plot()

            for idx, tl in self.get_tl_set().signals.items():
                if tl.is_out_of_xy_range(xlim, ylim):
                    tl.hide_plot()
                else:
                    tl.unhide_plot()


        if enable_surface_marking:
            for idx, sm in self.get_sm_set().data.items():
                if sm.is_out_of_xy_range(xlim, ylim):
                    sm.hide_plot()
                else:
                    sm.unhide_plot()

        
        # plt.draw를 쓰면 동작하지 않는다.
        # 참조: https://stackoverflow.com/questions/30880358/matplotlib-figure-not-updating-on-data-change
        fig.canvas.draw()


    def set_absolute_bbox_for_plot(self, xlim, ylim):
        self.abs_xlim = xlim
        self.abs_ylim = ylim


    """Event Handler"""

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
            search_coord = np.array([event.xdata, event.ydata])
            
            # 선택된 객체 업데이트
            node = self.edit_core.select_func.update_selected_objects_using_node_snap(search_coord)
            
            # 화면 출력 업데이트 (Point)
            self._update_point_display(fig, ax)

            # 화면 출력 업데이트 (Line/Link)  
            # 선택한 point가 포함된 선을 표시해줌
            if self.selected_line_mark != None:
                for prev_selected_line in self.selected_line_mark:
                    prev_selected_line.remove()
            self.selected_line_mark = ax.plot(
                self.get_selected_line().points[:,0],
                self.get_selected_line().points[:,1],
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
        alt+s:  Save as JSON
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
        

        # 입력된 key 출력하기 (up/down 입력에 대해서는 생략)
        # if ('up' not in event.key) and ('down' not in event.key):
        print_trace('Key pressed: {}'.format(event.key))


        if event.key == 'ctrl+alt+d':
            print('[DEBUG] Entered Debug Mode')
            print('[DEBUG] Exiting Debug Mode')


        elif event.key == 'up' or event.key == 'down':
            if event.key == 'up':
                self.edit_core.select_func.update_selected_point(1)
            else:
                self.edit_core.select_func.update_selected_point(-1)
            
            self._update_point_display(fig, ax)   


        elif event.key == 'ctrl+up' or event.key == 'ctrl+down':
            if event.key == 'ctrl+up':
                self.edit_core.select_func.update_selected_point(5)
            else:
                self.edit_core.select_func.update_selected_point(-5)
            
            self._update_point_display(fig, ax)   



        elif event.key == 'shift+up' or event.key == 'shift+down':
            if event.key == 'shift+up':
                self.edit_core.select_func.update_selected_point(20)
            else:
                self.edit_core.select_func.update_selected_point(-20)
            
            self._update_point_display(fig, ax)   


        elif event.key == 'shift+ctrl+up' or event.key == 'shift+ctrl+down':
            if event.key == 'shift+ctrl+up':
                self.edit_core.select_func.update_selected_point(100)
            else:
                self.edit_core.select_func.update_selected_point(-100)
            
            self._update_point_display(fig, ax)   


        elif event.key == '1':
            """change edit_mode = Create Line Mode"""
            self.edit_core.set_multistep_edit_mode('create_line')
            # self.set_multistep_edit_mode('create_line')
            print_info('Edit mode enabled: {}'.format(self.edit_core.edit_func_desc))

        elif event.key == '0':
            """dijkstra mode"""
            self.edit_core.set_multistep_edit_mode('dijkstra')
            print_info('Edit mode enabled: {}'.format(self.edit_core.edit_func_desc))


        elif event.key == 'enter':
            """edit_mode ok"""
            print_trace('edit_mode ok')

            # [방식1] 하나의 함수로 edit_core에서 처리하는 방식
            # self.edit_core.edit_mode_ok()

            # [방식2] mode 별로 나누는 방식
            mode = self.edit_core.get_multistep_edit_mode()
            if mode == 'create_line':
                self.create_line_task_ok()
            elif mode == 'dijkstra':
                self.path_planning_task_ok()
            else:
                print_error('Undefined multistep edit mode')


        elif event.key == 'escape':
            """edit_mode cancel"""
            print_trace('edit_mode cancel')

            # [방식1] 하나의 함수로 edit_core에서 처리하는 방식
            # self.edit_core.edit_mode_cancel()

            # [방식2] mode 별로 나누는 방식
            mode = self.edit_core.get_multistep_edit_mode()
            if mode == 'create_line':
                self.create_line_task_cancel()
            elif mode == 'dijkstra':
                self.path_planning_task_cancel()
            else:
                print_error('Undefined multistep edit mode')
            

        elif event.key == 'ctrl+z':
            """undo"""
            print_trace('undo')


        elif event.key == 'delete':
            """delete selected instance"""
            self.delete_line_or_link_task()
            print_trace('delete selected instance')
            

        elif event.key == 'q':
            # mode 별로 나누는 방식
            mode = self.edit_core.get_multistep_edit_mode()
            if mode == 'create_line':
                self.create_line_task_set_start_point()
            elif mode == 'dijkstra':
                self.path_planning_task_set_start_point()
            else:
                print_error('Undefined multistep edit mode')


        elif event.key == 'w':
            # mode 별로 나누는 방식
            mode = self.edit_core.get_multistep_edit_mode()
            if mode == 'create_line':
                self.create_line_task_set_end_point()
            elif mode == 'dijkstra':
                self.path_planning_task_set_end_point()
            else:
                print_error('Undefined multistep edit mode')
        

        elif event.key == 'ctrl+s':
            self.save_mgeo()


        elif event.key == 'ctrl+l':
            self.load_mgeo()


        elif event.key == 'v':
            print_info('Update line & node plot')
            self.update_plot(fig, ax, draw=False)


        elif event.key == 'alt+v':
            self.toggle_node()            


        elif event.key == 'ctrl+v':
            self.toggle_signal()


        elif event.key == 'b' or event.key == 'B': # line bisection
            if self.get_selected_point() is None or self.selected_line_mark is None:
                print_error(' A point must be selected!')
                return
            if self.get_selected_point()['type'] == 'start' or self.get_selected_point()['type'] == 'end':
                print_error(' Cannot divide the line at an endpoint!')
                return


            # identify what line we're on
            line_to_remove = self.get_selected_line()
            line_type = type(line_to_remove).__name__ 

            to_node = line_to_remove.get_to_node()
            from_node = line_to_remove.get_from_node()


            # 


            # 새로운 노드 생성하기
            idx_point = self.get_selected_point()['idx_point'] 
            new_node = Node()
            new_node.point = line_to_remove.points[idx_point]


            # 타입에 맞게 새로운 Line/Link 생성한다
            if line_type == 'Line':
                # create two new lines
                new_to_line = Line()
                new_from_line = Line()
            elif line_type == 'Link':
                # create two new lines
                new_to_line = Link()
                new_from_line = Link()
            else:
                unexpected_type = type(line_to_remove)
                raise BaseException('[ERROR] Unexpected selected_line type: {}'.format(unexpected_type))
            
            # 포인트 설정 및 From/To Node 설정
            new_to_line.set_points(line_to_remove.points[idx_point:])
            new_from_line.set_points(line_to_remove.points[0:idx_point+1])

            new_to_line.set_to_node(to_node)
            new_to_line.set_from_node(new_node)
            new_from_line.set_to_node(new_node)
            new_from_line.set_from_node(from_node)

            # Link인 경우, 그 밖의 데이터를 가져온다
            if line_type == 'Link':
                Link.copy_attributes(line_to_remove, new_to_line)
                Link.copy_attributes(line_to_remove, new_from_line)


            # 기존 Line/Link 삭제
            to_node.remove_from_links(line_to_remove)
            from_node.remove_to_links(line_to_remove)
            self.get_line_set().remove_line(line_to_remove)

            # add new objects to set lists
            self.get_node_set().append_node(new_node, create_new_key=True)
            self.get_line_set().append_line(new_to_line, create_new_key=True)
            self.get_line_set().append_line(new_from_line, create_new_key=True)
            

            # delete old objects from set lists
            line_to_remove.erase_plot()           

            # clear selection markings from canvas
            ax.lines.remove(self.selected_point_mark[0])
            del self.selected_point_mark[0]
            self.annotation_text.remove()
            self.annotation_text = None           
            
            self.ref_points = self.get_line_set().get_ref_points()
            self.update_plot(fig, ax, draw=True)

            print_info('Line bisection complete')
    

        elif event.key == 'g':
            # 해당 link의 opendrive 변환을 위하여 geometry 정보를 지정
            if self.get_selected_point() is None or self.selected_line_mark is None:
                print_error(' A point must be selected!')
                return

            idx_point = self.get_selected_point()['idx_point']

            selected_link = self.get_selected_line()
            selected_link.add_geometry(idx_point, 'poly3')


        elif event.key == 'd':
            # 같은 위치에 있는 node fix
            overlapped_node_sets = error_fix.search_overlapped_node(self.get_node_set(), 0.1)
            nodes_of_no_use = error_fix.repair_overlapped_node(overlapped_node_sets)
            error_fix.delete_nodes_from_node_set(self.get_node_set(), nodes_of_no_use)


            # Djikstra 풀기
            # dijkstra_obj = Dijkstra(self.get_node_set().nodes, self.get_line_set().lines)
            # result, global_path = dijkstra_obj.find_shortest_path(start_node_id, end_node_id)
            

        elif event.key == 'h':
            # highlight를 쳐줘서 찾아준다 (line or link)
            # NOTE: 디버그 모드에서만 현재는 사용한다
            
            def _highlight_line(highlight_obj_idx_list):
                for idx in self.get_line_set().lines:
                    line = self.get_line_set().lines[idx]
                    
                    if line.idx in highlight_obj_idx_list:
                        line.set_vis_mode_manual_appearance(3, 'b')
                    else:
                        line.set_vis_mode_manual_appearance(1, 'k')
            
            def _highlight_node(highlight_obj_idx_list):
                for idx in self.get_node_set().nodes:
                    node = self.get_node_set().nodes[idx]

                    if node.idx in highlight_obj_idx_list:
                        node.set_vis_mode_manual_appearance(7, 'r', no_text=False)
                    else:
                        node.set_vis_mode_manual_appearance(3, 'g', no_text=True)

            # [사용 방법]
            ## _highlight_line(['A219BA000137'])
            ## _highlight_node(['A119BA000142'])

            # redraw
            self.update_plot(fig, ax, draw=True)


        elif event.key == 'alt+h':
            # reset highlight
            for var in self.get_line_set().lines:
                line = self.get_line_set().lines[var]
                line.reset_vis_mode_manual_appearance()

            for var in self.get_node_set().nodes:
                node = self.get_node_set().nodes[var]
                node.reset_vis_mode_manual_appearance()

            # redraw
            self.update_plot(fig, ax, draw=True)
        

    def on_scr_zoom(self, event):
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

    """View Control"""
    def set_all_text_view_off(self):
        self.enable_node_text = False
        for idx, node in self.get_node_set().nodes.items():
            node.vis_mode_no_text = True
        
        self.enable_signal_text = False
        for idx, ts in self.get_ts_set().signals.items():
            ts.vis_mode_no_text = True

        for idx, tl in self.get_tl_set().signals.items():
            tl.vis_mode_no_text = True
                
        self.enable_surface_marking_text = False
        for idx, sm in self.get_sm_set().data.items():
            sm.vis_mode_no_text = True


    def toggle_node(self):
        fig = plt.gcf()
        ax = plt.gca()

        print_info('Toggle node view')
            
        # Toggle
        self.enable_node = not self.enable_node

        # Then, update
        self.update_plot(fig, ax, draw=False)


    def toggle_node_text(self):
        fig = plt.gcf()
        ax = plt.gca()

        print_info('Toggle node text view')
            
        if self.enable_node_text:
            # 현재가 보여지는 상태였으면, hide 시켜야 한다.
            for idx, node in self.get_node_set().nodes.items():
                node.vis_mode_no_text = not self.enable_node_text   
                node.hide_text()

        else:
            # 현재가 숨겨진 상태였으면, unhide 시켜야 한다.
            for idx, node in self.get_node_set().nodes.items():
                node.vis_mode_no_text = not self.enable_node_text   
                node.unhide_text()

        # Toggle
        self.enable_node_text = not self.enable_node_text

        # Then, update
        self.update_plot(fig, ax, draw=False)


    def toggle_signal(self):
        fig = plt.gcf()
        ax = plt.gca()

        print_info('Toggle signal view')
        
        # Toggle
        self.enable_signal = not self.enable_signal

        # Then, update
        self.update_plot(fig, ax, draw=False)


    def toggle_signal_text(self):
        fig = plt.gcf()
        ax = plt.gca()

        print_info('Toggle signal text view')
        
        # Toggle
        self.enable_signal_text = not self.enable_signal_text


        for idx, ts in self.get_ts_set().signals.items():
            ts.vis_mode_no_text = not self.enable_signal_text

        for idx, tl in self.get_tl_set().signals.items():
            tl.vis_mode_no_text = not self.enable_signal_text

        # Then, update
        self.update_plot(fig, ax, draw=False)


    def toggle_surface_marking(self):
        fig = plt.gcf()
        ax = plt.gca()

        print_info('Toggle surface marking view')
        
        # Toggle
        self.enable_surface_marking = not self.enable_surface_marking

        for idx, sm in self.get_sm_set().data.items():
            sm.vis_mode_no_text = not self.enable_surface_marking

        # Then, update
        self.update_plot(fig, ax, draw=False)


    def toggle_surface_marking_text(self):
        fig = plt.gcf()
        ax = plt.gca()

        print_info('Toggle surface marking text view')
        
        # Toggle
        self.enable_surface_marking_text = not self.enable_surface_marking_text

        # Then, update
        self.update_plot(fig, ax, draw=False)

    """개별 동작에 대한 Functions : Create Line"""

    def create_line_task_set_start_point(self):
        """사용자가 start point를 선택할 때의 동작, start marker를 표시한다"""
        fig = plt.gcf()
        ax = plt.gca()

        if self.get_selected_node() == None:
            print_error(' A node must be selected!')
            return

        start_node = self.get_selected_node()
        self.edit_core.create_line_func.set_start_node(start_node)

        # update start node marker
        if self.marker_start_node != None and self.marker_start_node != []:
            ax.lines.remove(self.marker_start_node[0])
        
        x = start_node.point[0]
        y = start_node.point[1]
        self.marker_start_node = ax.plot(x, y,
            marker='o',
            markersize=15,
            color='b')
        fig.canvas.draw()
        print_info('Start point selected.')

    
    def create_line_task_set_end_point(self):
        """사용자가 end point를 선택할 때의 동작, end marker를 표시한다"""
        fig = plt.gcf()
        ax = plt.gca()

        if self.get_selected_node() == None:
            print_error('A node must be selected!')
            return

        end_node = self.get_selected_node()
        self.edit_core.create_line_func.set_end_node(end_node)

        # update end node marker
        if self.marker_end_node != None and self.marker_end_node != []:
            ax.lines.remove(self.marker_end_node[0])

        x = end_node.point[0]
        y = end_node.point[1]
        self.marker_end_node = ax.plot(x, y,
            marker='P',
            markersize=15,
            color='b')
        fig.canvas.draw()
        print_info('End point selected.')


    def create_line_task_ok(self):
        self.edit_core.create_line_func.do()

        self.clear_start_end_marker()

        fig = plt.gcf()
        ax = plt.gca()
        self.update_plot(fig, ax, draw=True)

        print_info('create_line task finished')
        pass


    def create_line_task_cancel(self):
        self.edit_core.create_line_func.cancel()

        self.clear_start_end_marker()

        fig = plt.gcf()
        ax = plt.gca()
        self.update_plot(fig, ax, draw=True)

        print_info('create_line task cancelled')
        pass

    """개별 동작에 대한 Functions : Delete Line/Link"""
    
    def delete_line_or_link_task(self):
        fig = plt.gcf()
        ax = plt.gca()

        selected_obj = self.get_selected_line()
        idx = selected_obj.idx

        # NOTE: 이렇게 type의 __name__으로 판별하는 이유: Link는 Line을 상속하기 때문에
        # isinstance(selected_obj, Link), isinstance(selected_obj, Line) 모두 True가 나오므로
        # isinstance로 구분이 불가능
        class_name = type(selected_obj).__name__
        if class_name == 'Line':
            task = self.edit_core.get_onestep_edit_task('delete_line')
            task.do(selected_obj)

        elif class_name == 'Link':
            task = self.edit_core.get_onestep_edit_task('delete_link')
            task.do(selected_obj)

        else:
            print_error('Undefine line-style object. (type of selected_obj: {})'.format(class_name))
            return

        # plot update
        selected_obj.erase_plot()

        ax.lines.remove(self.selected_line_mark[0])
        ax.lines.remove(self.selected_point_mark[0])
        del self.selected_line_mark[0]
        del self.selected_point_mark[0]
        self.annotation_text.remove()
        self.annotation_text = None

        self.update_plot(fig, ax, draw=True)

        # BUG
        # 라인 삭제 후, 연결되어있던 node는 삭제되지 않고 남아있는데 display되지 않는다

        print_info('delete line id = {} done'.format(idx))


    def delete_danling_nodes(self):
        """Danling Node 삭제하기"""
        dangling_nodes = error_fix.find_dangling_nodes(self.get_node_set())

        print_info('{} danling nodes are found and deleted'.format(len(dangling_nodes)))

        task = self.edit_core.get_onestep_edit_task('delete_node')
        task.do(dangling_nodes)

        # 삭제한 node를 GUI에서 지운다
        for node in dangling_nodes:
            node.erase_plot()

        # plot을 업데이트한다
        fig = plt.gcf()
        ax = plt.gca()
        self.update_plot(fig, ax, draw=False)


    def delete_objects_out_of_xy_range(self):
        # TODO(sglee): delete_all_using_xy_range_task 등으로 refactoring
        
        # 임시로 input은 고정
        # xlim = [8, 12]
        # ylim = [0, 50]

        # Kcity 의 경우
        # xlim = [440, 750]
        # ylim = [920, 1980]

        # Daegu Technopolis 에서의 값 (Origin 변경 전)
        xlim = plt.gca().get_xlim()
        ylim = plt.gca().get_ylim()

        # Seoul Sangam 에서의 값
        # xlim = [-90, 735]
        # ylim = [-445, 240]

        print_info('Delete objects out of the range x = [{}, {}], y = [{}, {}]'.format(xlim[0], xlim[1], ylim[0], ylim[1]))

        self.clear_current_plot()

        edit_mgeo_planner_map.delete_objects_out_of_xy_range(self.edit_core.mgeo_planner_map, xlim, ylim)

        # plot을 업데이트한다
        fig = plt.gcf()
        ax = plt.gca()
        self.update_plot(fig, ax, draw=True)


    def delete_object_inside_xy_range(self):
        xlim = plt.gca().get_xlim()
        ylim = plt.gca().get_ylim()

        print_info('Delete objects inside the range x = [{}, {}], y = [{}, {}]'.format(xlim[0], xlim[1], ylim[0], ylim[1]))

        self.clear_current_plot()

        edit_mgeo_planner_map.delete_object_inside_xy_range(self.edit_core.mgeo_planner_map, xlim, ylim)
        
        # plot을 업데이트한다
        fig = plt.gcf()
        ax = plt.gca()
        self.update_plot(fig, ax, draw=True)


    def __delete_link_and_dependent_objs(self, lines_to_remove):
        if len(lines_to_remove) == 0:
            print_warn('Nothing to delete')
            return

        # 첫번째 lines_to_remove의 item이 Line인지 Link인지 확인하고
        # 그에 따라 삭제하는데 사용할 Task를 가져온다
        class_name = type(lines_to_remove[0]).__name__
        if class_name == 'Line':
            task = self.edit_core.get_onestep_edit_task('delete_line')

        elif class_name == 'Link':
            task = self.edit_core.get_onestep_edit_task('delete_link')

        else:
            print_error('Undefine line-style object. (type of selected_obj: {})'.format(class_name))
            return
        task.do(lines_to_remove)

        # 삭제한 line을 GUI에서 지운다
        for line in lines_to_remove:
            line.erase_plot()


        """Danling Node 삭제하기"""
        dangling_nodes = error_fix.find_dangling_nodes(self.get_node_set())
        task = self.edit_core.get_onestep_edit_task('delete_node')
        task.do(dangling_nodes)
            

        # 삭제한 node를 GUI에서 지운다
        for node in dangling_nodes:
            node.erase_plot()


        """Selected Item 초기화"""


    """"""

    def find_and_fix_overlapped_node(self):
        fig = plt.gcf()
        ax = plt.gca()

        overlapped_node = error_fix.search_overlapped_node(self.get_node_set(), dist_threshold=0.2)
        nodes_to_delete = error_fix.repair_overlapped_node(overlapped_node)
        print_info('Overlapped Node Fixed ({} nodes will be deleted)'.format(len(nodes_to_delete)))

        for node in nodes_to_delete:
            node.erase_plot()
            self.get_node_set().remove_node(node)

        print_info('Starting to update plot ... ')
        self.update_plot(fig, ax, draw=False)
        print_info('find_and_fix_overlapped_node done OK. Plot update finished.')


    def simplify_lane_markings(self):
        print_info('simplify_lane_markings called')
        fig = plt.gcf()
        ax = plt.gca()

        simplify_candidate = list()

        for idx, node in self.get_node_set().nodes.items():
            # 현재 노드의 from_link, to_link가 1개씩만 존재하면 simplify 지점으로 입력
            if len(node.get_to_links()) == 1 and len(node.get_from_links()) == 1:
                
                # 또한, attribute가 같아야 한다!
                to_link = node.get_to_links()[0]
                from_link = node.get_from_links()[0]
                if from_link.is_every_attribute_equal(to_link):
                    simplify_candidate.append(node)

        print_info('{} nodes (out of total {}) will be deleted'.format(
            len(simplify_candidate),
            len(self.get_node_set().nodes.keys())))


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
            new_line = LaneBoundary()

            # 포인트 생성 시, from_link의 마지막점과, to_link의 시작점이 겹치므로 from_link에서 마지막 점을 제외시킨다
            new_line.set_points(np.vstack((current_node_from_link.points[:-1], current_node_to_link.points)))

            to_node = sc_node.get_to_nodes()[0]
            from_node = sc_node.get_from_nodes()[0]
            
            to_node.remove_from_links(current_node_to_link)
            from_node.remove_to_links(current_node_from_link)

            new_line.set_to_node(to_node)
            new_line.set_from_node(from_node)

            new_line.get_attribute_from(current_node_from_link)

            self.get_line_set().append_line(new_line, create_new_key=True)                       

            
            # 삭제되는 대상은 plot을 지우고, 새로운 대상은 plot을 그린다
            current_node_to_link.erase_plot()
            current_node_from_link.erase_plot()
            sc_node.erase_plot()
            new_line.draw_plot(ax)

            self.get_line_set().remove_line(current_node_to_link)
            self.get_line_set().remove_line(current_node_from_link)
            self.get_node_set().remove_node(sc_node)

        print_info('Starting to update plot ... ')
        self.update_plot(fig, ax, draw=False)
        print_info('Simplify operation done OK. Plot update finished.')

    """Path Planning"""

    def path_planning_task_set_start_point(self):
        """사용자가 start point를 선택할 때의 동작, start marker를 표시한다"""
        fig = plt.gcf()
        ax = plt.gca()

        if self.get_selected_node() == None:
            print_error(' A node must be selected!')
            return

        start_node = self.get_selected_node()
        self.edit_core.path_planning_using_dijkstra_func.set_start_node(start_node)

        # update start node marker
        if self.marker_start_node != None and self.marker_start_node != []:
            ax.lines.remove(self.marker_start_node[0])
        
        x = start_node.point[0]
        y = start_node.point[1]
        self.marker_start_node = ax.plot(x, y,
            marker='o',
            markersize=15,
            color='b')
        fig.canvas.draw()
        print_info('Start point selected.')        


    def path_planning_task_set_end_point(self):
        """사용자가 end point를 선택할 때의 동작, end marker를 표시한다"""
        fig = plt.gcf()
        ax = plt.gca()

        if self.get_selected_node() == None:
            print_error('A node must be selected!')
            return

        end_node = self.get_selected_node()
        self.edit_core.path_planning_using_dijkstra_func.set_end_node(end_node)

        # update end node marker
        if self.marker_end_node != None and self.marker_end_node != []:
            ax.lines.remove(self.marker_end_node[0])

        x = end_node.point[0]
        y = end_node.point[1]
        self.marker_end_node = ax.plot(x, y,
            marker='P',
            markersize=15,
            color='b')
        fig.canvas.draw()
        print_info('End point selected.')


    def path_planning_task_ok(self):
        result, path = self.edit_core.path_planning_using_dijkstra_func.do()

        print('path: {}'.format(path))

        self.clear_start_end_marker()

        fig = plt.gcf()
        ax = plt.gca()
        self.update_plot(fig, ax, draw=True)
        
        print_info('path_planning task finished')


    def path_planning_task_cancel(self):
        self.edit_core.path_planning_using_dijkstra_func.cancel()

        self.clear_start_end_marker()

        fig = plt.gcf()
        ax = plt.gca()
        self.update_plot(fig, ax, draw=True)
        
        print_info('path_planning task cancelled')
        

    """개별 동작에 대한 Functions: 차선 변경 링크 생성"""

    def create_lane_change_link_set(self, line_set):
        link_set = self.get_line_set()
        lane_ch_link_set = lane_change_link_creation.create_lane_change_link_auto_depth_using_length(
                link_set, method=1, min_length_for_lane_change=20)

        link_set = LineSet.merge_two_sets(link_set, lane_ch_link_set)
        self.edit_core.set_line(link_set)

        # 기존 링크 UI삭제 후 다시 그리기
        link_set.erase_plot()

        fig = plt.gcf()
        ax = plt.gca()
        self.update_plot(fig, ax, draw=True)

        print_info("Lane change links created")

    """MGeo Load/Save"""

    def load_mgeo(self):
        root_dir = file_io.get_proj_root_dir()
        init_load_path = os.path.join(root_dir, 'saved/') 
        init_load_path = os.path.normpath(init_load_path)
        print_trace('init_load_path: {}'.format(init_load_path))

        load_path = filedialog.askdirectory(
            initialdir = init_load_path, 
            title = 'Load files from') # defaultextension = 'json') 과 같은거 사용 가능    
        
        if load_path == '' or load_path == None:
            print_info('MGeo Load operation cancelled')
            return

        # 데이터 로드하기
        mgeo_planner_map = MGeo.create_instance_from_json(load_path)


        # NOTE: 다음은 Road Mesh 생성 시의 코드이다. 향후 해당 기능 다시 구현할 것
        # node_set, line_set, plane_set = mgeo_load.load(load_path, random_search=True)

        # line_set.set_vis_mode_all_different_color(vis_mode_all_different_color)
 
        # # 새로 로드한 node_set, line_set으로 변경
        # self.set_geometry_obj(line_set, node_set)
        # self.plane_set = plane_set

        # mgeo_planner_map 업데이트 전에 clear 시켜준다
        self.clear_current_plot()
        self.set_all_text_view_off()
        
        # Edit Core 업데이트
        self.edit_core.set_geometry_obj(mgeo_planner_map)
        
        print_info('Data is now imported. Starting to draw the first plot first...')

        fig = plt.gcf()
        ax = plt.gca()
        self.update_plot(fig, ax, draw=True)

        print_info('The first plot finished')

        print_info("MGeo data successfully loaded from: {}".format(load_path))


    def save_mgeo(self):
        root_dir = file_io.get_proj_root_dir()
        init_save_path = os.path.join(root_dir, 'saved/') 
        init_save_path = os.path.normpath(init_save_path)
        print_trace('init_save_path: {}'.format(init_save_path))
        
        save_path = filedialog.askdirectory(
            initialdir=init_save_path, 
            title='Select a folder to save MGeo data into')
        if save_path == '' or save_path == None:
            print('[ERROR] invalid save_path (your input: {})'.format(save_path))
            return

        self.edit_core.mgeo_planner_map.to_json(save_path)
        print_info("MGeo data successfully saved into: {}".format(save_path))


    def load_lane_marking_data(self):
        root_dir = file_io.get_proj_root_dir()
        init_load_path = os.path.join(root_dir, 'saved/') 
        init_load_path = os.path.normpath(init_load_path)
        print_trace('init_load_path: {}'.format(init_load_path))

        load_path = filedialog.askdirectory(
            initialdir = init_load_path, 
            title = 'Load files from') # defaultextension = 'json') 과 같은거 사용 가능    
        
        if load_path == '' or load_path == None:
            print_info('MGeo Load operation cancelled')
            return

        # filename = os.path.join(load_path, 'global_info.json')
        # with open(filename, 'r') as f:
        #     global_info = json.load(f)

        filename = os.path.join(load_path, 'node_set.json')
        with open(filename, 'r') as f:
            node_save_info_list = json.load(f)

        filename = os.path.join(load_path, 'lane_marking_set.json')
        with open(filename, 'r') as f:
            lane_marking_info_list = json.load(f)

        node_set = NodeSet()
        lane_boundary_set = LineSet()

        for save_info in node_save_info_list:
            idx = save_info['idx']
            point = save_info['point']

            node = Node(idx)
            node.point = np.array(point)

            node_set.append_node(node, create_new_key=False)

        for save_info in lane_marking_info_list:
            obj = LaneBoundary.from_dict(save_info, node_set)

            lane_marking_set.append_line(obj, create_new_key=False)

        mgeo_planner_map = MGeo(
            node_set=node_set, link_set=lane_marking_set)
        # mgeo_planner_map.set_origin(origin)

        # mgeo_planner_map 업데이트 전에 clear 시켜준다
        self.clear_current_plot()
        self.set_all_text_view_off()
        
        # Edit Core 업데이트
        self.edit_core.set_geometry_obj(mgeo_planner_map)
        
        print_info('Data is now imported. Starting to draw the first plot first...')

        fig = plt.gcf()
        ax = plt.gca()
        self.update_plot(fig, ax, draw=True)

        print_info('The first plot finished')

        print_info("MGeo lane marking data successfully loaded from: {}".format(load_path))
            

    # def save_lane_marking_data(self):
    #     root_dir = file_io.get_proj_root_dir()
    #     init_save_path = os.path.join(root_dir, 'saved/') 
    #     init_save_path = os.path.normpath(init_save_path)
    #     print_trace('init_save_path: {}'.format(init_save_path))
        
    #     save_path = filedialog.askdirectory(
    #         initialdir=init_save_path, 
    #         title='Select a folder to save MGeo data into')
    #     if save_path == '' or save_path == None:
    #         print('[ERROR] invalid save_path (your input: {})'.format(save_path))
    #         return

    #     self.edit_core.mgeo_planner_map.to_json(save_path)
    #     print_info("MGeo data successfully saved into: {}".format(save_path))


    """데이터 Import"""

    def import_ngii_shp1_lane_marking(self):
        root_dir = file_io.get_proj_root_dir()
        init_import_path = os.path.join(root_dir, 'rsc/map_data/') 
        init_import_path = os.path.normpath(init_import_path)
        print_trace('init_import_path: {}'.format(init_import_path))

        input_path = filedialog.askdirectory(
            initialdir=init_import_path,
            title='Select a folder that contains CODE42 HDMap data')
        if (input_path == '' or input_path == None):
            print_error('invalid input_path (your input: {})'.format(input_path))
            return

        mgeo_planner_map = ngii_shp1_to_mgeo.import_lane_marking_data(input_path)

        # mgeo_planner_map 업데이트 전에 clear 시켜준다
        self.clear_current_plot()
        self.set_all_text_view_off()

        # Edit Core 업데이트
        self.edit_core.set_geometry_obj(mgeo_planner_map)

        # print_info('Do: Find & Fix Overlapped Node first')
        # self.find_and_fix_overlapped_node()

        # print_info('Data is now imported. Starting to draw the first plot first...')

        # 새로 Plot하기
        fig = plt.gcf()
        ax = plt.gca()
        self.update_plot(fig, ax, draw=True)

        print_info('The first plot finished')

        print_info('NGII SHP (ver1) lane marking data imported from: {}'.format(input_path))


    def import_ngii_shp1(self):
        # NOTE: 고정된 테스트 데이터 로드 시
        # input_path = '../../rsc/map_data/code42_shp_yangjae/'
        # input_path = os.path.join(current_path, input_path)
        # input_path = os.path.normpath(input_path)

        root_dir = file_io.get_proj_root_dir()
        init_import_path = os.path.join(root_dir, 'rsc/map_data/') 
        init_import_path = os.path.normpath(init_import_path)
        print_trace('init_import_path: {}'.format(init_import_path))

        input_path = filedialog.askdirectory(
            initialdir=init_import_path,
            title='Select a folder that contains ngii shp1 data')
        if (input_path == '' or input_path == None):
            print_error('invalid input_path (your input: {})'.format(input_path))
            return

        mgeo_planner_map = ngii_shp1_to_mgeo.import_all_data(input_path)

        # mgeo_planner_map 업데이트 전에 clear 시켜준다
        self.clear_current_plot()
        self.set_all_text_view_off()

        # Edit Core 업데이트
        self.edit_core.set_geometry_obj(mgeo_planner_map)

        print_info('Data is now imported. Starting to draw the first plot first...')

        # 새로 Plot하기
        fig = plt.gcf()
        ax = plt.gca()
        self.update_plot(fig, ax, draw=True)

        print_info('The first plot finished')

        print_info('NGII SHP (ver2) data is imported from: {}'.format(input_path))

    def import_ngii_shp2(self):
        # NOTE: 고정된 테스트 데이터 로드 시
        # input_path = '../../rsc/map_data/code42_shp_yangjae/'
        # input_path = os.path.join(current_path, input_path)
        # input_path = os.path.normpath(input_path)

        root_dir = file_io.get_proj_root_dir()
        init_import_path = os.path.join(root_dir, 'rsc/map_data/') 
        init_import_path = os.path.normpath(init_import_path)
        print_trace('init_import_path: {}'.format(init_import_path))

        input_path = filedialog.askdirectory(
            initialdir=init_import_path,
            title='Select a folder that contains CODE42 HDMap data')
        if (input_path == '' or input_path == None):
            print_error('invalid input_path (your input: {})'.format(input_path))
            return

        mgeo_planner_map = ngii_shp2_to_mgeo.import_all_data(input_path)

        # mgeo_planner_map 업데이트 전에 clear 시켜준다
        self.clear_current_plot()
        self.set_all_text_view_off()

        # Edit Core 업데이트
        self.edit_core.set_geometry_obj(mgeo_planner_map)

        print_info('Data is now imported. Starting to draw the first plot first...')

        # 새로 Plot하기
        fig = plt.gcf()
        ax = plt.gca()
        self.update_plot(fig, ax, draw=True)

        print_info('The first plot finished')

        print_info('NGII SHP (ver2) data is imported from: {}'.format(input_path))


    def import_code42_hdmap(self):

        root_dir = file_io.get_proj_root_dir()
        init_import_path = os.path.join(root_dir, 'rsc/map_data/') 
        init_import_path = os.path.normpath(init_import_path)
        print_trace('init_import_path: {}'.format(init_import_path))

        input_path = filedialog.askdirectory(
            initialdir=init_import_path,
            title='Select a folder that contains CODE42 HDMap data')
        if (input_path == '' or input_path == None):
            print_error('invalid input_path (your input: {})'.format(input_path))
            return

        importer = hdmap_42dot_importer.HDMap42dotImporter()

        mgeo_planner_map = importer.import_shp_geojson(input_path)

        # mgeo_planner_map 업데이트 전에 clear 시켜준다
        self.clear_current_plot()

        # Edit Core 업데이트
        self.edit_core.set_geometry_obj(mgeo_planner_map)

        # 새로 Plot하기
        fig = plt.gcf()
        ax = plt.gca()
        self.update_plot(fig, ax, draw=True)

        print_info('CODE42 data is imported from: {}'.format(input_path))

    def import_geojson(self):
        
        mgeo_planner_map = load_stryx_lane()

        # mgeo_planner_map 업데이트 전에 clear 시켜준다
        self.clear_current_plot()

        # Edit Core 업데이트
        self.edit_core.set_geometry_obj(mgeo_planner_map)

        # 새로 Plot하기
        fig = plt.gcf()
        ax = plt.gca()
        self.update_plot(fig, ax, draw=True)

        print_info('GeoJson data is imported')

    """데이터 Export"""
    
    def export_map_build_data_all(self):
        root_dir = file_io.get_proj_root_dir()
        init_save_path = os.path.join(root_dir, 'saved/') 
        init_save_path = os.path.normpath(init_save_path)
        print_trace('init_save_path: {}'.format(init_save_path))
        
        save_path = filedialog.askdirectory(
            initialdir=init_save_path, 
            title='Select a folder to save map build data into')
        if save_path == '' or save_path == None:
            print('[ERROR] invalid save_path (your input: {})'.format(save_path))
            return

        morai_sim_build_data_exporter.export_ts(
            save_path, self.get_ts_set(), self.get_line_set())
        
        print_info('Traffic signs exported to {}'.format(save_path))

        morai_sim_build_data_exporter.export_tl(
            save_path, self.get_tl_set(), self.get_line_set())

        print_info('Traffic lights exported to {}'.format(save_path))

        morai_sim_build_data_exporter.export_sm(
            save_path, self.get_sm_set(), self.get_line_set())

        print_info('Surface markings exported to {}'.format(save_path))


    def export_map_build_data_ts(self):
        root_dir = file_io.get_proj_root_dir()
        init_save_path = os.path.join(root_dir, 'saved/') 
        init_save_path = os.path.normpath(init_save_path)
        print_trace('init_save_path: {}'.format(init_save_path))
        
        save_path = filedialog.askdirectory(
            initialdir=init_save_path, 
            title='Select a folder to save map build data into')
        if save_path == '' or save_path == None:
            print('[ERROR] invalid save_path (your input: {})'.format(save_path))
            return

        morai_sim_build_data_exporter.export_ts(
            save_path, self.get_ts_set(), self.get_line_set())

        print_info('Traffic signs exported to {}'.format(save_path))


    def export_map_build_data_tl(self):
        root_dir = file_io.get_proj_root_dir()
        init_save_path = os.path.join(root_dir, 'saved/') 
        init_save_path = os.path.normpath(init_save_path)
        print_trace('init_save_path: {}'.format(init_save_path))
        
        save_path = filedialog.askdirectory(
            initialdir=init_save_path, 
            title='Select a folder to save map build data into')
        if save_path == '' or save_path == None:
            print('[ERROR] invalid save_path (your input: {})'.format(save_path))
            return

        morai_sim_build_data_exporter.export_tl(
            save_path, self.get_tl_set(), self.get_line_set())

        print_info('Traffic lights exported to {}'.format(save_path))


    def export_map_build_data_sm(self):
        root_dir = file_io.get_proj_root_dir()
        init_save_path = os.path.join(root_dir, 'saved/') 
        init_save_path = os.path.normpath(init_save_path)
        print_trace('init_save_path: {}'.format(init_save_path))

        save_path = filedialog.askdirectory(
            initialdir=init_save_path, 
            title='Select a folder to save map build data into')
        if save_path == '' or save_path == None:
            print('[ERROR] invalid save_path (your input: {})'.format(save_path))
            return

        morai_sim_build_data_exporter.export_sm(
            save_path, self.get_sm_set(), self.get_line_set())

        print_info('Surface markings exported to {}'.format(save_path))

    """Mesh Export"""


    def export_lane_mesh(self):
        """lane instance 각각을 파일로 출력하는 방법"""
        print_info('export_lane_mesh called')

        root_dir = file_io.get_proj_root_dir()
        init_save_path = os.path.join(root_dir, 'saved/') 
        init_save_path = os.path.normpath(init_save_path)
        print_trace('init_save_path: {}'.format(init_save_path))
        
        save_path = filedialog.askdirectory(
            initialdir=init_save_path, 
            title='Select a folder to save lane_mesh into')
        if save_path == '' or save_path == None:
            print('[ERROR] invalid save_path (your input: {})'.format(save_path))
            return

        for idx, lane in self.get_line_set().lines.items():
            if lane.lane_type != 502: # 유턴 구역선
                continue

            file_name = 'w_misc_u_turn_marking_{}'.format(idx)
            vertices, faces = lane.create_mesh_gen_points()

            poly_obj = make_road(vertices, faces)

            file_name = os.path.normpath(os.path.join(save_path, file_name))  
            write_obj(poly_obj, file_name)


                
    def export_lane_mesh2(self):
        print_info('export_lane_mesh called')

        root_dir = file_io.get_proj_root_dir()
        init_save_path = os.path.join(root_dir, 'saved/') 
        init_save_path = os.path.normpath(init_save_path)
        print_trace('init_save_path: {}'.format(init_save_path))
        
        save_path = filedialog.askdirectory(
            initialdir=init_save_path, 
            title='Select a folder to save lane_mesh into')
        if save_path == '' or save_path == None:
            print('[ERROR] invalid save_path (your input: {})'.format(save_path))
            return

        vertex_face_sets = dict()

        # TODO: 여기 구현해서 넣어야 함
        for idx, lane in self.get_line_set().lines.items():
            
            # 파일 이름 생성
            if lane.lane_type == 530: # 정지선
                file_name = 'w_misc_stop_line'
            elif lane.lane_type == 525: # 교차로 내 유도선
                file_name = 'w_misc_intersection_guide_line'
            elif lane.lane_type == 502: # 유턴 구역선
                file_name = 'w_misc_u_turn_marking'
            else:
                if lane.get_lane_num() == 1:
                    file_name = '{}_{}'.format(lane.lane_color[0], lane.lane_shape[0])
                else:
                    file_name = '{}_{}_{}'.format(lane.lane_color[0], lane.lane_shape[0], lane.lane_shape[1])
            
            # 해당 lane의 vertex, faces를 계산
            vertices, faces = lane.create_mesh_gen_points()

            # 해당 파일 이름으로 구성된 vertex_face_set에 추가한다
            if file_name in vertex_face_sets.keys():
                vertex_face = vertex_face_sets[file_name]

                exiting_num_vertices = len(vertex_face['vertex'])

                # 그 다음, face는 index 번호를 변경해주어야 한다
                faces = np.array(faces) # 상수를 쉽게 더하기 위해서 np array로 변경한다
                faces += exiting_num_vertices # vertex 리스트의 index가, 기존 vertex의 개수만큼 밀리게 되므로 이렇게 더해준다
                
                # 둘 다 리스트이므로, +로 붙여주면 된다.
                vertex_face['vertex'] += vertices # 그냥 리스트이므로 이렇게 붙여준다
                vertex_face['face'] += faces.tolist()
                vertex_face['cnt'] += 1

            else:
                vertex_face_sets[file_name] = {'vertex': vertices, 'face': faces, 'cnt':1}


        for file_name, vertex_face in vertex_face_sets.items():
            print('file: {}, num of lane objects: {}'.format(file_name, vertex_face['cnt']))
            file_name = os.path.normpath(os.path.join(save_path, file_name))  

            mesh_gen_vertices = vertex_face['vertex']
            mesh_gen_vertex_subsets_for_each_face = vertex_face['face']

            poly_obj = make_road(mesh_gen_vertices, mesh_gen_vertex_subsets_for_each_face)
            write_obj(poly_obj, file_name)

        print_info('export_lane_mesh done OK')

    """ MGeo 수정 """

    def change_origin(self):
        # TODO(sglee): refactor & new_origin 이 argument가 되도록
        # edit_core쪽에서 mgeo_planner_map instance를 가지고 있으면
        # 해당 기능을 mgeo planner map 쪽에서 제공하면 된다. 

        # KCity에서의 Origin 
        # new_origin = np.array([302459.942, 4122635.537, 28.991])

        # Daegu Technopolis에서의 Origin
        # new_origin = np.array([451140.341000, 3947642.281000, 70.125000])

        # 판교맵에서의 Origin
        new_origin = np.array([209402.0923992687, 533433.0495021925, 39.684636742713245])

        old_origin = self.edit_core.get_origin()

        new_origin_str = '[{:.6f}, {:.6f}, {:.6f}]'.format(new_origin[0], new_origin[1], new_origin[2])
        old_origin_str = '[{:.6f}, {:.6f}, {:.6f}]'.format(old_origin[0], old_origin[1], old_origin[2])
        print_info('Origin will be changed from {} to {}'.format(old_origin_str, new_origin_str))

        edit_mgeo_planner_map.change_origin(
            self.edit_core.mgeo_planner_map, new_origin, retain_global_position=True)

        # 기존에 있던 node_set, line_set 정리
        self.clear_current_plot()

        print_info('Updating plot after changing origin...')
        # 다시 그리기
        fig = plt.gcf()
        ax = plt.gca()
        self.update_plot(fig, ax, draw=True)
        print_info('change_origin finished')


    def fill_points_in_links(self):
        # TODO(sglee): step_len을 argument가 되도록
        step_len = 0.5

        for idx, link in self.get_line_set().lines.items():
            if not link.is_it_for_lane_change():        
                link.fill_in_points_evenly(step_len)
        
        # 다시 그리기
        fig = plt.gcf()
        ax = plt.gca()
        self.update_plot(fig, ax, draw=True)


    def fill_points_in_lane_markings(self):
        step_len = 0.1

        for idx, lane in self.get_line_set().lines.items():
            lane.fill_in_points_evenly(step_len)
        
        self.clear_current_plot()
        
        # 다시 그리기
        fig = plt.gcf()
        ax = plt.gca()
        self.update_plot(fig, ax, draw=True)


    """ 임시 코드 """
    def import_pangyo_aict_and_ngii_shp2(self):
        
        root_dir = file_io.get_proj_root_dir()
        aict_path = os.path.normpath(os.path.join(root_dir, 'rsc/map_data/aict_shp_pangyo/1st2ndIntg_TM_Mid'))
        
        ngii_utm52n_path = os.path.normpath(os.path.join(root_dir, 'rsc/map_data/ngii_shp2_Seongnam_Pangyo/SEC01_UTM52N_ElipsoidHeight'))
        ngii_utmk_path = os.path.normpath(os.path.join(root_dir, 'rsc/map_data/ngii_shp2_Seongnam_Pangyo/SEC01_UTMK_OrthometricHeight'))

        aict = ngii_shp1_to_mgeo.import_all_data(aict_path, origin_node_id='204G02980402')        
        
        # 우선 UTM52N이 Ellipsoid height인데, 이를 UTM52N의 orthometric height로 변환한다.
        # 이는 UTMK Orthometric height 데이터를 그냥 이용하는 것으로 한다.

        ngii_utm52n = ngii_shp2_to_mgeo.import_all_data(ngii_utm52n_path, origin_node_id='A119AS305283')
        ngii_utmk = ngii_shp2_to_mgeo.import_all_data(ngii_utmk_path, origin_node_id='A119AS305283')
        
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
        aict_origin_node_global = aict.node_set.nodes['204G02980402'].point + aict.get_origin() 
        ngii_origin_node_global = ngii.node_set.nodes['A119AS305283'].point + ngii.get_origin()


        """여기가 ngii 데이터의 변환용"""
        src_origin = ngii.get_origin()
        dst_origin = trans.TransformPoint(src_origin[0], src_origin[1], src_origin[2])
        dst_origin = np.array(dst_origin)
        ngii.set_origin(dst_origin)        
        
        for idx, node in ngii.node_set.nodes.items():
            utm52n_global = node.point + src_origin
            tm_mid_global = trans.TransformPoint(utm52n_global[0], utm52n_global[1], utm52n_global[2])
            node.point = np.array(tm_mid_global) - dst_origin

        for idx, link in ngii.link_set.lines.items():
            points = list()
            for point in link.points:
                utm52n_global = point + src_origin
                tm_mid_global = trans.TransformPoint(utm52n_global[0], utm52n_global[1], utm52n_global[2])
                points.append(tm_mid_global)
            link.point = np.array(points)


        root_dir = file_io.get_proj_root_dir()
        init_save_path = os.path.join(root_dir, 'saved/') 
        init_save_path = os.path.normpath(init_save_path)
        print_trace('init_save_path: {}'.format(init_save_path))
        
        save_path = filedialog.askdirectory(
            initialdir=init_save_path, 
            title='Select a folder to save MGeo data into')
        if save_path == '' or save_path == None:
            print('[ERROR] invalid save_path (your input: {})'.format(save_path))
            return

        ngii.to_json(save_path)
        print_info("MGeo data successfully saved into: {}".format(save_path))

        print('[INFO] successfully read two file sets')


def print_info(msg):
    print('[INFO]', msg)

def print_warn(msg):
    print('[WARN] ', msg)

def print_error(msg):
    print('[ERROR]', msg)

def print_trace(msg):
    print('[TRACE]', msg)

def print_debug(mag):
    print('[DEBUG] ', msg)

