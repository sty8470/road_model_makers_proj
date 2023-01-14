import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path) # 현재 경로 추가
sys.path.append(os.path.normpath(os.path.join(current_path, '../'))) # mgeo가 있는 경로

import numpy as np

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtCore import Qt, QMetaObject
from PyQt5.QtWidgets import *

from lib.mgeo.class_defs import *
from lib.mgeo.edit import core
import mpl_user_input_handler


class MPLCanvas(FigureCanvas):

    def __init__(self, initial_dir = './'):
        self.fig = plt.figure()
        self.fig.set_size_inches(12,12)
        ax = self.fig.add_subplot(111)

        FigureCanvas.__init__(self, self.fig)
        FigureCanvas.setSizePolicy(self, QSizePolicy.Expanding, QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

        # 편집 기능을 제공하는 클래스
        self.edit_core = core.MGeoEditCore()

        # 사용자 입력에 따른 콜백을 처리하기 위한 클래스 인스턴스
        # NOTE: 반드시 FigureCanvas.__init__ 부분이 호출되고 난 다음에 UserInputHandler를 생성해야함
        #       내부적으로 fig.canvas.mpl_connect 를 호출하게 되는데, FigureCanvas.__init__ 전에
        #       이 부분을 실행하면 사용자 입력에 대한 callback이 호출되지 않는다.
        self.callback = mpl_user_input_handler.UserInputHandler(self.edit_core, self.fig)


    def set_data(self, node_set, link_set):        
        self.list_node = node_set
        self.list_link = link_set   

        mgeo_planner_map = MGeo(self.list_node, self.list_link)
        self.edit_core.set_geometry_obj(mgeo_planner_map)
        self.callback.update_plot(plt.gcf(), plt.gca(), draw=True)   


    def set_node_data(self, node_set):        
        self.list_node = node_set     

        self.callback.set_geometry_obj(self.list_link, self.list_node)
        self.callback.update_plot(plt.gcf(), plt.gca(), raw=True)   


    def set_link_data(self, link_set):
        self.list_link = link_set

        self.callback.set_geometry_obj(self.list_link, self.list_node)
        self.callback.update_plot(plt.gcf(), plt.gca(), draw=True)