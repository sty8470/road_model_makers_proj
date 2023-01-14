import os
import sys

import json

from PyQt5 import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *


from lib.mgeo.utils.logger import Logger

class DisplayStyle:
    
    def __init__(self, canvas, config, config_file_path, widget):
        self.canvas = canvas
        self.config = config
        self.json_file_path = config_file_path
        self.tree_style = widget
        self.data_update = False
        self.tree_style.itemClicked.connect(self.update_display_state)
        
    def set_widget(self):
        self.tree_style.clear()
        for item_key, item_value in self.config['STYLE'].items():
            tree_item = QTreeWidgetItem(self.tree_style)
            tree_item.setText(0, item_key)
            if item_key == 'OpenSCENARIO' or item_key == 'MScenario':
                for sub_item, sub_value in item_value.items():
                    tree_sub_item = QTreeWidgetItem(tree_item)
                    tree_sub_item.setText(0, sub_item)
                    self.list_up_display(sub_value, tree_sub_item)
            else:
                self.list_up_display(item_value, tree_item)

    def list_up_display(self, item_value, tree_item):
        for prop_key, prop_value in item_value.items():
            prop_item = QTreeWidgetItem(tree_item)
            prop_item.setText(0, prop_key)

            if type(prop_value) == dict:
                for pp_key, pp_value in prop_value.items():
                    pp_item = QTreeWidgetItem(prop_item)
                    pp_item.setText(0, pp_key)
                    if type(pp_value) == list:
                        color = QBrush(QColor(pp_value[0]*255, pp_value[1]*255, pp_value[2]*255))
                        pp_item.setText(1, str(pp_value))
                        pp_item.setBackground(1, color)
                    else:
                        pp_item.setText(1, str(pp_value))
            else:
                if prop_value == True:
                    prop_item.setCheckState(1, Qt.Checked)
                elif prop_value == False:
                    prop_item.setCheckState(1, Qt.Unchecked)
                elif type(prop_value) == list:
                    color = QBrush(QColor(prop_value[0]*255, prop_value[1]*255, prop_value[2]*255))
                    prop_item.setText(1, str(prop_value))
                    prop_item.setBackground(1, color)
                else:
                    prop_item.setText(1, str(prop_value))
                    
    def update_display_state(self, item, column):
        select_item = item.text(0)
        item_title = None
        
        if select_item in ['VIEW', 'TEXT', 'GEO CHANGE', 'LANE CHANGE LINK']:
            if item.parent().parent() is not None and 'scenario' in item.parent().parent().text(0).lower():
                item_title = item.parent().parent().text(0)
            item1 = item.parent().text(0)
            item2 = item.text(0)
            if item.checkState(column) == Qt.Checked:
                new_state = True
                item.setCheckState(1, Qt.Checked)
            elif item.checkState(column) == Qt.Unchecked:
                new_state = False
                item.setCheckState(1, Qt.Unchecked)
            with open(self.json_file_path, 'w') as output:
                if item_title is not None:
                    self.config['STYLE'][item_title][item1][item2] = new_state
                else:
                    self.config['STYLE'][item1][item2] = new_state
                json.dump(self.config, output, indent=2)

        elif item.parent() is None:
            return

        else:
            if item.parent().parent() is not None and item.parent().parent().parent() is not None and 'scenario' in item.parent().parent().parent().text(0).lower():
                item_title = item.parent().parent().parent().text(0)
                
            result = None
            if 'COLOR' in select_item:
                result = self.openColorDialog()
                
            elif select_item in ['SIZE', 'WIDTH']:
                new_value, okPressed = QInputDialog.getText(self.canvas, "Mgeo Style", item.text(0), QLineEdit.Normal, item.text(1))
                if okPressed and new_value != '':
                    try :
                        result = int(new_value)
                    except Exception:
                        QMessageBox.warning("Warning", "Type Error, Please enter by number.")
                        pass
                else:
                    return
                
            elif select_item in ['POLY3 STYLE', 'LINE STYLE', 'PARAMPOLY3 STYLE']:
                items = ['Dot', 'Dash', 'DashDot', 'Solid']
                new_value, okPressed = QInputDialog.getItem(self.canvas, "Mgeo Style", item.text(0), items, items.index(item.text(1)), False)
                if okPressed and new_value != '':
                    result = new_value

            if result is not None:
                with open(self.json_file_path, 'w') as output:
                    if item_title is not None:
                        self.config['STYLE'][item_title][item.parent().parent().text(0)][item.parent().text(0)][item.text(0)] = result
                    else:
                        if item.parent().parent() is not None:
                            self.config['STYLE'][item.parent().parent().text(0)][item.parent().text(0)][item.text(0)] = result
                        elif item.parent():
                            self.config['STYLE'][item.parent().text(0)][item.text(0)] = result
                    json.dump(self.config, output, indent=2)
                self.set_widget()
        
        self.data_update = True
        
    def openColorDialog(self):
        color = QColorDialog.getColor()
        if color.isValid():
            rgb_color = [color.red()/255, color.green()/255, color.blue()/255]
            return rgb_color
        else:
            return None
