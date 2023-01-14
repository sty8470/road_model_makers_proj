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

from mgeo_odr_converter import MGeoToOdrDataConverter
from xodr_data import OdrData

from GUI.feature_sets_base import BaseFeatureSet


class OdrConversion(BaseFeatureSet):
    def __init__(self, canvas):
        super(OdrConversion, self).__init__(canvas)
        self.odr_persistent_data = None


    def clear_odr_roads(self):
        """
        생성되어 있는 odr road를 지운다. 링크를 삭제하면서 Road를 삭제할 때, 그에 따른 Ref Line이 삭제되지 않는 문제가 있을 때 사용 할 수 있다.
        """
        Logger.log_trace('Called: clear_odr_roads')
        try:
            # 링크에 있는 데이터 초기화
            for link in self.canvas.getLinkSet().lines.values():
                edit_link.reset_odr_conv_variables(link)

            # odr data 변수에 새로운 값 할당
            self.canvas.odr_data = OdrData()

            # widget update
            self.canvas.updateMgeoIdWidget()

            Logger.log_info('clear_odr_roads is done successfully.')
            return

        except BaseException as e:
            Logger.log_error('clear_odr_roads failed (traceback is down below) \n{}'.format(traceback.format_exc()))


    def create_prelimiary_odr_roads(self):
        """
        각 link에 있는 Road ID 만을 이용하여 OdrRoad 클래스 인스턴스와 이를 포함하는 OdrData 클래스 인스턴스를 생성한다.
        (즉, Ref Line, Lane Section 등은 설정되지 않는다)
        """
        Logger.log_trace('Called: create_odr_road_prelimiary')
        try:
            link_set = self.getLinkSet()

            converter = MGeoToOdrDataConverter.get_instance()
            self.canvas.odr_data = converter.create_preliminary_odr_roads(link_set)

            self.canvas.updateMgeoIdWidget()

            Logger.log_info('create_prelimiary_odr_roads is done successfully.')
            return self.canvas.odr_data

        except BaseException as e:
            Logger.log_error('create_prelimiary_odr_roads failed (traceback is down below) \n{}'.format(traceback.format_exc()))


    def create_odr_roads(self):
        """
        Ref Line, Lane Section 등 모든 데이터를 포함한 OdrRoad 클래스 인스턴스와 이를 포함하는 OdrData 클래스 인스턴스를 생성한다.
        """    
        Logger.log_trace('Called: create_odr_roads')
        try:
            import time
            start = time.time()

            link_set = self.getLinkSet()

            converter = MGeoToOdrDataConverter.get_instance()
            self.canvas.odr_data = converter.create_odr_roads(link_set)
            self.odr_persistent_data = self.canvas.odr_data

            self.canvas.updateMgeoIdWidget()

            end = time.time()
            print('Elapsed Time: {} sec'.format(end - start))
            Logger.log_info('create_odr_roads is done successfully.')
            return self.canvas.odr_data

        except BaseException as e:
            Logger.log_error('create_odr_roads failed (traceback is down below) \n{}'.format(traceback.format_exc()))


    def create_complete_odr_data(self, odr_widget):
        # ODR 생성 시 옵션 선택할 수 있도록 변경
        odr_widget.showDialog()
        # include_signal=True, fix_signal_road_id=False

        # ODR 생성 시 옵션 선택 팝업창에서 취소하면 취소
        if odr_widget.result() > 0:
            Logger.log_trace('Called: create_complete_odr_data')
            try:
                import time
                start = time.time()

                mgeo_planner_map = self.canvas.mgeo_planner_map
                # widget에서 받은 값으로 OpenDRIVE 변환 옵션 설정 
                converter = MGeoToOdrDataConverter.get_instance()
                converter.set_config_all(odr_widget.getOpenDRIVEConversionConfig())
                
                # OpenDRIVE 변환
                if self.odr_persistent_data != self.canvas.odr_data:
                    self.odr_persistent_data = None
                self.canvas.odr_data = converter.convert(mgeo_planner_map, self.odr_persistent_data)
                self.canvas.updateMgeoIdWidget()
                self.odr_persistent_data = self.canvas.odr_data
                end = time.time()
                print('Elapsed Time: {} sec'.format(end - start))
                Logger.log_info('create_complete_odr_data is done successfully')
                return self.canvas.odr_data

            except BaseException as e:
                Logger.log_error('create_complete_odr_data failed (traceback is down below) \n{}'.format(traceback.format_exc()))

