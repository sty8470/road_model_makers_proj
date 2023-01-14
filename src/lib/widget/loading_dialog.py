from PyQt5 import QtCore
from PyQt5.QtWidgets import QProgressDialog, QProgressBar, QWidget
from PyQt5.QtCore import Qt
import platform

class LoadingDialog(QProgressDialog):
    def __init__(self, parent, label_text):
        super().__init__()
        self.initUI(parent, label_text)
    
    def initUI(self, parent, label_text=''):
        self.parent_window = parent

        progressbar = QProgressBar()
        progressbar.setTextVisible(False)        
        
        if platform.system() == "Windows":
            #self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
            self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        else:
            self.setWindowFlags(Qt.SplashScreen)

        self.setModal(True)
        self.setBar(progressbar)
        self.setCancelButton(None)
        self.setLabelText(label_text)
        self.setRange(0,0)

        self.bg_widget = QWidget(self.parent_window)
        
        if platform.system() == "Windows":
            self.bg_widget.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        else:
            self.bg_widget.setWindowFlags(Qt.SplashScreen)
        self.bg_widget.setStyleSheet('background-color: rgba(128,128,128,190)')
        if not platform.system() == "Windows":
            self.bg_widget.setWindowOpacity(0.7)

    def keyPressEvent(self, event):
        # if not event.key() == Qt.Key_Escape:
        #     super(LoginDialog, self).keyPressEvent(event)
        return

    def closeEvent(self, event):
        self.bg_widget.close()

    def show_loading(self):
        if platform.system() == "Windows":
            self.bg_widget.setGeometry(0, 0, self.parent_window.geometry().width(), self.parent_window.geometry().height())
        else:
            self.bg_widget.setGeometry(self.parent_window.geometry().x(), self.parent_window.geometry().y(), self.parent_window.geometry().width(), self.parent_window.geometry().height())
        self.bg_widget.show()
        self.bg_widget.adjustSize()

        self.show()
