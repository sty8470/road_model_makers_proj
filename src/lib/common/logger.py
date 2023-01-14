#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from os.path import join, getsize, isfile, isdir, splitext
import sys
import time
import shutil

from lib.common.log_type import LogType
from PyQt5.QtCore import QThread, pyqtSignal

class Logger(QThread):
    log_update = pyqtSignal(dict)
    instance = None

    def __init__(self, log_file_path=None, log_widget=None):
        super().__init__()
        # save file path(main path)
        # open save file
        # save log message
        # close save file
        # 다른 파일에서도 바로바로 접근할 수 있게
        # 1. 파일에 저장하는 함수
        # 2. 파일에 내용 불러와서 widget 화면에 
        # widget 화면에도 표시해야하고, 파일에 저장까지 해야하는데
        # 파일에 저장을 먼저 하고
        # 화면에 표시하기 전부 canvas랑 연결되어 있는데,
        logger_thread = self
        logger_thread.log_update.connect(self.save_msg)

        self.ctime = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))

        if log_file_path is None:
            # caller에서 전달된 log_file_path가 없으면 이렇게 생성한다.
            this_file_path = os.path.dirname(os.path.realpath(__file__))
            log_file_path = os.path.normpath(os.path.join(this_file_path, '../log')) 
        if not os.path.exists(log_file_path):
            os.makedirs(log_file_path) # recursive하게 os.mkdir을 호출한다

        self.log_file_path = os.path.normpath(log_file_path)
        self.file_name = os.path.normpath(os.path.join(log_file_path, 'log_{}.log'.format(self.ctime))) 
        self.log_widget = log_widget
        if self.log_widget is not None:
            self.log_widget.collapsible.combobox.currentTextChanged.connect(self.on_log_filter_level_changed)
            self.log_widget.collapsible.clearBtn.clicked.connect(self.clear_log_history)
        
        self.log_history = list() # 현재까지의 모든 log data
        self.log_filter_criterion = 30 # INFO의 log level 이다.
        
        self.check_folder_size()
        self.open_log_file()


    def check_folder_size(self):
        TotalSize = 0
        file_path = self.log_file_path
        for item in os.walk(file_path):
            for file in item[2]:
                try:
                    TotalSize = TotalSize + getsize(join(item[0], file))
                except:
                    print("error with file:  " + join(item[0], file))

        if TotalSize/(1024*1024) > 100: # 폴더 용량 체크
            file_name_and_time_lst = []
            for f_name in os.listdir('{}'.format(file_path)):
                written_time = os.path.getctime('{}\\{}'.format(file_path, f_name))
                file_name_and_time_lst.append((f_name, written_time))
            sorted_file_list = sorted(file_name_and_time_lst, key=lambda x: x[1], reverse=False)
            old_file = sorted_file_list[0]
            os.remove(join(file_path, old_file[0]))


    def open_log_file(self):
        with open(self.file_name, "w") as log_file:
            log_file.write(self.file_name + '\n\t\t')


    def save_msg(self, log_msg):
        """
        로그를 UI에 업데이트하고 파일로 저장하는 메서드
        """
        # 실제 로그 메세지는 log_msg['msg']에 포함되어 있고, 이는 multi-line이다.
        # 다음과 같이 포맷팅한다
        # - QTextEdit에서의 출력을 위해 LineBreak 문자를 <br>로 변경
        # - [INFO], [WARNING] 등을 붙여준다
        # - WARNING, ERROR에 대해 색상을 붙여준다
        # print_msg = '[{}] {}'.format(log_msg['type'], log_msg['msg'].replace('\n', '<br>'))

        print_msg = ''

        try:
            print_msg = '[{}] {}'.format(log_msg['type'], log_msg['msg'].replace('\n', '<br>'))
        except:
            return
        
        # style_msg에는 <br>을 붙이지 않는다 -> 아래에서 QTextEdit 인스턴스에 append로 UI에 출력할 예정이기때문.
        # (끝에 <br>이 붙어있으면, 줄을 두 번 띄우게 된다)
        if log_msg['type'] == "ERROR":
            style_msg = "<span style=\"color:#ff0000;\">{}</span>".format(print_msg)
        elif log_msg['type'] == "WARNING":
            style_msg = "<span style=\"color:#ff6633;\">{}</span>".format(print_msg)
        else:
            style_msg = "<span>{}</span>".format(print_msg)

        
        # 전체 로그 데이터에 추가하기
        log_msg['style_msg'] = style_msg # 위에서 formatting 해준 msg를 추가한다
        self.log_history.append(log_msg)
        
        # UI 업데이트 (log filter의 level과 현재 메세지의 level을 비교하여 UI를 업데이트)
        if log_msg['type_level'] >= self.log_filter_criterion: 
            if self.log_widget is not None:
                
                # [Logger UI #1] 가장 최근 Log 만 보여주는 공간
                # msg가 multi-line인 경우, 첫번째 줄만 출력한다
                msg_split_by_line = print_msg.split('<br>')
                self.log_widget.collapsible.setText(msg_split_by_line[0])                    
                
                # [Logger UI #2] 현재까지 모든 Log를 보여주는 공간
                self.log_widget.text_area.append(style_msg)
                # NOTE: 아래는 사용 가능한 다른 함수들인데, 사용하지 않게 된 이유들이다.
                # self.log_widget.text_area.setText(str(self.log_filtered)) >> 매우 느림, log_filtered 변수는 현재 필터 기준, 필터링된 log history이다  
                # self.log_widget.text_area.insertPlainText(style_msg) >> 포맷을 인식하지 못함
                # self.log_widget.text_area.insertHtml(style_msg) >> 매우 느림

                # 현재 스크롤바의 위치와 비교해서 위치 이동
                lock_point = self.log_widget.scrollbar.sliderPosition()
                if self.log_widget.scrollbar.maximum() > lock_point > 0:
                    self.log_widget.scrollbar.setValue(lock_point)
                else:
                    self.log_widget.scrollbar.setValue(self.log_widget.scrollbar.maximum())

        # 파일에 작성하기 (log filter의 level과 관계없이 작성)
        with open(self.file_name, "a") as log_file:
            # seperator를 tab 문자로 하여 저장. (comma 사용 시, traceback message 가 문제가 됨)
            # 한편, log_msg['msg'] 내부가 multiline인 경우가 있으므로, 줄바꿈 이후에 \t\t 이 들어와야 로그파일을 볼 때 정상적으로 볼 수 있다
            msg = '{}\t{}\t{}'.format(log_msg['type'], log_msg['time'], log_msg['msg'].replace('\n', '\n\t\t'))
            log_file.write(msg + '\n')


    def clear_log_history(self):
        """
        현재까지 저장된 log history와 UI를 clear한다
        """
        self.log_history = list()
        self.log_widget.text_area.setText('')


    def on_log_filter_level_changed(self, tag=None):
        """
        UI에서 Log Level을 변경하면 호출되는 callback 메서드
        """
        # 'DEBUG', 'TRACE', 'INFO', 'WARNING', 'ERROR'
        self.log_filter_criterion = LogType[tag].value
        self.update_log_history_ui()


    def update_log_history_ui(self):
        """
        UI에서 Log Level이 변경되었을 때, Log History 창을 업데이트한다
        """
        display_msg = ''
        for log_msg in self.log_history:
            if log_msg['type_level'] >= self.log_filter_criterion:
                display_msg += log_msg['style_msg'] + '<br>'

        self.log_widget.text_area.setText(display_msg)


    def _log_debug(self, msg):
        ctime = time.strftime('%Y-%m-%d %X', time.localtime(time.time()))
        log_msg = {'type':'DEBUG', 'time':ctime, 'msg':msg, 'type_level':10}
        # self.save_msg(log_msg)
        self.log_update.emit(log_msg)

    def _log_trace(self, msg):
        ctime = time.strftime('%Y-%m-%d %X', time.localtime(time.time()))
        log_msg = {'type':'TRACE', 'time':ctime, 'msg':msg, 'type_level':20}
        # self.save_msg(log_msg)
        self.log_update.emit(log_msg)


    def _log_info(self, msg):
        ctime = time.strftime('%Y-%m-%d %X', time.localtime(time.time()))
        log_msg = {'type':'INFO', 'time':ctime, 'msg':msg, 'type_level':30}
        # self.save_msg(log_msg)
        self.log_update.emit(log_msg)

    def _log_warning(self, msg):
        ctime = time.strftime('%Y-%m-%d %X', time.localtime(time.time()))
        log_msg = {'type':'WARNING', 'time':ctime, 'msg':msg, 'type_level':40}
        # self.save_msg(log_msg)
        self.log_update.emit(log_msg)


    def _log_error(self, msg):
        ctime = time.strftime('%Y-%m-%d %X', time.localtime(time.time()))
        log_msg = {'type':'ERROR', 'time':ctime, 'msg':msg, 'type_level':50}
        # self.save_msg(log_msg)
        self.log_update.emit(log_msg)


    @classmethod
    def log_debug(cls, msg):
        print('[DEBUG] {}'.format(msg))
        if cls.instance is not None:
            cls.instance._log_debug(msg)


    @classmethod
    def log_trace(cls, msg):
        print('[TRACE] {}'.format(msg))
        if cls.instance is not None:
            cls.instance._log_trace(msg)


    @classmethod
    def log_info(cls, msg):
        print('[INFO] {}'.format(msg))
        if cls.instance is not None:
            cls.instance._log_info(msg)


    @classmethod
    def log_warning(cls, msg):
        print('[WARNING] {}'.format(msg))
        if cls.instance is not None:
            cls.instance._log_warning(msg)

    @classmethod
    def log_error(cls, msg):
        print('[ERROR] {}'.format(msg))
        if cls.instance is not None:
            cls.instance._log_error(msg)


    @classmethod
    def create_instance(cls, log_file_path=None, log_widget=None):
        cls.instance = cls(log_file_path, log_widget)
        return cls.instance
    
    @classmethod
    def log_copy(cls, copy_log_path):
        shutil.copy(cls.instance.file_name, copy_log_path)