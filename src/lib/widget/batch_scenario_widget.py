import os

from PyQt5 import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

import xml.etree.ElementTree as ET
import json

from lib.common.logger import Logger

class BatchScenarioWidget:
    def __init__(self, file_io_funcs, btn_load, btn_save,
                       btn_add, btn_del, btn_upward, btn_downward,
                       btn_select_all, btn_start, btn_stop, btn_skip, table_widget):
        # Initialize member variables
        self.file_io_funcs = file_io_funcs
        self.table_widget:QTableWidget = table_widget
        self.is_batch_simulation_start = False
        self.btn_start = btn_start
        self.btn_stop = btn_stop
        self.btn_skip = btn_skip
        # Set widget options
        self.table_widget.setColumnWidth(0, 40)
        self.table_widget.setColumnWidth(1, 120)
        self.set_start_status(False)
        # Set button handlers
        btn_load.clicked.connect(lambda:self.__load_test_suite())
        btn_save.clicked.connect(lambda:self.__save_test_suite())
        btn_add.clicked.connect(lambda:self.__add_test_scenario())
        btn_del.clicked.connect(lambda:self.__delete_test_scenario())
        btn_upward.clicked.connect(lambda:self.__move_scenario_upward())
        btn_downward.clicked.connect(lambda:self.__move_scenario_downward())
        btn_select_all.clicked.connect(lambda:self.__select_all_scenario())
        # Set context menu
        self.table_widget.setContextMenuPolicy(Qt.ActionsContextMenu)
        self.context_action_load = QAction("Load Scenario", self.table_widget)
        self.context_action_run = QAction("Run Simulation", self.table_widget)
        self.table_widget.addAction(self.context_action_load)
        self.table_widget.addAction(self.context_action_run)
    
    def get_test_scenario_selected(self):
        try:
            selected_row = self.table_widget.currentRow()
            if selected_row < 0:
                raise Exception("No row has selected")
            file_path = self.table_widget.item(selected_row, 1).data(Qt.ToolTipRole)
            if not os.path.exists(file_path):
                raise FileExistsError("{}".format(file_path))
            return file_path
        except FileExistsError as e:
            QMessageBox.warning(self.table_widget, "Warning", "The selected file doesn't exist ({})".format(e))
            return None
        except BaseException as e:
            Logger.log_warning("{}".format(e))
            return None

    def get_test_scenarios(self):
        try:
            scenario_file_list = []
            row_count = self.table_widget.rowCount()
            for idx in range(row_count):
                if self.table_widget.item(idx, 0).checkState() == Qt.Unchecked:
                    continue
                file_path = self.table_widget.item(idx, 1).data(Qt.ToolTipRole)
                if not os.path.exists(file_path):
                    raise FileExistsError("{}".format(file_path))

                scenario_file_list.append(file_path)
            return scenario_file_list
        except FileExistsError as e:
            QMessageBox.warning(self.table_widget, "Warning", "Scenario file doesn't exist ({})".format(e))
            return []
        except BaseException as e:
            Logger.log_warning("{}".format(e))
            return []
    
    def is_start(self):
        return self.is_batch_simulation_start
    
    def set_highlight(self, highlight_path:str):
        row_count = self.table_widget.rowCount()
        font_bold = QFont()
        font_bold.setBold(True)
        font_regular = QFont()
        font_regular.setBold(False)
        for idx in range(row_count):
            widget_item = self.table_widget.item(idx, 1)
            file_path = widget_item.data(Qt.ToolTipRole)
            if file_path == highlight_path:
                widget_item.setFont(font_bold)
            else:
                widget_item.setFont(font_regular)

    def set_start_status(self, status:bool):
        self.is_batch_simulation_start = status
        self.btn_start.setEnabled(not status)
        self.btn_stop.setEnabled(status)
        self.btn_skip.setEnabled(status)

    def __add_test_scenario(self):
        # Get filename
        filepath_list = self.file_io_funcs.get_open_filenames("Select scenario files",
                                                              'OpenScenario_IMPORT', 'xosc')
        if not filepath_list:
            return
        # Add new scenario
        row_count = self.table_widget.rowCount()
        self.table_widget.setRowCount(row_count + len(filepath_list))   # filepath_list 개수 만큼 row 확장
        for i, filepath in enumerate(filepath_list):
            idx = row_count + i
            self._add_test_scenario_to_table(idx, filepath)
    
    def _add_test_scenario_to_table(self, idx, file_path, skip=False):
        # 1. Checkbox
        item_index = QTableWidgetItem(str(idx+1))
        item_index.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
        if skip:
            item_index.setCheckState(Qt.Unchecked)
        else:
            item_index.setCheckState(Qt.Checked)
        self.table_widget.setItem(idx, 0, item_index)
        # 2. File name
        item_path = QTableWidgetItem()
        item_path.setData(Qt.ToolTipRole, file_path)
        item_path.setData(Qt.DisplayRole, os.path.basename(file_path).split('.')[0])
        self.table_widget.setItem(idx, 1, item_path)
        # 3. Map name
        tree = ET.parse(file_path)
        map_element = tree.find('SimulatorInfo/Map')
        if map_element is not None and 'name' in map_element.attrib:
            self.table_widget.setItem(idx, 2, QTableWidgetItem(map_element.attrib['name']))
        # 4. Description
        header_element = tree.find('FileHeader')
        if header_element is not None and 'description' in header_element.attrib:
            self.table_widget.setItem(idx, 3, QTableWidgetItem(header_element.attrib['description']))
    
    def __clear(self):
        self.table_widget.setRowCount(0)
    
    def __delete_test_scenario(self):
        selected_row = self.table_widget.currentRow()
        selected_col = self.table_widget.currentColumn()
        # Delete the selected row
        self.table_widget.removeRow(self.table_widget.currentRow())
        # Re-index
        row_count = self.table_widget.rowCount()
        for idx in range(row_count):
            self.table_widget.item(idx, 0).setText(str(idx+1))
        # Keep selected cell
        self.table_widget.setCurrentCell(selected_row, selected_col)

    def __load_test_suite(self):
        # Get filename
        open_filename = self.file_io_funcs.get_open_filename("Select a test-suite file",
                                                             'OpenScenario_IMPORT', 'json')
        if not open_filename:
            return
        # Parse data
        try:
            with open(open_filename) as f:
                data = json.load(f)
        
            if data['type'] != "Scenario Runner Test Suite":
                raise TypeError("Invalid Test Suite")
            
            if data['workspace_path'] != 'Absolute':
                raise TypeError("Only absolute path is supported currently")

            self.__clear()
            self.table_widget.setRowCount(len(data['test_scenarios']))
            for idx, testcase in enumerate(data['test_scenarios']):
                if not os.path.exists(testcase['filepath']):
                    raise FileExistsError("Scenario file doesn't exist ({})".format(testcase['filepath']))
                self._add_test_scenario_to_table(idx, testcase['filepath'], (testcase['skip'] == 'True'))
        except FileExistsError as e:
            self.__clear()
            QMessageBox.warning(self.table_widget, "Warning", "{}".format(e))
        except TypeError as e:
            self.__clear()
            QMessageBox.warning(self.table_widget, "Warning", "Failed to load a test-suite: {}".format(str(e)))
        except BaseException as e:
            self.__clear()
            QMessageBox.warning(self.table_widget, "Warning", "Failed to load a test-suite")

    def __move_scenario_upward(self):
        selected_row = self.table_widget.currentRow()
        selected_col = self.table_widget.currentColumn()
        if selected_row <= 0:
            return

        col_count = self.table_widget.columnCount()
        for idx in range(1, col_count):
            selected_item = QTableWidgetItem(self.table_widget.item(selected_row, idx))
            upper_item = QTableWidgetItem(self.table_widget.item(selected_row-1, idx))
            self.table_widget.setItem(selected_row, idx, upper_item)
            self.table_widget.setItem(selected_row-1, idx, selected_item)
        self.table_widget.setCurrentCell(selected_row-1, selected_col)

    def __move_scenario_downward(self):
        selected_row = self.table_widget.currentRow()
        selected_col = self.table_widget.currentColumn()
        row_count = self.table_widget.rowCount()
        if selected_row >= row_count-1:
            return

        col_count = self.table_widget.columnCount()
        for idx in range(1, col_count):
            selected_item = QTableWidgetItem(self.table_widget.item(selected_row, idx))
            lower_item = QTableWidgetItem(self.table_widget.item(selected_row+1, idx))
            self.table_widget.setItem(selected_row, idx, lower_item)
            self.table_widget.setItem(selected_row+1, idx, selected_item)
        self.table_widget.setCurrentCell(selected_row+1, selected_col)

    def __save_test_suite(self):
        row_count = self.table_widget.rowCount()
        if row_count <= 0:
            QMessageBox.warning(self.table_widget, "Warning", "Failed to save a test-suite: The list is empty")
            return
        
        # Get filename
        save_filename = self.file_io_funcs.get_save_filename("Save file", 'OpenScenario_SAVE',
                                                        'json', "JSON files (*.json)")
        if not save_filename:
            return
        # Generate json data
        data = {'type': "Scenario Runner Test Suite",
                'description': "",
                'option': {},
                'workspace_path': 'Absolute',
                'test_scenarios': [] }
        for idx in range(row_count):
            file_path = self.table_widget.item(idx, 1).data(Qt.ToolTipRole)
            skip = (self.table_widget.item(idx, 0).checkState() == Qt.Unchecked)
            data['test_scenarios'].append({'filepath': file_path, 'skip': str(skip)})
        # Save as a json file
        with open(save_filename, "w", encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    def __select_all_scenario(self):
        # Check all rows if not all rows are checked
        # OR, Uncheck all rows if all rows are checked
        row_count = self.table_widget.rowCount()
        all_checked = True
        for idx in range(row_count):
            item = self.table_widget.item(idx, 0)
            all_checked &= (item.checkState() == Qt.Checked)
        
        new_state = Qt.Checked if all_checked == False else Qt.Unchecked
        for idx in range(row_count):
            item = self.table_widget.item(idx, 0)
            item.setCheckState(new_state)