import os
import sys

from PyQt5.QtWidgets import *
from lib.openscenario.client.client_lib.defs import ControllerFrom

class StartScenarioDialog(QDialog):
    """
    Start Scenario Dialog. Select ego cruise mode.
    """
    def __init__(self):
        super().__init__()
        self.initUI()
        self.ego_is_cruised_by = ControllerFrom.MoraiSim_Drive

    def initUI(self):
        widgetLayout = QGridLayout()
        groupbox = QGroupBox("Ego Vehicle Controller")
        vbox = QVBoxLayout()

        rbtn_built_in = QRadioButton('Built-in', groupbox)
        rbtn_morai_sim_drive = QRadioButton('MORAI SIM: Drive', groupbox)
        rbtn_external = QRadioButton('External', groupbox)
        rbtn_morai_sim_drive.setChecked(True)

        self.button_group = QButtonGroup(groupbox)
        self.button_group.addButton(rbtn_built_in, ControllerFrom.BuiltIn.value)
        self.button_group.addButton(rbtn_morai_sim_drive, ControllerFrom.MoraiSim_Drive.value)
        self.button_group.addButton(rbtn_external, ControllerFrom.External.value)
        vbox.addWidget(rbtn_built_in)
        vbox.addWidget(rbtn_morai_sim_drive)
        vbox.addWidget(rbtn_external)
        groupbox.setLayout(vbox)
        widgetLayout.addWidget(groupbox, 0, 0)

        buttonbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonbox.accepted.connect(self.accept)
        buttonbox.rejected.connect(self.reject)

        widgetLayout.addWidget(buttonbox, 2, 0)
        
        self.setLayout(widgetLayout)
        self.setWindowTitle('Start Scenario') 

    def showDialog(self):
        return super().exec_()
        
    def accept(self):
        self.ego_is_cruised_by = ControllerFrom(self.button_group.checkedId())
        self.done(1)

    def close(self):
        self.done(0)