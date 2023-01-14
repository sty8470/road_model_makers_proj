import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))


from mpl_canvas import MPLCanvas

from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtCore import Qt, QMetaObject
from PyQt5.QtWidgets import *

import numpy as np

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

from lib.mgeo.class_defs import *
from lib.mgeo.test_common import test_cases_planner_map


class MplWidget(QtWidgets.QWidget):

    def __init__(self, parent = None):
        QtWidgets.QWidget.__init__(self, parent)

        self.canvas = MPLCanvas()
        self.toolbar = NavigationToolbar(self.canvas, self)

        self.canvas.setFocusPolicy( Qt.ClickFocus )
        self.canvas.setFocus()

        self.vbl = QVBoxLayout()
        self.vbl.addWidget(self.toolbar)
        self.vbl.addWidget(self.canvas)

        self.setLayout(self.vbl)


class PyQTWindow(QtWidgets.QMainWindow):

    def __init__(self, parent = None):
        super(PyQTWindow, self).__init__(parent)
        self.createUI(self)

    def createUI(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 600)

        # action 때문에 우선 생성해야한다
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.mpl = MplWidget(self.centralwidget)


        # menubar 만들기(Layout)
        menubar = self.menuBar()
        menubar.setNativeMenuBar(False)
        filesMenu = menubar.addMenu('&Files')
        importMenu = menubar.addMenu('&Import')
        exportMenu = menubar.addMenu('&Export')
        editMenu = menubar.addMenu('&Edit')
        laneMeshGenMenu = menubar.addMenu('&Lane Mesh Gen')
        viewMenu = menubar.addMenu('&View')
        infoMenu = menubar.addMenu('&Info')


        # action 만들기
        loadMGeoAction = QAction('Load MGeo', self)
        loadMGeoAction.triggered.connect(
            self.mpl.canvas.callback.load_mgeo)

        saveMGeoAction = QAction('Save MGeo', self)
        saveMGeoAction.triggered.connect(
            self.mpl.canvas.callback.save_mgeo)

        loadLaneMarkingAction = QAction('Load Lane Marking MGeo', self)
        loadLaneMarkingAction.triggered.connect(
            self.mpl.canvas.callback.load_lane_marking_data)    

        exitAction = QAction('Exit', self)
        exitAction.triggered.connect(qApp.quit)

        importNGII1Action = QAction('Import NGII Shp Ver1', self)
        importNGII1Action.triggered.connect(
            self.mpl.canvas.callback.import_ngii_shp1
        )

        importNGII1LaneMarkingAction = QAction('Import NGII Shp Ver1 (Lane Marking Data)', self)
        importNGII1LaneMarkingAction.triggered.connect(
            self.mpl.canvas.callback.import_ngii_shp1_lane_marking
        )

        importNGII2Action = QAction('Import NGII Shp Ver2', self)
        importNGII2Action.triggered.connect(
            self.mpl.canvas.callback.import_ngii_shp2)

        importCode42Action = QAction('Import CODE42 HDMap', self)
        importCode42Action.triggered.connect(
            self.mpl.canvas.callback.import_code42_hdmap)

        importGeoJsonAction = QAction('Import GeoJson', self)
        importGeoJsonAction.triggered.connect(
            self.mpl.canvas.callback.import_geojson)

        exportMapBuildDataAllAction = QAction('Simulation Map Build Data (All)', self)
        exportMapBuildDataAllAction.triggered.connect(
            self.mpl.canvas.callback.export_map_build_data_all
        )
        
        exportMapBuildDataTSAction = QAction('Simulation Map Build Data (TS only)', self)
        exportMapBuildDataTSAction.triggered.connect(
            self.mpl.canvas.callback.export_map_build_data_ts
        )

        exportMapBuildDataTLAction = QAction('Simulation Map Build Data (TL only)', self)
        exportMapBuildDataTLAction.triggered.connect(
            self.mpl.canvas.callback.export_map_build_data_tl
        )

        exportMapBuildDataSMAction = QAction('Simulation Map Build Data (SM only)', self)
        exportMapBuildDataSMAction.triggered.connect(
            self.mpl.canvas.callback.export_map_build_data_sm
        )
        

        deleteObjectsOutOfXYRangeAction = QAction('Delete Objects out of XY Range', self)
        deleteObjectsOutOfXYRangeAction.triggered.connect(
            self.mpl.canvas.callback.delete_objects_out_of_xy_range)

        deleteObjectsInsideTheScreenAction = QAction('Delete Objects inside this Screen', self)
        deleteObjectsInsideTheScreenAction.triggered.connect(
            self.mpl.canvas.callback.delete_object_inside_xy_range)
        
        deleteDanglingNodesAction = QAction('Delete Dangling Nodes', self)
        deleteDanglingNodesAction.triggered.connect(
            self.mpl.canvas.callback.delete_danling_nodes)

        createLaneChangeLinksAction = QAction('Create Lane Change Links', self)
        createLaneChangeLinksAction.triggered.connect(
            self.mpl.canvas.callback.create_lane_change_link_set)

        changeOriginAction = QAction('Change Origin', self)
        changeOriginAction.triggered.connect(
            self.mpl.canvas.callback.change_origin)

        fillPointsInLinksAction = QAction('Fill Points in Links', self)
        fillPointsInLinksAction.triggered.connect(
            self.mpl.canvas.callback.fill_points_in_links)

        ##########

        findAndFixOverlappedNodeAction = QAction('Find & Fix Overlapped Node', self)
        findAndFixOverlappedNodeAction.triggered.connect(
            self.mpl.canvas.callback.find_and_fix_overlapped_node)

        simplifyLaneMarkingsAction = QAction('Simplify Lane Markings', self)
        simplifyLaneMarkingsAction.triggered.connect(
            self.mpl.canvas.callback.simplify_lane_markings)

        fillPointsInLaneMarkingsAction = QAction('Fill Points in Lane Markings', self)
        fillPointsInLaneMarkingsAction.triggered.connect(
            self.mpl.canvas.callback.fill_points_in_lane_markings)

        exportLaneMeshAction = QAction('Export Lane Mesh', self)
        exportLaneMeshAction.triggered.connect(
            self.mpl.canvas.callback.export_lane_mesh2)


        ##########

        toggleNodeAction =  QAction('Toggle Node View', self)
        toggleNodeAction.triggered.connect(
            self.mpl.canvas.callback.toggle_node)

        toggleNodeTextAction = QAction('Toggle Node Text View', self)
        toggleNodeTextAction.triggered.connect(
            self.mpl.canvas.callback.toggle_node_text)

        toggleSignalAction =  QAction('Toggle Signal View', self)
        toggleSignalAction.triggered.connect(
            self.mpl.canvas.callback.toggle_signal)
        
        toggleSignalTextAction = QAction('Toggle Signal Text View', self)
        toggleSignalTextAction.triggered.connect(
            self.mpl.canvas.callback.toggle_signal_text)

        toggleSurfaceMarkingAction =  QAction('Toggle Surface Marking View', self)
        toggleSurfaceMarkingAction.triggered.connect(
            self.mpl.canvas.callback.toggle_surface_marking)

        toggleSurfaceMarkingTextAction = QAction('Toggle Surface Marking Text View', self)
        toggleSurfaceMarkingTextAction.triggered.connect(
            self.mpl.canvas.callback.toggle_surface_marking_text)

        softwareInfoAction = QAction('Software Infomation', self)


        # menu, action 연결
        filesMenu.addAction(loadMGeoAction)
        filesMenu.addAction(saveMGeoAction)
        filesMenu.addAction(loadLaneMarkingAction)
        filesMenu.addAction(exitAction)
        
        importMenu.addAction(importNGII1Action)
        importMenu.addAction(importNGII1LaneMarkingAction)
        importMenu.addAction(importNGII2Action)
        importMenu.addAction(importCode42Action)
        importMenu.addAction(importGeoJsonAction)

        exportMenu.addAction(exportMapBuildDataAllAction)
        exportMenu.addAction(exportMapBuildDataTSAction)
        exportMenu.addAction(exportMapBuildDataTLAction)
        exportMenu.addAction(exportMapBuildDataSMAction)

        editMenu.addAction(deleteObjectsOutOfXYRangeAction)
        editMenu.addAction(deleteObjectsInsideTheScreenAction)
        editMenu.addAction(deleteDanglingNodesAction)
        editMenu.addAction(createLaneChangeLinksAction)
        editMenu.addAction(changeOriginAction)
        editMenu.addAction(fillPointsInLinksAction)
    

        laneMeshGenMenu.addAction(findAndFixOverlappedNodeAction)
        laneMeshGenMenu.addAction(simplifyLaneMarkingsAction)
        laneMeshGenMenu.addAction(fillPointsInLaneMarkingsAction)
        laneMeshGenMenu.addAction(exportLaneMeshAction)

        viewMenu.addAction(toggleNodeAction)
        viewMenu.addAction(toggleNodeTextAction)
        viewMenu.addAction(toggleSignalAction)
        viewMenu.addAction(toggleSignalTextAction)
        viewMenu.addAction(toggleSurfaceMarkingAction)
        viewMenu.addAction(toggleSurfaceMarkingTextAction)

        infoMenu.addAction(softwareInfoAction)



        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.mpl.sizePolicy().hasHeightForWidth())
        self.mpl.setSizePolicy(sizePolicy)
        self.mpl.setObjectName("mpl")
        self.verticalLayout.addWidget(self.mpl)
        MainWindow.setCentralWidget(self.centralwidget)
        
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        MainWindow.setWindowTitle("PyQT MainWindow")
        QMetaObject.connectSlotsByName(MainWindow)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    qtWindow = PyQTWindow()

    # 테스트용으로 미리 한 세트의 데이터를 로드한다
    node_set, link_set = test_cases_planner_map.load_test_case_001()
    qtWindow.mpl.canvas.set_data(node_set, link_set)

    qtWindow.show()
    sys.exit(app.exec_())