import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))
sys.path.append(os.path.normpath(os.path.join(current_path, '../../')))

import traceback

from lib.common.logger import Logger

from PyQt5 import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from lib.mgeo.class_defs import *
from lib.mgeo.class_defs.mgeo_item import MGeoItem
from lib.mgeo.edit.funcs import edit_node, edit_link, edit_signal, edit_junction, edit_mgeo_planner_map
from lib.mgeo.utils import error_fix

from GUI.feature_sets_base import BaseFeatureSet


class ErrorFix(BaseFeatureSet):
    def __init__(self, canvas):
        super(ErrorFix, self).__init__(canvas)

        # overlapped_node_set
        self.overlapped_node = []

        # dangling_nodes_set
        self.dangling_nodes = []


    # 에러 수정 기능
    def find_overlapped_node(self, act_repair, act_clear):
        Logger.log_trace('Called: find_overlapped_node')
        try:
            if self.getNodeSet() is None or len(self.getNodeSet().nodes) < 1 :
                QMessageBox.warning(self.canvas, "Warning", "There is no node data.")
                return

            self.overlapped_node = error_fix.search_overlapped_node(self.getNodeSet(), 0.1)
            for i in self.overlapped_node:
                for n in i:
                    self.canvas.list_error.append({'type': MGeoItem.NODE, 'id': n.idx})

            # overlapped_nodes에 node 유무에 따라 (repair_overlapped_node) menu action enable
            if self.overlapped_node is None or self.overlapped_node == []:
                QMessageBox.information(self.canvas, "Information", "No overlapped node is found.")
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
            if len(self.overlapped_node) < 1:
                QMessageBox.warning(self.canvas, "Warning", "There is no overlapped node to repair.")
                return

            nodes_of_no_use = error_fix.repair_overlapped_node(self.overlapped_node)
            edit_node.delete_nodes(self.getNodeSet(), nodes_of_no_use)

            # 불필요한 노드가 삭제되었으면 error list를 clear 시켜준다
            self.canvas.list_error.clear()
            self.overlapped_node = []

            act_repair.setDisabled(True)
            self.canvas.updateMgeoIdWidget()
            Logger.log_info('repair_overlapped_node done OK')
        except BaseException as e:
            Logger.log_error('repair_overlapped_node failed (traceback is down below) \n{}'.format(traceback.format_exc()))


    def find_dangling_nodes(self, act_repair, act_clear):
        Logger.log_trace('Called: find_dangling_nodes')
        try:
            if self.getNodeSet() is None or len(self.getNodeSet().nodes) < 1 :
                QMessageBox.warning(self.canvas, "Warning", "There is no node data.")
                return

            self.dangling_nodes = error_fix.find_dangling_nodes(self.getNodeSet())
            for node in self.dangling_nodes:
                self.canvas.list_error.append({'type': MGeoItem.NODE, 'id': node.idx})

            node_idx_string = '['
            for node in self.dangling_nodes:
                node_idx_string += '{}, '.format(node.idx)
            node_idx_string += ']'
            Logger.log_info('find_dangling_nodes result: {}'.format(node_idx_string))

            # dangling_nodes에 node 유/무에 따라 (delete_dangling_nodes) menu action enable
            if self.dangling_nodes is None or self.dangling_nodes == []:
                QMessageBox.information(self.canvas, "Information", "There is no dangling nodes to delete.")
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
            node_idx_string = '['
            for node in self.dangling_nodes:
                node_idx_string += '{}, '.format(node.idx)
            node_idx_string += ']'

            edit_node.delete_nodes(self.getNodeSet(), self.dangling_nodes)
            act_repair.setDisabled(True)
            self.canvas.updateMgeoIdWidget()
            Logger.log_info('dangling nodes ({}) deleted.'.format(node_idx_string))
        
        except BaseException as e:
            Logger.log_error('delete_item failed (traceback is down below) \n{}'.format(traceback.format_exc()))


    def find_closed_loop_link(self, act_clear):
        Logger.log_trace('Called: find_closed_loop_link')
        try:
            closed_loop_links = []
            for idx, link in self.canvas.getLinkSet().lines.items():
                if link.from_node is link.to_node:
                    closed_loop_links.append(link)
                    
            if len(closed_loop_links) == 0:
                # 찾은 결과가 없는 경우, 안내 후 종료.
                self.canvas.list_error.clear() # 기존에 clear 되지 않았던 오류가 있다면 clear한다
                
                QMessageBox.information(self.canvas, "Information", "No closed-loop link is found.")
                Logger.log_info('No closed-loop link is found')
                return 

            else:
                # 찾은 결과가 있을 경우, error_list에 추가한다
                for link in closed_loop_links:
                    # 찾은 결과가 있을 경우, error_list에 추가한다
                    self.canvas.list_error.append({'type': MGeoItem.LINK, 'id': link.idx})

                # 찾은 결과가 있으면, clear 기능을 활성화한다 
                act_clear.setDisabled(False)

                self.canvas.updateMgeoIdWidget()
                closed_loop_links_id_string = Link.get_id_list_string(closed_loop_links)
                Logger.log_info('{} closed-loop link(s) are found: {}'.format(len(closed_loop_links), closed_loop_links_id_string))
                return 

        except BaseException as e:
            Logger.log_error('find_closed_loop_link failed (traceback is down below) \n{}'.format(traceback.format_exc()))


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

