import os
import sys

from lib.command_manager.concrete_commands import DeleteMgeoItem, FixDanglingLinks, FixDanglingLanes, FixSignalRoadConnection, RepairOverlappedNode

current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))
sys.path.append(os.path.normpath(os.path.join(current_path, '../../')))

import traceback
import copy
import numpy as np

from PyQt5 import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from lib.mgeo.class_defs import *
# from lib.mgeo.class_defs import lane_boundary_set, mgeo, mgeo_map_planner
from lib.mgeo.class_defs.mgeo_item import MGeoItem
from lib.mgeo.edit.funcs import edit_node, edit_link, edit_lane_boundary, edit_signal, edit_junction, edit_mgeo_planner_map
from lib.mgeo.utils import error_fix
from lib.common.logger import Logger
from lib.widget.select_node_type_window import SelectNodeTypeWindow
from lib.widget.select_line_type_window import SelectLineTypeWindow
from lib.widget.select_link_dist_threshold_window import SelectLinkThresholdWindow

from GUI.feature_sets_base import BaseFeatureSet
from GUI.feature_sets_ngii2_fix import ChangeNgiitoMGeoWidget, ChangeNgiitoMGeo
from GUI.feature_sets_intersection_region import *

# [SHJ]
from collections import OrderedDict

class ErrorFix(BaseFeatureSet):
    """
    Guidelines
    - Find Function
        1. Define data type
        2. Search for data (through error_fix if necessary)
        3. Create string output
        4. Contingency for no results from step 2
        5. Determine enabling clear/repair actions
    - Repair/Delete Function
        1. Take results from the find function
        2. Act on the data (through error_fix if necessary)
        3. Reset canvas variables and UI variables
        4. Create string output for logging
    All functions should follow try/exception pattern
    """
    def __init__(self, canvas):
        super(ErrorFix, self).__init__(canvas)
        # overlapped_node_set
        self.overlapped_node_type = MGeoItem.NODE
        self.overlapped_node = []

        # dangling_nodes_set
        self.dangling_node_type = MGeoItem.NODE
        self.dangling_nodes = []

        # end_nodes_set
        self.end_nodes = []

        # duplicated_line
        self.duplicated_lane = dict()

        # closed-loop link
        self.closed_loop_link_type = MGeoItem.LINK
        self.closed_loop_links = []

        # short_link_set
        self.short_link_set = []
        self.link_dist_threshold = 0


    def find_short_link(self, act_repair, act_clear):
        Logger.log_trace('Called: find_short_link')
        try:
            link_threshold_window = SelectLinkThresholdWindow()
            return_link_threshold = link_threshold_window.showDialog()

            if return_link_threshold != 1:
                return
            else:
                self.link_dist_threshold = float(link_threshold_window.dist_threshold.text())
                link_set = self.getLinkSet()
                link_type = MGeoItem.LINK
                        
            self.short_link = error_fix.find_short_link(link_set, self.link_dist_threshold)
            
            link_idx_string = '['
            for short_link in self.short_link:
                self.canvas.list_error.append({'type': link_type, 'id': short_link.idx})
                link_idx_string += '{}, '.format(short_link.idx)
            link_idx_string += ']'
            Logger.log_info('find_short_link result: {}'.format(link_idx_string))

            if self.short_link is None or self.short_link == []:  
                QMessageBox.information(self.canvas, "Information", "No short links were found.")
                act_repair.setDisabled(True)
                if self.canvas.list_highlight1 == []:
                    act_clear.setDisabled(True)
            else:
                act_repair.setDisabled(False)
                act_clear.setDisabled(False)

        except BaseException as e:
            Logger.log_error('find_short_link failed (traceback is down below) \n{}'.format(traceback.format_exc()))
    
    
    def repair_short_link(self, act_repair):
        Logger.log_trace('Called: repair_short_link')
        try:
            node_set = self.getNodeSet()
            link_set = self.getLinkSet()
            lane_node_set = self.canvas.getLaneNodeSet()
            lane_link_set = self.canvas.getLaneBoundarySet()

            short_link_list, nodes_of_no_use = error_fix.repair_short_link(self.short_link, link_set)
            # short_lane_of_no_use_right, lane_nodes_of_no_use_right = error_fix.repair_short_lane_mark_right(self.short_link, self.link_dist_threshold)
            # short_lane_of_no_use_left, lane_nodes_of_no_use_left = error_fix.repair_short_lane_mark_left(self.short_link, self.link_dist_threshold)
            
            for link in short_link_list:
                edit_link.delete_link(link_set, link)

            edit_node.delete_nodes(node_set, nodes_of_no_use)

            # for node_of_short_link in nodes_of_no_use:
            #     try:
            #         node_set.remove_node(node_of_short_link)
            #     except:
            #         pass
            #     #edit_node.delete_node(node_set, node_of_short_link.point)
            # for short_link in short_link_list:
            #     link_set.remove_line(short_link)
            
            # for node_of_short_link_right in lane_nodes_of_no_use_right:
            #     try:
            #         lane_node_set.remove_node(node_of_short_link_right)
            #     except:
            #         print('already removed')
            #     # edit_node.delete_nodes(lane_node_set, lane_nodes_of_no_use_right)
            #     #edit_node.delete_node(node_set, node_of_short_link.point)
            # for short_lane_mark_right in short_lane_of_no_use_right:
            #     try:
            #         lane_link_set.remove_line(short_lane_mark_right)
            #     except:
            #         print('already removed')
            # for node_of_short_link_left in lane_nodes_of_no_use_left:
            #     try:
            #         lane_node_set.remove_node(node_of_short_link_left)
            #     except:
            #         print('already removed')
            #     # edit_node.delete_nodes(lane_node_set, lane_nodes_of_no_use_left)
            #     #edit_node.delete_node(node_set, node_of_short_link.point)
            # for short_lane_mark_left in short_lane_of_no_use_left:
            #     try:
            #         lane_link_set.remove_line(short_lane_mark_left)
            #     except:
            #         print('already removed')

            # reset canvas and UI
            self.canvas.list_error.clear()
            self.short_link = []
            act_repair.setDisabled(True)
            self.canvas.updateMgeoIdWidget()
            
            delete_node_string = '['
            for node in nodes_of_no_use:
                delete_node_string += '{}, '.format(node.idx)
            delete_node_string += ']'
            Logger.log_info('short_link nodes result: {}'.format(delete_node_string))

            link_idx_string = '['
            for i in short_link_list:
                link_idx_string += '{}, '.format(i.idx)
            link_idx_string += ']'
            Logger.log_info('short_links deleted: {}'.format(link_idx_string))
            Logger.log_info('repair_short_link completed')
        
        except BaseException as e:
            Logger.log_error('repair_short_link failed (traceback is down below) \n{}'.format(traceback.format_exc()))


    def find_overlapped_node(self, act_repair, act_clear):
        Logger.log_trace('Called: find_overlapped_node')
        try:
            node_type_window = SelectNodeTypeWindow()
            return_node_type = node_type_window.showDialog()
                      
            if return_node_type != 1:
                return
            else:
                dist_threshold = float(node_type_window.dist_threshold.text())
                if node_type_window.node.isChecked():
                    node_set = self.getNodeSet()
                    node_type = MGeoItem.NODE
                else:
                    node_set = self.canvas.getLaneNodeSet()
                    node_type = MGeoItem.LANE_NODE
            
            if node_set is None or len(node_set.nodes) < 1 :
                QMessageBox.warning(self.canvas, "Warning", "No node data loaded.")
                return

            self.overlapped_node = error_fix.search_overlapped_node(node_set, dist_threshold)
            self.overlapped_node_type = node_type
            
            node_idx_string = '['
            for i in self.overlapped_node:
                for n in i:
                    self.canvas.list_error.append({'type': node_type, 'id': n.idx})
                    node_idx_string += '{}, '.format(n.idx)
            node_idx_string += ']'
            Logger.log_info('find_overlapped_node result: {}'.format(node_idx_string))

            # overlapped_nodes에 node 유무에 따라 (repair_overlapped_node) menu action enable
            if self.overlapped_node is None or self.overlapped_node == []:
                QMessageBox.information(self.canvas, "Information", "No overlapped nodes were found.")
                act_repair.setDisabled(True)
                if (self.dangling_nodes is None or self.dangling_nodes == []) and self.canvas.list_highlight1 == []:
                    act_clear.setDisabled(True)
            else:
                act_repair.setDisabled(False)
                act_clear.setDisabled(False)

        except BaseException as e:
            Logger.log_error('find_overlapped_node failed (traceback is down below) \n{}'.format(traceback.format_exc()))
            

    def repair_overlapped_node(self, act_repair):
        Logger.log_trace('Called: repair_overlapped_node')
        try:
            if self.overlapped_node_type == MGeoItem.LANE_NODE:
                node_type = MGeoItem.LANE_NODE
            else:
                node_type = MGeoItem.NODE

            if len(self.overlapped_node) < 1:
                QMessageBox.warning(self.canvas, "Warning", "There are no overlapped nodes to repair.")
                return
            cmd_repair_overlapped_node = RepairOverlappedNode(self.canvas, self.overlapped_node, node_type)
            self.canvas.command_manager.execute(cmd_repair_overlapped_node)
            
            # 불필요한 노드가 삭제되었으면 error list를 clear 시켜준다
            self.overlapped_node = []
            act_repair.setDisabled(True)

        except BaseException as e:
            Logger.log_error('repair_overlapped_node failed (traceback is down below) \n{}'.format(traceback.format_exc()))


    def find_dangling_nodes(self, act_repair, act_clear):
        Logger.log_trace('Called: find_dangling_nodes')
        try:
            node_type_window = SelectNodeTypeWindow(threshold=False)
            return_node_type = node_type_window.showDialog()

            if return_node_type != 1:
                return
            else:
                if node_type_window.node.isChecked():
                    node_set = self.getNodeSet()
                    node_type = MGeoItem.NODE
                else:
                    node_set = self.canvas.getLaneNodeSet()
                    node_type = MGeoItem.LANE_NODE

            if node_set is None or len(node_set.nodes) < 1 :
                QMessageBox.warning(self.canvas, "Warning", "No node data loaded.")
                return

            self.dangling_nodes = error_fix.find_dangling_nodes(node_set)

            for node in self.dangling_nodes:
                self.canvas.list_error.append({'type': node_type, 'id': node.idx})

            node_idx_string = '['
            for node in self.dangling_nodes:
                node_idx_string += '{}, '.format(node.idx)
            node_idx_string += ']'
            Logger.log_info('find_dangling_nodes result: {}'.format(node_idx_string))
            self.dangling_node_type = node_type

            # dangling_nodes에 node 유/무에 따라 (delete_dangling_nodes) menu action enable
            if self.dangling_nodes is None or self.dangling_nodes == []:
                QMessageBox.information(self.canvas, "Information", "No dangling nodes were found.")
                act_repair.setDisabled(True)
                if self.overlapped_node is None or self.overlapped_node == []:
                    act_clear.setDisabled(True)
            else:
                act_repair.setDisabled(False)
                act_clear.setDisabled(False)
        
        except BaseException as e:
            Logger.log_error('find_dangling_nodes failed (traceback is down below) \n{}'.format(traceback.format_exc()))


    def delete_dangling_nodes(self, act_repair):
        Logger.log_trace('Called: delete_dangling_nodes')
        try:
            if self.dangling_node_type == MGeoItem.LANE_NODE:
                node_type = MGeoItem.LANE_NODE
            else:
                node_type = MGeoItem.NODE

            items = list()
            node_idx_string = '['
            for node in self.dangling_nodes:
                node_idx_string += '{}, '.format(node.idx)
                item = {'id':node.idx, 'type':node_type}
                items.append(item)
            node_idx_string += ']'

            cmd_delete_dangling_node = DeleteMgeoItem(self.canvas, items)
            self.canvas.command_manager.execute(cmd_delete_dangling_node)

            act_repair.setDisabled(True)
            Logger.log_info('dangling nodes ({}) deleted.'.format(node_idx_string))
        
        except BaseException as e:
            Logger.log_error('delete_item failed (traceback is down below) \n{}'.format(traceback.format_exc()))


    def find_end_nodes(self, act_clear):
        Logger.log_trace('Called: find_end_nodes')
        try:
            node_type_window = SelectNodeTypeWindow(threshold=False)
            return_node_type = node_type_window.showDialog()

            if return_node_type != 1:
                return
            else:
                if node_type_window.node.isChecked():
                    node_set = self.getNodeSet()
                    node_type = MGeoItem.NODE
                else:
                    node_set = self.canvas.getLaneNodeSet()
                    node_type = MGeoItem.LANE_NODE

            if node_set is None or len(node_set.nodes) < 1:
                QMessageBox.warning(self.canvas, "Warning", "No node data loaded.")
                return

            self.end_nodes = error_fix.find_end_nodes(node_set)
            for node in self.end_nodes:
                self.canvas.list_error.append({'type': node_type, 'id': node.idx})

            node_idx_string = '['
            for node in self.end_nodes:
                node_idx_string += '{}, '.format(node.idx)
            node_idx_string += ']'
            Logger.log_info('find_end_nodes result: {}'.format(node_idx_string))

            if self.end_nodes is None or self.end_nodes == []:
                pass
            else:
                act_clear.setDisabled(False)

        except BaseException as e:
            Logger.log_error('find_end_nodes failed (traceback below)\n{}'.format(traceback.format_exc()))


    def find_dangling_links(self, act_find, act_clear, action_fix):
        Logger.log_trace('Called: find_dangling_links')
        try:
            line_set = None
            line_type = MGeoItem.LINK

            line_type_window = SelectLineTypeWindow()
            return_line_type = line_type_window.showDialog()

            if return_line_type != 1:
                return
            else:
                if line_type_window.link.isChecked():
                    line_set = self.getLinkSet()
                    line_type = MGeoItem.LINK
                else:
                    line_set = self.canvas.getLaneBoundarySet()
                    line_type = MGeoItem.LANE_BOUNDARY

            if line_set is None:
                QMessageBox.warning(self.canvas, "Warning", "No link data selected.")
                return
            if line_type == MGeoItem.LINK and len(self.getLinkSet().lines) < 1:
                QMessageBox.warning(self.canvas, "Warning", "No link data loaded.")
                return
            if line_type == MGeoItem.LANE_BOUNDARY and len(self.canvas.getLaneBoundarySet().lanes) < 1:
                QMessageBox.warning(self.canvas, "Warning", "No lane_boundary data loaded.")
                return
            
            self.dangling_links = error_fix.find_dangling_links(line_set, line_type.name)
            for link in self.dangling_links:
                self.canvas.list_error.append({'type': line_type, 'id': link.idx})

            link_idx_string = '['
            for link in self.dangling_links:
                link_idx_string += '{}, '.format(link.idx)
            link_idx_string += ']'
            Logger.log_info('find_dangling_lines(type:{}) result: {}'.format(line_type.name, link_idx_string))

            # dangling_links에 link 유/무에 따라 (delete_dangling_links) menu action enable
            if self.dangling_links is None or self.dangling_links == []:
                QMessageBox.information(self.canvas, "Information", "No dangling lines were found.")
                act_find.setDisabled(True)
                if self.overlapped_node is None or self.overlapped_node == []:
                    act_clear.setDisabled(True)
            else:
                action_fix.setDisabled(False)
                act_clear.setDisabled(False)
        
        except BaseException as e:
            Logger.log_error('find_dangling_links failed (traceback is down below) \n{}'.format(traceback.format_exc()))
            

    def fix_dangling_links(self, act_fix, act_clear):
        Logger.log_trace('Called: fix_dangling_lines')
        try:
            dangling_link_idx_list = list()
            link_idx_string = '['
            for link in self.dangling_links:
                link_idx_string += '{}, '.format(link.idx)
                dangling_link_idx_list.append(link.idx)
            link_idx_string += ']'
            # link -> FixDanglingLinks / lane -> FixDanglingLanes
            if 'boundary' in str(self.dangling_links[0]):
                cmd_fix_dangling_links = FixDanglingLanes(self.canvas, dangling_link_idx_list)
            else:
                cmd_fix_dangling_links = FixDanglingLinks(self.canvas, dangling_link_idx_list)
            self.canvas.command_manager.execute(cmd_fix_dangling_links)

            act_fix.setDisabled(True)
            Logger.log_info('dangling lines ({}) fixed.'.format(link_idx_string))

            if self.dangling_links is None or self.dangling_links == []:
                act_fix.setDisabled(True)
            else:
                act_clear.setDisabled(False)

        except BaseException as e:
            Logger.log_error('fix_item failed (traceback is down below) \n{}'.format(traceback.format_exc()))


    def find_location_error_link(self, act_find, act_clear):
        """link의 start/end point와 node의 위치가 1m 이상 차이가 나는 node를 검색"""
        Logger.log_trace('Called: find_location_error_link')

        self.error_link_list = list()
        try:
            if self.getLinkSet() is None or len(self.getLinkSet().lines) < 1 :
                QMessageBox.warning(self.canvas, "Warning", "No link data loaded.")
                return

            for idx, link in self.getLinkSet().lines.items():
                if link.has_location_error_node():
                    self.error_link_list.append(link)

            for link in self.error_link_list:
                self.canvas.list_error.append({'type': MGeoItem.LINK, 'id': link.idx})

            if self.error_link_list is None or self.error_link_list == []:
                QMessageBox.information(self.canvas, "Information", "No links with location errors found.")
                act_find.setDisabled(True)
            else:
                act_clear.setDisabled(False)

        except BaseException as e:
            Logger.log_error('find_location_error_link failed (traceback is down below) \n{}'.format(traceback.format_exc()))

        return self.error_link_list


    def find_closed_loop_link(self, act_clear):
        Logger.log_trace('Called: find_closed_loop_link')
        try:
            line_type_window = SelectLineTypeWindow()
            return_line_type = line_type_window.showDialog()

            if return_line_type != 1:
                return
            else:
                if line_type_window.link.isChecked():
                    lines = self.canvas.getLinkSet().lines
                    # line_type = MGeoItem.NODE
                    line_type = MGeoItem.LINK
                else:
                    lines = self.canvas.getLaneBoundarySet().lanes
                    line_type = MGeoItem.LANE_BOUNDARY
                self.closed_loop_link_type = line_type

            self.closed_loop_links = []
            for idx, link in lines.items():
                if link.from_node is link.to_node:
                    self.closed_loop_links.append(link)
                    
            if self.closed_loop_links == []:
                # 찾은 결과가 없는 경우, 안내 후 종료.
                self.canvas.list_error.clear() # 기존에 clear 되지 않았던 오류가 있다면 clear한다
                QMessageBox.information(self.canvas, "Information", "No closed-loop links were found.")
                Logger.log_info('No closed-loop link is found')

            else:
                # 찾은 결과가 있을 경우, error_list에 추가한다
                for link in self.closed_loop_links:
                    self.canvas.list_error.append({'type': line_type, 'id': link.idx})

                closed_loop_links_id_string = Link.get_id_list_string(self.closed_loop_links)
                Logger.log_info('{} closed-loop link(s) were found: {}'.format(len(self.closed_loop_links), closed_loop_links_id_string))

                # 찾은 결과가 있으면, clear 기능을 활성화한다 
                act_clear.setDisabled(False)

        except BaseException as e:
            Logger.log_error('find_closed_loop_link failed (traceback is down below) \n{}'.format(traceback.format_exc()))


    def delete_closed_loop_link(self, act_clear):
        Logger.log_trace('Called: repair_closed_loop_link')
        try:
            items = list()
            for closed_loop in self.closed_loop_links:
                item = {'id':closed_loop.idx, 'type':self.closed_loop_link_type}
                items.append(item)
            
            cmd_delete_closed_loop = DeleteMgeoItem(self.canvas, items)
            self.canvas.command_manager.execute(cmd_delete_closed_loop)

            self.canvas.list_error.clear()
            Logger.log_info('delete_closed_loop_link completed')

        except BaseException as e:
            Logger.log_error('delete_closed_loop_link failed (traceback below) \n{}'.format(traceback.format_exc()))


    def find_opposite_direction_link(self, act_clear):
        Logger.log_trace('Called: find_opposite_direction_link')
        try:
            opposite_direction_links = []
            opposite_direction_lane_boundarys = []
            link_set = self.canvas.mgeo_planner_map.link_set.lines
            lane_boundary_set  = self.canvas.mgeo_planner_map.lane_boundary_set.lanes
            
            for link in link_set.values():
                # NOTE(chi) temporary commit

                boundary_dir = link.lane_mark_left[0].points[1] - link.lane_mark_left[0].points[0]  
                link_dir = link.points[1] - link.points[0]
                if np.dot(boundary_dir, link_dir) < 0:

                    opposite_direction_lane_boundarys.append(link.lane_mark_left[0])
                
                boundary_dir = link.lane_mark_right[0].points[1] - link.lane_mark_right[0].points[0]  
                link_dir = link.points[1] - link.points[0]
                if np.dot(boundary_dir, link_dir) < 0:
                    opposite_direction_lane_boundarys.append(link.lane_mark_right[0])
                
                try:
                    
                    to_link_second = link.get_to_links()[0].points[1]
                    to_link_first = link.get_to_links()[0].points[0]
                    
                    to_node_link_second = link.points[-1]
                    to_node_link_first = link.points[-2]
                    
                    from_link_second = link.get_from_links()[0].points[-1]
                    from_link_first = link.get_from_links()[0].points[-2]

                    from_node_link_second = link.points[1]
                    from_node_link_first = link.points[0]
                    
                    if (np.dot(to_link_second-to_link_first, to_node_link_second-to_node_link_first) < 0) \
                        and (np.dot(from_link_second-from_link_first, from_node_link_second-from_node_link_first) < 0):  
                        opposite_direction_links.append(link)
                    
                except:
                    try:
                        to_link_second = link.get_to_links()[0].points[1]
                        to_link_first = link.get_to_links()[0].points[0]
                        
                        to_node_link_second = link.points[-1]
                        to_node_link_first = link.points[-2]
                        
                        if (np.dot(to_link_second-to_link_first, to_node_link_second-to_node_link_first) < 0):
                            opposite_direction_links.append(link)
                    except:
                        try:
                            from_link_second = link.get_from_links()[0].points[-1]
                            from_link_first = link.get_from_links()[0].points[-2]

                            from_node_link_second = link.points[1]
                            from_node_link_first = link.points[0]
                            
                            if (np.dot(from_link_second-from_link_first, from_node_link_second-from_node_link_first) < 0):  
                                opposite_direction_links.append(link)
                        except: 
                            pass

            if len(opposite_direction_links) == 0:
                # 찾은 결과가 없는 경우, 안내 후 종료.
                self.canvas.list_error.clear() # 기존에 clear 되지 않았던 오류가 있다면 clear한다
                
                QMessageBox.information(self.canvas, "Information", "No opposing direction links were found.")
                Logger.log_info('"No opposite direction link is found')
                # return  

            else:
                # 찾은 결과가 있을 경우, error_list에 추가한다
                for link in opposite_direction_links:
                    # 찾은 결과가 있을 경우, error_list에 추가한다
                    self.canvas.list_error.append({'type': MGeoItem.LINK, 'id': link.idx})
                
                link_idx_string = '['
                for link in opposite_direction_links:
                    link_idx_string += '{}, '.format(link.idx)
                link_idx_string += ']'
                Logger.log_info('find_opposite_direction_link result: {}'.format(link_idx_string))

                # 찾은 결과가 있으면, clear 기능을 활성화한다 
                act_clear.setDisabled(False)
                
                for link in opposite_direction_links:
                    link.points = np.flip(link.points, axis = 0)             
                    
                    temp_to_node = link.to_node
                    temp_from_node = link.from_node
                    
                    link.to_node = temp_from_node
                    link.from_node = temp_to_node
                    
                    link.to_node.from_links.append(link)
                    link.to_node.to_links.remove(link)
                    
                    link.from_node.to_links.append(link)
                    link.from_node.from_links.remove(link)

                #for lane boundary

            for link in lane_boundary_set.values():
                try:
                    
                    to_link_second = link.get_to_links()[0].points[1]
                    to_link_first = link.get_to_links()[0].points[0]
                    
                    to_node_link_second = link.points[-1]
                    to_node_link_first = link.points[-2]
                    
                    from_link_second = link.get_from_links()[0].points[-1]
                    from_link_first = link.get_from_links()[0].points[-2]

                    from_node_link_second = link.points[1]
                    from_node_link_first = link.points[0]
                    
                    if (np.dot(to_link_second-to_link_first, to_node_link_second-to_node_link_first) < 0) \
                        and (np.dot(from_link_second-from_link_first, from_node_link_second-from_node_link_first) < 0):  
                        opposite_direction_lane_boundarys.append(link)

                except:
                    try:
                        to_link_second = link.get_to_links()[0].points[1]
                        to_link_first = link.get_to_links()[0].points[0]
                        
                        to_node_link_second = link.points[-1]
                        to_node_link_first = link.points[-2]
                        
                        if (np.dot(to_link_second-to_link_first, to_node_link_second-to_node_link_first) < 0):
                            opposite_direction_lane_boundarys.append(link)
                    except:
                        try:
                            from_link_second = link.get_from_links()[0].points[-1]
                            from_link_first = link.get_from_links()[0].points[-2]

                            from_node_link_second = link.points[1]
                            from_node_link_first = link.points[0]
                            
                            if (np.dot(from_link_second-from_link_first, from_node_link_second-from_node_link_first) < 0):  
                                opposite_direction_lane_boundarys.append(link)
                        except: 
                            pass
            
            opposite_direction_lane_boundarys = set(opposite_direction_lane_boundarys)
            opposite_direction_lane_boundarys = list(opposite_direction_lane_boundarys)
            
            if len(opposite_direction_lane_boundarys) == 0:
                # 찾은 결과가 없는 경우, 안내 후 종료.
                self.canvas.list_error.clear() # 기존에 clear 되지 않았던 오류가 있다면 clear한다
                
                QMessageBox.information(self.canvas, "Information", "No opposing direction lane_boundary were found.")
                Logger.log_info('"No opposite direction lane boundary is found')
                return 

            else:
                for link in opposite_direction_lane_boundarys:
                    self.canvas.list_error.append({'type': MGeoItem.LANE_BOUNDARY, 'id': link.idx})
                
                link_idx_string = '['
                for link in opposite_direction_lane_boundarys:
                    link_idx_string += '{}, '.format(link.idx)
                link_idx_string += ']'
                Logger.log_info('find_opposite_direction_lane_boundary result: {}'.format(link_idx_string))

                # 찾은 결과가 있으면, clear 기능을 활성화한다 
                act_clear.setDisabled(False)
                
                for link in opposite_direction_lane_boundarys:
                    link.points = np.flip(link.points, axis = 0)             
                    
                    temp_to_node = link.to_node
                    temp_from_node = link.from_node
                    
                    link.to_node = temp_from_node
                    link.from_node = temp_to_node
                    
                    link.to_node.from_links.append(link)
                    link.to_node.to_links.remove(link)
                    
                    link.from_node.to_links.append(link)
                    link.from_node.from_links.remove(link)
        
            # opposite_direction_links = []
            # for idx, node in self.canvas.getNodeSet().nodes.items():
            #     if len(node.from_links) >= 2 and len(node.to_links) < 1:
            #         for link in node.from_links:
            #             opposite_direction_links.append(link)
                    
            # if len(opposite_direction_links) == 0:
            #     # 찾은 결과가 없는 경우, 안내 후 종료.
            #     self.canvas.list_error.clear() # 기존에 clear 되지 않았던 오류가 있다면 clear한다
                
            #     QMessageBox.information(self.canvas, "Information", "No opposing direction links were found.")
            #     Logger.log_info('"No opposite direction link is found')
            #     return 

            # else:
            #     # 찾은 결과가 있을 경우, error_list에 추가한다
            #     for link in opposite_direction_links:
            #         # 찾은 결과가 있을 경우, error_list에 추가한다
            #         self.canvas.list_error.append({'type': MGeoItem.LINK, 'id': link.idx})
                
            #     link_idx_string = '['
            #     for link in opposite_direction_links:
            #         link_idx_string += '{}, '.format(link.idx)
            #     link_idx_string += ']'
            #     Logger.log_info('find_opposite_direction_link result: {}'.format(link_idx_string))

            #     # 찾은 결과가 있으면, clear 기능을 활성화한다 
            #     act_clear.setDisabled(False)

            #     return 

        except BaseException as e:
            Logger.log_error('find_opposite_direction_link failed (traceback is down below) \n{}'.format(traceback.format_exc()))
        
        # try:
        #     opposite_direction_links = []
            
        #     link_set = self.canvas.mgeo_planner_map.lane_boundary_set.lanes
            
        #     for link in link_set.values():
        #         try:
                    
        #             to_link_second = link.get_to_links()[0].points[1]
        #             to_link_first = link.get_to_links()[0].points[0]
                    
        #             to_node_link_second = link.points[-1]
        #             to_node_link_first = link.points[-2]
                    
        #             from_link_second = link.get_from_links()[0].points[-1]
        #             from_link_first = link.get_from_links()[0].points[-2]

        #             from_node_link_second = link.points[1]
        #             from_node_link_first = link.points[0]
                    
        #             if (np.dot(to_link_second-to_link_first, to_node_link_second-to_node_link_first) < 0) \
        #                 and (np.dot(from_link_second-from_link_first, from_node_link_second-from_node_link_first) < 0):  
        #                 opposite_direction_links.append(link)

        #         except:
        #             try:
        #                 to_link_second = link.get_to_links()[0].points[1]
        #                 to_link_first = link.get_to_links()[0].points[0]
                        
        #                 to_node_link_second = link.points[-1]
        #                 to_node_link_first = link.points[-2]
                        
        #                 if (np.dot(to_link_second-to_link_first, to_node_link_second-to_node_link_first) < 0):
        #                     opposite_direction_links.append(link)
        #             except:
        #                 try:
        #                     from_link_second = link.get_from_links()[0].points[-1]
        #                     from_link_first = link.get_from_links()[0].points[-2]

        #                     from_node_link_second = link.points[1]
        #                     from_node_link_first = link.points[0]
                            
        #                     if (np.dot(from_link_second-from_link_first, from_node_link_second-from_node_link_first) < 0):  
        #                         opposite_direction_links.append(link)
        #                 except: 
        #                     pass

        #     if len(opposite_direction_links) == 0:
        #         # 찾은 결과가 없는 경우, 안내 후 종료.
        #         self.canvas.list_error.clear() # 기존에 clear 되지 않았던 오류가 있다면 clear한다
                
        #         QMessageBox.information(self.canvas, "Information", "No opposing direction links were found.")
        #         Logger.log_info('"No opposite direction lane_boundary is found')
        #         return 

        #     else:
        #         # 찾은 결과가 있을 경우, error_list에 추가한다
        #         for link in opposite_direction_links:
        #             # 찾은 결과가 있을 경우, error_list에 추가한다
        #             self.canvas.list_error.append({'type': MGeoItem.LINK, 'id': link.idx})
                
        #         link_idx_string = '['
        #         for link in opposite_direction_links:
        #             link_idx_string += '{}, '.format(link.idx)
        #         link_idx_string += ']'
        #         Logger.log_info('find_opposite_direction_lane_boundary result: {}'.format(link_idx_string))

        #         # 찾은 결과가 있으면, clear 기능을 활성화한다 
        #         act_clear.setDisabled(False)
                
        #         for link in opposite_direction_links:
        #             link.points = np.flip(link.points, axis = 0)             
                    
        #             temp_to_node = link.to_node
        #             temp_from_node = link.from_node
                    
        #             link.to_node = temp_from_node
        #             link.from_node = temp_to_node
                    
        #             link.to_node.from_links.append(link)
        #             link.to_node.to_links.remove(link)
                    
        #             link.from_node.to_links.append(link)
        #             link.from_node.from_links.remove(link)

        # except BaseException as e:
        #     Logger.log_error('find_opposite_direction_link failed (traceback is down below) \n{}'.format(traceback.format_exc()))


    def find_duplicated_link(self, act_clear):
        Logger.log_trace('Called: find_duplicated_link')
        try:
            duplicated_links = []
            for idx, link in self.canvas.getLinkSet().lines.items():
                for compare_idx, compare_link in self.canvas.getLinkSet().lines.items():
                    if idx != compare_idx and link.from_node == compare_link.from_node and link.to_node == compare_link.to_node:
                        duplicated_links.append(link)
                        duplicated_links.append(compare_link)
                    
            if len(duplicated_links) == 0:
                # 찾은 결과가 없는 경우, 안내 후 종료.
                self.canvas.list_error.clear() # 기존에 clear 되지 않았던 오류가 있다면 clear한다
                
                QMessageBox.information(self.canvas, "Information", "No duplicated links were found.")
                Logger.log_info('"No duplicated links were found')
                return 

            else:
                # 찾은 결과가 있을 경우, error_list에 추가한다
                for link in duplicated_links:
                    # 찾은 결과가 있을 경우, error_list에 추가한다
                    self.canvas.list_error.append({'type': MGeoItem.LINK, 'id': link.idx})
                
                link_idx_string = '['
                for link in duplicated_links:
                    link_idx_string += '{}, '.format(link.idx)
                link_idx_string += ']'
                Logger.log_info('find_duplicated_link result: {}'.format(link_idx_string))

                # 찾은 결과가 있으면, clear 기능을 활성화한다 
                act_clear.setDisabled(False)

                return 

        except BaseException as e:
            Logger.log_error('find_duplicated_link failed (traceback is down below) \n{}'.format(traceback.format_exc()))


    def clear_highlight(self, repair_action_list, act_clear):
        Logger.log_trace('Called: clear_highlight')
        try:
            self.canvas.list_error.clear()
            self.canvas.list_highlight1.clear()
            self.overlapped_node.clear()
            self.dangling_nodes.clear()
            
            # 찾았던 item clear 시키는 현재 기능 또한 disable 시킨다
            act_clear.setDisabled(True)
            
            # repair 관련 기능들 다시 disable 시킨다
            for action in repair_action_list:
                action.setDisabled(True)
            
        except BaseException as e:
            Logger.log_error('clear_highlight failed (traceback is down below) \n{}'.format(traceback.format_exc()))       


    def find_empty_related_signal_link(self, act_repair, act_clear):
        Logger.log_trace('Called: find_empty_related_signal_link')
        try:
            unset_related_signal_links = []
            # 모든 링크 확인
            # signal class -> link_id_list
            # related signal 없으면 에러링크
            tl_set = self.getTLSet().signals

            for signal_id in tl_set:
                if tl_set[signal_id].type_def == 'mgeo':
                    if tl_set[signal_id].type == 'pedestrian':
                        continue
                else:
                    if tl_set[signal_id].sub_type != '505':
                        continue
                
                for link_id in tl_set[signal_id].link_id_list:
                    if link_id != '' and link_id != None:
                        if link_id in self.canvas.getLinkSet().lines:
                            signal_link = self.canvas.getLinkSet().lines[link_id]
                        
                            if signal_link.related_signal == None or signal_link.related_signal == '':
                                if link_id not in unset_related_signal_links:
                                    unset_related_signal_links.append(link_id)
                        else:
                            Logger.log_info('signal id : {}  \n {} is wrong link id.'.format(signal_id, link_id))
            
            if len(unset_related_signal_links) == 0:
                self.canvas.list_error.clear()
                QMessageBox.information(self.canvas, "Information", "No empty related signal links were found.")
                Logger.log_info('No empty related signal links were found')

            else:
                # 찾은 결과가 있을 경우, error_list에 추가한다
                for link in unset_related_signal_links:
                    self.canvas.list_error.append({'type': MGeoItem.LINK, 'id': link})
                
                link_idx_string = '['
                for link in unset_related_signal_links:
                    link_idx_string += '{}, '.format(link)
                link_idx_string += ']'
                Logger.log_info('find_empty_related_signal_link result: {}'.format(link_idx_string))

                # 찾은 결과가 있으면, clear 기능을 활성화한다 
                act_clear.setDisabled(False)

        except BaseException as e:
            Logger.log_error('find_empty_related_signal_link failed (traceback is down below) \n{}'.format(traceback.format_exc()))


    def add_duplicate_point(self, dup_dic, key_, point_idx):
        if key_ in dup_dic: 
            dup_dic[key_].add(point_idx)
        else:
            dup_dic[key_] = set()
            dup_dic[key_].add(point_idx)

    
    # ADD: 11/9/2021 [SHJ]
    def find_intersecting_links(self):
        '''
        Find all intersecting links
        '''
        Logger.log_trace('Called: find intersecting links')
        
        # Define increased traffic node list and temporary link list
        compared_link_list = list()
        ref_nodes = list()
        merging_nodes = list()
        
        intersecting_dict = OrderedDict()
        
        # Define the key from the canvas
        key = self.canvas.mgeo_key
        
        # Grab the map info
        mgeo_map_planner = self.canvas.mgeo_maps_dict[key]
        node_set = mgeo_map_planner.node_set
        link_set = mgeo_map_planner.link_set
        
        '''
        Pre-processing 1. 
        Reference Node (Ref Links) Information
        Reference Node tracked where the traffic gets busy
        
        Merging Case have to be the links that are intersecting each other
        But the algorithm have to search all intersecting links at the intersection
        '''
        for idx, item in node_set.nodes.items():
            if item.on_stop_line == True:
                ref_nodes.append(item)
            
            # MERGING CASE: If they have more than 2 from_links and 1 to_links
            # that links are intersecting each other
            if len(item.from_links) >= 2 and len(item.to_links) == 1:
                link_cnt = 0
                
                # Find all links in from_links from ref_node
                for link in item.from_links:
                    # if they are not lane changed link, count the links
                    if link.lazy_point_init == False:
                        link_cnt += 1
                        if link_cnt > 1:
                            merging_nodes.append(item)
        
        ''' Compared Links Information'''
        # Preprocess the to_link information by getting rid of the link can change the lane
        for node in ref_nodes:
            for link in node.to_links:
                compared_link_list.append(link)
        
        compared_link_list = sorted(compared_link_list, key=lambda x: x.idx)
        
        intersection_region = BoundingBox(link_set)
        for ref_link in compared_link_list:
            for link in compared_link_list:
                flag = intersection_region.check_intersects_long_vec(ref_link, link)
                
                if flag == True:
                    print("Link {} intersects with ref_link {}".format(link.idx, ref_link.idx))
         
        
    def check_intersect_lane(self, lane_a, lane_b):
        a_min_x = lane_a.bbox_x[0]
        a_max_x = lane_a.bbox_x[1]
        a_min_y = lane_a.bbox_y[0]
        a_max_y = lane_a.bbox_y[1]
        a_min_z = lane_a.bbox_z[0]
        a_max_z = lane_a.bbox_z[1]

        b_min_x = lane_b.bbox_x[0]
        b_max_x = lane_b.bbox_x[1]
        b_min_y = lane_b.bbox_y[0]
        b_max_y = lane_b.bbox_y[1]
        b_min_z = lane_b.bbox_z[0]
        b_max_z = lane_b.bbox_z[1]

        if (a_max_x < b_min_x) or (a_min_x > b_max_x) : return False
        if (a_max_y < b_min_y) or (a_min_y > b_max_y) : return False
        if (a_max_z < b_min_z) or (a_min_z > b_max_z) : return False

        return True
            
    
    def find_duplicated_lane(self):
        Logger.log_trace('Called: find_duplicated_lane start')
        try:
            lane_set = self.canvas.getLaneBoundarySet()
            if lane_set is None:
                Logger.log_error('lane_boundary_set is null')
                return

            lane_marking_list = lane_set.lanes
            
            duplicate_lane_id_dic = dict()
            no_touch_lane_id = list()

            total_len = len(lane_marking_list)
            threshold_dist = 0.1        # 중첩거리 기준
            debug_loop_cnt = 0

            # 체크하는 라인 종류
            check_lane_type = set()
            check_lane_type.add(501) # 중앙선
            check_lane_type.add(502) # 유턴구역선
            check_lane_type.add(506) # 진로변경제한선(정지선 뒤)
            check_lane_type.add(507) # 진로변경제한선(합류 지점)
            check_lane_type.add(508) # 진로변경제한선(합류 지점[고속도로, 자동차전용도로])


            for lane_a in lane_marking_list:
                # 라인 하나를 기준으로 잡고(A라고 하자), 이 라인과 겹치는 라인이 있는지 찾아보자.
                # 다른 라인(B)들을 순회하면서, B에게 속해있는 노드들의 위치가 A 위에 있는지 검사.
                
                line_A = lane_marking_list[lane_a]

                if (line_A.lane_type[0] in check_lane_type) == False : # 검사할 레인의 종류.
                    debug_loop_cnt += 1
                    continue
                no_touch_lane_id.append(lane_a)

                for lane_b in lane_marking_list:
                    if lane_a == lane_b : 
                        continue
                    line_B = lane_marking_list[lane_b]
                    if line_B.lane_type[0] != line_A.lane_type[0] :               # 비교 대상과 레인 종류가 같아야 합니다.
                        continue
                    if lane_b in no_touch_lane_id :
                        continue
                    if self.check_intersect_lane(line_A, line_B) == False : # AABB 충돌 체크해서 아니면 넘어감.
                        continue

                    temp_dupl_idx_list = list()
                    for i in range(len(line_A.points) - 1):
                        # Logger.log_debug('------')
                        for j in range(len(line_B.points)):
                            lp_dist = self.calculate_distance_point_to_line(line_A.points[i], line_A.points[i+1], line_B.points[j])
                            # Logger.log_debug('lp_dist = {}'.format(lp_dist))
                            if lp_dist < threshold_dist :
                                # 겹친다고 판단.
                                temp_dupl_idx_list.append(j)
                    
                    if len(temp_dupl_idx_list) > 1: # 한 개만 제거 하는 건 예외로 둔다.( 연결 부위 )
                        for du_val in temp_dupl_idx_list:
                            self.add_duplicate_point(duplicate_lane_id_dic, line_B.idx, du_val)

                    temp_dupl_idx_list.clear()

                Logger.log_debug('{}'.format(debug_loop_cnt + len(no_touch_lane_id)) + '/{}'.format(total_len))
                debug_loop_cnt += 1

            # 중복된 것을 지움.
            for key, val in duplicate_lane_id_dic.items():
                lane_ = lane_marking_list[key]
                cp_arr = lane_.points.tolist()
                lane_len = len(cp_arr)

                if lane_len == 0: break
                dupl_idx_list = list()
                for s_val in val:
                    dupl_idx_list.append(s_val)
                
                if len(dupl_idx_list) <= 0 : continue
                dupl_idx_list.sort(reverse=True) # 인덱스 내림차순으로 정렬.(삭제 편리를 위해)

                # lane 을 나눔.  # 중간점만 제거되면 레인의 모양이 변형됨. 
                self.divide_part_of_lane(lane_, dupl_idx_list)

            duplicate_lane_id_dic.clear()
            no_touch_lane_id.clear()
            
            Logger.log_trace('Called: find_duplicated_lane end')
        except BaseException as e:
            Logger.log_error('find_duplicated_lanes failed (traceback is down below) \n{}'.format(traceback.format_exc()))


    def divide_part_of_lane(self, origin_lane, duplicate_idx_list):
        remain_point_idx_list = list()
        for i in range(len(origin_lane.points)):
            if (i in duplicate_idx_list):
                continue
            else:
                remain_point_idx_list.append(i) # 살아남은 노드들 모음.
        
        lane_marking_list = self.canvas.getLaneBoundarySet().lanes

        if len(remain_point_idx_list) <= 1: # 노드 하나만 있다면 line을 생성할 필요가 없으니 삭제.
            del lane_marking_list[origin_lane.idx]
            return

        # 점들을 체크해서 선을 분할해줍니다.
        start_idx = remain_point_idx_list[0]
        num_of_part = 0
        part_dic = dict()
        for val in remain_point_idx_list:
            if val == start_idx :
                if num_of_part in part_dic: 
                    part_dic[num_of_part].append(val)
                else:
                    part_dic[num_of_part] = list()
                    part_dic[num_of_part].append(val)
                start_idx += 1
            else:
                # 단선 되었다는 이야기.
                num_of_part += 1
                if num_of_part in part_dic: 
                    part_dic[num_of_part].append(val)
                else:
                    part_dic[num_of_part] = list()
                    part_dic[num_of_part].append(val)
                start_idx = (val + 1)
        
        # 분리된 선의 끝 처리
        origin_lane_len = len(origin_lane.points)
        for pkey, pvalue in part_dic.items():
            len_pvalue = len(pvalue)
            if min(pvalue) == 0 :
                if origin_lane_len > len_pvalue :
                    pvalue.append(len_pvalue)
            if max(pvalue) == (origin_lane_len - 1) :
                if min(pvalue) != 0 :
                    pvalue.append(min(pvalue) - 1)
            if min(pvalue) != 0 and max(pvalue) != (origin_lane_len - 1) :
                pvalue.append(min(pvalue) - 1)
                pvalue.append(max(pvalue) + 1)
        
        # 나뉜 점을 기반으로 라인을 분할해 줍니다.
        for pkey, pvalue in part_dic.items():
            part_lane = copy.deepcopy(origin_lane)
            cp_arr = part_lane.points.tolist()
            pvalue.sort(reverse=True) # 인덱스 내림차순으로 정렬.(삭제 편리를 위해)

            # 여기 없는 값만 지워줍니다.
            for i in reversed(range(origin_lane_len)) :
                if i in pvalue:
                    continue
                del cp_arr[i]

            # 새로 생성해서 넣어줍니다.
            part_lane.points = np.array(cp_arr)
            part_lane.idx += '_part_{}'.format(pkey)
            lane_marking_list[part_lane.idx] = part_lane

            if (part_lane.idx in self.duplicated_lane) == False:
                self.duplicated_lane[part_lane.idx] = list()
                self.duplicated_lane[part_lane.idx].append(part_lane)
            else:
                self.duplicated_lane[part_lane.idx] = list()
                self.duplicated_lane[part_lane.idx].append(part_lane)
        
        del lane_marking_list[origin_lane.idx]


    def find_mismatch_lane_change(self):
        Logger.log_trace('Called: find_mismatch_lane_change')
        try:
            link_set = self.getLinkSet()

            if link_set is None or len(link_set.lines) < 1:
                QMessageBox.warning(self.canvas, 'Warning', 'No link data loaded.')
                return

            mismatch = error_fix.find_mismatch_lane_change_links(link_set)

            link_idx_string = '['
            for link, lane_ch_link in mismatch.items():
                link_idx_string += 'Link: {} '.format(link)
                link_idx_string += '{} ,'.format(lane_ch_link)
            link_idx_string += ']'
            Logger.log_info('find_mismatch_lane_change result: {}'.format(link_idx_string))

        except BaseException as e:
            Logger.log_error('find_mismatch failed')


    def fix_signal_road_connection(self):
        Logger.log_trace('Called: fix_signal_road_connection')
        try:
            cmd_fix_signal_road_connection = FixSignalRoadConnection(self.canvas)
            self.canvas.command_manager.execute(cmd_fix_signal_road_connection)

            Logger.log_info('fix_signal_road_connection changed {} signals'.format(cmd_fix_signal_road_connection.counter))

        except BaseException as e:
            Logger.log_error('fix_signal_road_connection failed')


    # 점 a, b가 이루는 선분과 다른점의 거리를 구해 반환합니다.
    def calculate_distance_point_to_line(self, line_pos_a, line_pos_b, point):
        A = np.array(line_pos_a[0:2])
        B = np.array(line_pos_b[0:2])
        distance = np.dot(point[0:2]-A, B-A)/sum(np.square(B-A))
        if distance < 0:
            ret_dist_value = np.sqrt(sum((point[0:2]-A)**2))
            return ret_dist_value
        elif distance > 1: 
            ret_dist_value = np.sqrt(sum((point[0:2]-B)**2))
            return ret_dist_value
        else:
            scaleAB = (B-A)*distance
            perpendicular_point = A + scaleAB
            perperdicular_p_to_p = point[0:2] - perpendicular_point
            ret_dist_value = np.sqrt(sum((perperdicular_p_to_p)**2))
            return ret_dist_value


    def change_ngii_to_mgeo(self):

        type_def = next((link.link_type_def for idx, link in self.canvas.getLinkSet().lines.items() if link.link_type_def != '' or link.link_type_def is not None), None)
        
        select_window = ChangeNgiitoMGeoWidget(type_def=type_def)
        return_edit = select_window.showDialog()
        
        funcs_ngii_to_mgeo = ChangeNgiitoMGeo()

        if return_edit != 1:
            return
        else:
            if select_window.on_stop_line_node.isChecked():
                funcs_ngii_to_mgeo.find_mismatch_on_stop_line(self.canvas.mgeo_planner_map, self.canvas.list_error)
                funcs_ngii_to_mgeo.repair_mismatch_on_stop_line(self.canvas.mgeo_planner_map, self.canvas.list_error)
                
            if select_window.link_id_list_tl.isChecked():
                funcs_ngii_to_mgeo.find_mismatch_traffic_ligth_link_id(self.canvas.mgeo_planner_map, self.canvas.list_error)
                funcs_ngii_to_mgeo.repair_mismatch_traffic_ligth_link_id(self.canvas.mgeo_planner_map, self.canvas.list_error)
                
            if select_window.related_signal_link.isChecked():
                funcs_ngii_to_mgeo.set_link_related_signal(self.canvas.mgeo_planner_map)

            if select_window.set_type_def.isChecked():
                funcs_ngii_to_mgeo.find_and_repair_null_type_def(self.canvas.mgeo_planner_map, select_window.type_def_text.text())
        Logger.log_info('complete change_ngii_to_mgeo')

    """
    OpenDRIVE Junction Error 수정 (TomTom 기준) 
    """
    # tomtom juction error 
    def find_junction_error(self):
        """
        1. junction 자동 생성 후에 incoming junction 위치 찾기
        2. 같은 road_id로 묶인 link중에 이미 분리된(이전 링크) road id를 가진 link들 위치 찾기
        3. carla에서 display안되는 부분(jucntion 2개가 합쳐져야 하는 부분) 위치 찾기 : carla_none_junctions
        """
        junctions = self.getJunctionSet().junctions

        # 1
        for junction in junctions:
            current_junction = junctions[junction]
            for node in current_junction.jc_nodes:
                if len(node.from_links) < 1:
                    sp_dict = {'type':MGeoItem.JUNCTION, 'id':junction}
                    if sp_dict not in self.canvas.list_error:
                        self.canvas.list_error.append(sp_dict)
                        Logger.log_info('[Junction Error] End Junctions → Junction ID : {}'.format(junction))
        
        # 2, 3
        error_junction = []
        # 하나로 합쳐져야할 junction
        carla_none_junctions = []

        for junction in junctions:
            current_junction = junctions[junction]
            
            sp_dict = {'type':MGeoItem.JUNCTION, 'id':junction}
            if sp_dict in self.canvas.list_error:
                continue
            
            junction_link_list = []
            for node in current_junction.jc_nodes:
                to_links = node.to_links
                for fnode in to_links:
                    if fnode.to_node in current_junction.jc_nodes:
                        junction_link_list.append(fnode)

            if len(junction_link_list) < 1:
                continue

            for jl in junction_link_list:
                from_j_list = jl.from_node.junctions
                to_j_list = jl.to_node.junctions
                if len(from_j_list) > 1 and len(to_j_list) > 1:
                    if from_j_list == to_j_list:
                        junction_list = []
                        for j in to_j_list:
                            junction_list.append(j.idx)
                        if junction_list not in carla_none_junctions:
                            carla_none_junctions.append(junction_list)
            
            check_link = dict()

            current_link = junction_link_list[0]
            check_link[current_link.road_id] = [current_link]

            while current_link.lane_ch_link_right is not None:
                current_link = current_link.lane_ch_link_right
                if current_link.road_id in check_link:
                    check_link[current_link.road_id].append(current_link)
                else:
                    check_link[current_link.road_id] = [current_link]

            current_link = junction_link_list[0]
            while current_link.lane_ch_link_left is not None:
                current_link = current_link.lane_ch_link_left
                if current_link.road_id in check_link:
                    check_link[current_link.road_id].append(current_link)
                else:
                    check_link[current_link.road_id] = [current_link]

            for check_road in check_link:
                road_ids = []
                
                if next((item for item in check_link[check_road] if len(item.from_node.from_links) > 1), False):
                    continue

                for clink in check_link[check_road]:
                    if len(clink.from_node.from_links) == 1:
                        road_id = clink.from_node.from_links[0].road_id
                        if road_id not in road_ids:
                            road_ids.append(road_id)
                
                if len(road_ids) > 1:
                    for clink in check_link[check_road]:
                        sp_dict = {'type':MGeoItem.LINK, 'id':clink.idx}
                        self.canvas.list_error.append(sp_dict)
                        if junction not in error_junction:
                            error_junction.append(junction)
                            Logger.log_info('[Junction Error] Unregistered Fork → Junction({}), Road id : {}'.format(junction, clink.road_id))

        # carla에서 안나오는 부분 > junction 하나로 합쳐야하는 부분
        if len(carla_none_junctions) > 0:
            Logger.log_info("[Junction Warning] If you don't combine junctions, road may not be visible.  → Junction({})".format(carla_none_junctions))

        # 1-1. geojson에는 laneBorder에 PASSING_NOT_ALLOWED으로 저장되어 있음
        # 1-2. singleBorder에는 white/SINGLE_SOLID_LINE인데

        links = self.canvas.getLinkSet(self.canvas.mgeo_key).lines
        error_road_id = []
        for link in links:
            current_link = links[link]
            from_node = current_link.from_node
            to_node = current_link.to_node

            # if current_link.link_type not in ['DRIVABLE_LANE', 'HOV_LANE', 'BUS_LANE', 'RESTRICTED_LANE']:
            #     continue

            if len(from_node.junctions) > 0 or len(to_node.junctions) > 0:
                continue
            if len(from_node.to_links) == 1 and len(to_node.from_links) == 1:
                continue

            lane_left = current_link.get_lane_mark_left()
            lane_right = current_link.get_lane_mark_right()
            if lane_left is not [] and current_link.can_move_left_lane:
                # if lane_left[0].lane_color == 'white' and lane_left[0].lane_shape[0] == 'Solid':
                Logger.log_info('[Junction Error] Where a junction needs to be created → Link ID : {}, Road ID : {}'.format(link, current_link.road_id))
                sp_dict = {'type':MGeoItem.LINK, 'id':link}
                self.canvas.list_error.append(sp_dict)

            if lane_right is not [] and current_link.can_move_right_lane:
                # if lane_right[0].lane_color == 'white' and lane_right[0].lane_shape[0] == 'Solid':
                Logger.log_info('[Junction Error] Where a junction needs to be created → Link ID : {}, Road ID : {}'.format(link, current_link.road_id))
                sp_dict = {'type':MGeoItem.LINK, 'id':link}
                self.canvas.list_error.append(sp_dict)


    def repair_junction_error_split(self):
        """
        2. 같은 road_id로 묶인 link중에 이미 분리된(이전 링크) road id를 가진 link에 대해서 road_id 다시 부여하기
        (새로운 아이디는 {현재 road_id}-1 로 입력함 >> change_road_name 함수 참고)
        """
        
        if len(self.canvas.list_error) == 0:
            return

        junctions = self.canvas.getJunctionSet().junctions
        links = self.canvas.getLinkSet(self.canvas.mgeo_key).lines

        new_error_list = []
        road_link_set = {}

        for ld in self.canvas.list_error:
            if ld['type'] != MGeoItem.LINK:
                new_error_list.append(ld)
                continue

            error_link = links[ld['id']]
            if error_link.road_id not in road_link_set:
                road_link_set[error_link.road_id] = [error_link]
            else:
                road_link_set[error_link.road_id].append(error_link)
                
        self.change_road_name(road_link_set)

        self.canvas.updateMgeoIdWidget()
        self.canvas.list_error = new_error_list

    def change_road_name(self, road_link_set):

        for rid, links in road_link_set.items():
            # 이전에 갈라진 부분에서부터 id/ego_lane/left, right lane change 다시
            first_link = None
            for item in links:
                if item.ego_lane == 1:
                    first_link = item

            if first_link is None or len(first_link.from_node.from_links) == 0:
                Logger.log_info('[Junction Error] Unregistered Fork → Where a junction needs to be changed Road ID : {}'.format(rid))
                continue

            com_link_road_id = first_link.from_node.from_links[0].road_id

            nroad_id = first_link.road_id
            nego_lane = 1
            current_link = first_link.lane_ch_link_right
            while current_link in links:
                # 옆으로 한칸씩 가면서 이전 링크 로드 아이디가 다른지 체크해서 달라지는 지점부터 road_id 바꾸고 ego_lane바꾸고
                cur_prev_road = []
                for c in current_link.from_node.from_links:
                    cur_prev_road.append(c.road_id)
                # cur_prev_road = current_link.from_node.from_links[0].road_id
                
                # road_id 달라지는 부분
                if com_link_road_id not in cur_prev_road:
                    nroad_id = nroad_id + '-1'
                    nego_lane = 0
                    current_link.can_move_left_lane = False
                    current_link.lane_ch_link_left.can_move_right_lane = False

                nego_lane += 1
                current_link.road_id = nroad_id
                current_link.ego_lane = nego_lane
                com_link_road_id = cur_prev_road[0]

                next_link = current_link.lane_ch_link_right
                if next_link is not None and next_link.road_id == rid:
                    current_link = next_link
                else:
                    break
                
            Logger.log_info('[Junction Fix] Unregistered Fork → Rename Road ID : {}'.format(rid))


    def repair_junction_error_incoming(self):
        """
        1. junction 자동 생성 후에 incoming junction 시작 부분에 방향벡터만큼의 link를 만들기
        
        ※ 분리되면서 시작되는 junction / 합쳐지는 junction으로 분리해서 새로운 link 생성
        - 시작 부분이 나뉘는 거는 road_id를 하나로
        - 시작 부분이 합쳐지는 거는 road_id가 나뉘어야함

        양옆 link/lane_mark 정보 입력은 copy_value_for_virtual_link 함수 참고
        새로운 line(link/lane_mark) 만드는 부분은 virtual_line_for_junction 함수 참고

        """

        if len(self.canvas.list_error) == 0:
            return

        junctions = self.canvas.getJunctionSet().junctions
        links = self.canvas.getLinkSet(self.canvas.mgeo_key).lines
        new_error_list = []

        for item in self.canvas.list_error:

            if item['type'] != MGeoItem.JUNCTION:
                new_error_list.append(item)
                continue
            self.canvas.virtual_road += 1
            junction_item = junctions[item['id']]
            # 시작 부분이 나뉘는 거는 road_id를 하나로
            # 시작 부분이 합쳐지는 거는 road_id가 나뉘어야함

            road_id_dict = dict()
            for node in junction_item.jc_nodes:
                if len(node.from_links) == 0:

                    for tolink in node.to_links:
                        road_id = tolink.road_id
                        if road_id not in road_id_dict:
                            if len(node.to_links) > 1:
                                new_road_id = 'virtualroad{}'.format(self.canvas.virtual_road)
                            else:
                                self.canvas.virtual_road += 1
                                new_road_id = 'virtualroad{}'.format(self.canvas.virtual_road)
                            road_id_dict[road_id] = new_road_id

            divide_link_list = []
            for link in links:
                if links[link].road_id in road_id_dict.keys():
                    in_link = next((item for item in divide_link_list if links[link].from_node == item.from_node), None)
                    if in_link is None:
                        divide_link_list.append(links[link])

            divide_lane_list = []
            for link in divide_link_list:
                new_line = self.virtual_line_for_junction(link, self.canvas.getNodeSet(self.canvas.mgeo_key), self.canvas.getLinkSet(self.canvas.mgeo_key))
                new_line.road_id = road_id_dict[link.road_id]

                if link.lane_mark_left is not []:
                    lane = link.lane_mark_left[0]
                    if next((item for item in divide_lane_list if item.from_node == lane.from_node), None) is None:
                        divide_lane_list.append(lane)
                        self.virtual_line_for_junction(lane, self.canvas.getLaneNodeSet(), self.canvas.getLaneBoundarySet())

                if link.lane_mark_right is not []:
                    lane = link.lane_mark_right[0]
                    if next((item for item in divide_lane_list if item.from_node == lane.from_node), None) is None:
                        divide_lane_list.append(lane)
                        self.virtual_line_for_junction(lane, self.canvas.getLaneNodeSet(), self.canvas.getLaneBoundarySet())

            start_ego_lane = None
            road_id_list = []
            for link in divide_link_list:
                new_link, is_start = self.copy_value_for_virtual_link(link)
                if new_link.road_id not in road_id_list:
                    road_id_list.append(new_link.road_id)
                if is_start:
                    start_ego_lane = new_link
            
            if len(road_id_list) == 1:
                current_link = start_ego_lane
                ego_lane = 1
                while current_link is not None:
                    current_link.ego_lane = ego_lane
                    ego_lane += 1

                    right_link = current_link.lane_ch_link_right
                    if right_link is not None and right_link.link_type == 'DRIVABLE_LANE':
                        current_link.can_move_right_lane = True
                    else:
                        current_link.can_move_right_lane = False
                        
                    left_link = current_link.lane_ch_link_left
                    if left_link is not None and left_link.link_type == 'DRIVABLE_LANE':
                        current_link.can_move_left_lane = True
                    else:
                        current_link.can_move_left_lane = False

                    # 차선변경 불가능
                    if current_link.link_type != 'DRIVABLE_LANE':
                        current_link.can_move_right_lane = False
                        current_link.can_move_left_lane = False

                    current_link = current_link.lane_ch_link_right
            
            Logger.log_info('[Junction Fix] End Junctions  →  Junction ID({}), Create new Road ({})'.format(item['id'], road_id_list))

        self.canvas.updateMgeoIdWidget()
        self.canvas.list_error = new_error_list


    def copy_value_for_virtual_link(self, link):
        if len(link.from_node.from_links) > 0:
            new_link = link.from_node.from_links[0]
            # if len(link.from_node.to_links) > 1:
            #     # 왼쪽 link
            #     left_here_link = next(item for item in link.from_node.to_links if item.can_move_right_lane == False and item.ego_lane != -1)
            #     left_link = left_here_link.lane_ch_link_left.from_node.from_links[0]
            #     new_link.set_left_lane_change_dst_link(left_link)

            #     # 왼쪽 lane
            #     left_lane = left_here_link.lane_mark_left[0].from_node.from_links[0]
            #     new_link.set_lane_mark_left(left_lane)

            #     # 오른쪽 link
            #     right_here_link = next(item for item in link.from_node.to_links if item.can_move_left_lane == False and item.ego_lane == -1)
            #     right_link = right_here_link.lane_ch_link_right.from_node.from_links[0]
            #     new_link.set_right_lane_change_dst_link(right_link)
                
            #     # 오른쪽 lane
            #     right_lane = right_here_link.lane_mark_right[0].from_node.from_links[0]
            #     new_link.set_lane_mark_right(right_lane)

            # else:
            #     if link.lane_ch_link_left is not None:
            #         left_link = link.lane_ch_link_left.from_node.from_links[0]
            #         new_link.set_left_lane_change_dst_link(left_link)

            #     if link.lane_ch_link_right is not None:
            #         right_link = link.lane_ch_link_right.from_node.from_links[0]
            #         new_link.set_right_lane_change_dst_link(right_link)
            #     left_lane = link.lane_mark_left[0].from_node.from_links[0]
            #     new_link.set_lane_mark_left(left_lane)
            #     right_lane = link.lane_mark_right[0].from_node.from_links[0]
            #     new_link.set_lane_mark_right(right_lane)
                        
            new_link.can_move_left_lane = link.can_move_left_lane
            new_link.can_move_right_lane = link.can_move_right_lane

            new_link.speed_unit = link.speed_unit
            new_link.speed_offset = []

            if new_link.lane_ch_link_left is None:
                return new_link, True
            else:
                return new_link, False


    def virtual_line_for_junction(self, line, node_set, line_set):
        p0 = line.points[0]
        p1 = line.points[1]
        vec = (p1-p0) / np.linalg.norm(p1-p0)
        new_point = p0 - vec

        point_idx = 1
        new_node = Node()
        new_node.point = new_point
        node_set.append_node(new_node, create_new_key=True)
        if type(line).__name__ == 'Link':

            self.canvas.virtual_link += 1
            new_link_id = 'VL{}'.format(self.virtual_link)

            new_line = Link(idx=new_link_id)
            Link.copy_attributes(line, new_line)
            new_line.link_type_def = line.link_type_def
            
        elif type(line).__name__ == 'LaneBoundary':

            self.canvas.virtual_lane += 1
            new_lane_id = 'VLM{}'.format(self.canvas.virtual_lane)

            new_line = LaneBoundary(idx=new_lane_id)
            LaneBoundary.copy_attribute(line, new_line)
            new_line.lane_type_def = line.lane_type_def

        new_line_points = np.vstack((new_point, line.from_node.point))
        new_line.set_points(new_line_points)
        new_line.set_from_node(new_node)
        new_line.set_to_node(line.from_node)

        line_set.append_line(new_line)

        return new_line

    # node on stop line == True 인 Node와 Lane Boundary 하이라이트
    def highlight_on_stop_line(self):
        Logger.log_trace('Called: find_on_stop_line')
        try:
            nodes = self.canvas.getNodeSet(self.canvas.mgeo_key).nodes
            lanes = self.canvas.getLaneBoundarySet(self.canvas.mgeo_key).lanes
            
            self.canvas.list_highlight2 = []
            for node in nodes.values():
                on_stop_line = node.on_stop_line
                if on_stop_line == None:
                    node.on_stop_line = False
                if on_stop_line:
                    sp_dict = {'type': MGeoItem.NODE, 'id': node.idx}
                    self.canvas.list_highlight2.append(sp_dict)

            for lane in lanes.values():
                on_stop_line = lane.lane_type[0]
                if on_stop_line == 530:
                    sp_dict = {'type': MGeoItem.LANE_BOUNDARY, 'id': lane.idx}
                    self.canvas.list_highlight2.append(sp_dict)

        except BaseException as e:
            Logger.log_error('find_on_stop_line failed (traceback below)\n{}'.format(traceback.format_exc()))



    def highlight_traffic_light_type_none(self):
        Logger.log_trace('Called: traffic_light_type_none')
        try:
            lights = self.canvas.getTLSet(self.canvas.mgeo_key).signals
            highlight_list = []
            for light in lights.values():
                if light.type not in ['car', 'bus', 'pedestrian']:
                    sp_dict = {'type': MGeoItem.TRAFFIC_LIGHT, 'id': light.idx}
                    highlight_list.append(sp_dict)
                elif light.type == 'car':
                    if light.sub_type is None or light.sub_type == '':
                        sp_dict = {'type': MGeoItem.TRAFFIC_LIGHT, 'id': light.idx}
                        highlight_list.append(sp_dict)
        except BaseException as e:
            Logger.log_error('traffic_light_type_none failed (traceback below)\n{}'.format(traceback.format_exc()))


        return highlight_list
