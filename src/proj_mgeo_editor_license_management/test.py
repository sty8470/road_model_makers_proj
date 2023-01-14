# 외부 쓰레드 에서 QT UI 접근하는 방법
import sys

from typing import Counter
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

class MyWindow(QDialog):    
    def __init__(self, parent=None):
        super().__init__(parent)

        # setting ui
        self.text_edit = QTextEdit(self)
        self.text_edit.setEnabled(True)
        self.text_edit.setVisible(False)
        box_layout = QVBoxLayout()
        box_layout.addWidget(self.text_edit)        
        self.setLayout(box_layout)

        # start thread
        self.myThread = Worker(parent=self)
        #self.myThread.count = 0
        self.myThread.count_changed.connect(self.update_count)  # custom signal from worker thread to main thread        
        self.myThread.start()
     
    #@pyqtSlot(int)
    def update_count(self, count):
        self.text_edit.append(str(count))  

class Worker(QThread):
    count_changed = pyqtSignal(int)
    def __init__(self, parent=None):
        super().__init__()
        self.main = parent
        self.working = True
        self.count = 0

    def run(self):
        while self.working:            
            self.count_changed.emit(self.count)
            self.sleep(1)
            self.count += 1

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MyWindow()    
    window.show()
    
    app.exec_()
