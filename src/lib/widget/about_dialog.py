import webbrowser
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from stdlib_list import stdlib_list

import os
import json
import re
import webbrowser

from tkinter import *
from PIL import ImageTk, Image

current_path = os.path.dirname(os.path.realpath(__file__))
lib_path = os.path.normpath(os.path.join(current_path, '../'))
src_path = os.path.normpath(os.path.join(lib_path, '../'))
root_path = os.path.normpath(os.path.join(src_path, '../'))
opengl_path = os.path.normpath(os.path.join(src_path, 'proj_mgeo_editor_morai_opengl'))
gui_path = os.path.normpath(os.path.join(opengl_path, 'GUI'))
users_path = os.path.normpath(os.path.join(gui_path, 'Users'))
user_internal_path = os.path.normpath(os.path.join(users_path, 'User_internal.json'))
data_path = os.path.normpath(os.path.join(root_path, 'data'))
img_path = os.path.normpath(os.path.join(data_path, 'img'))
morai_logo_path = os.path.normpath(os.path.join(img_path, 'morai_logo.png'))
mgeo_icon_path = os.path.normpath(os.path.join(opengl_path,'map.ico'))

with open(user_internal_path) as f:
    morai_map_editor_ver = json.load(f)
    f.close()
class HSeperationLine(QFrame):
  '''
  가로 구분선
  '''
  def __init__(self):
    super().__init__()
    self.setMinimumWidth(1)
    self.setFixedHeight(3)
    self.setFrameShape(QFrame.HLine)
    self.setFrameShadow(QFrame.Sunken)

class LicenseOverhaul():
    '''
    src directory 밑에 있는 모든 파이썬 파일들을 선회한다. (O)
    모든 파일 이름들을 리스트에 저장한다. (O)
    import로 된 모든 라인을 가지고 온다. (very likely, 외부 리소스이다.) (O)
    from으로 된 모든 라인들 가지고 온다.
        첫 번째 키워드가 파일 안에 있지 않다면, 외부 리소스이다.
    '''
    def __init__(self):
       
       self.all_dirs_and_files = set()
       self.import_libraries = set()
       self.from_libraries = set()
       self.external_libraries = set()
    
    def get_python_standard_libraries(self):
        '''
        파이썬 3.7.3 버젼의 모든 디폴트로 저장된, standard library들을 
        '''
        std_libraries = stdlib_list('3.7')
        return std_libraries
          
    def get_dirs_and_files(self):
        '''
        src_path 밑에 있는 모든 디렉토리와 파이선 파일들을 추출한다.
        '''
       # 모든 디렉토리들을 추출한다
        for (root, dirs, files) in os.walk(src_path):
           for dir in dirs:
               self.all_dirs_and_files.add(dir.lower())
               
        # 모든 파이썬 파일들을 추출한다.
        for (root, dirs, files) in os.walk(src_path):
           for file in files:
               if '.' in file and file.split('.')[1] == 'py':
                   self.all_dirs_and_files.add((file.split('.')[0]).lower()) 
        return self.all_dirs_and_files
   
    def get_import_libraries(self):
        '''
        import로 시작하는 모든 외부 라이브러리들을 추출한다. Flag는 0으로 설정한다.
        '''
        for (root, dirs, files) in os.walk(src_path):
           for file in files:
               if '.' in file and file.split('.')[1] == 'py':
                   file_path = os.path.join(root, file)
                   with open(file_path, 'r', encoding='utf-8') as python_file:
                       for line in python_file:
                           line = line.strip()
                           if len(line.split()) > 1 and line.split()[0] == 'import':
                               lib_name = (line.split()[1]).lower()
                               if '.' in lib_name:
                                   lib_name = (lib_name.split('.')[0]).lower()
                               self.import_libraries.add(lib_name)
        return self.import_libraries
    
    def get_from_libraries(self):
        '''
        from으로 시작하는 모든 외부 라이브러리들을 추출한다. Flag는 1로 설정한다.
        '''
        for (root, dirs, files) in os.walk(src_path):
            for file in files:
                    if '.' in file and file.split('.')[1] == 'py':
                        file_path = os.path.join(root, file)
                        with open(file_path, 'r', encoding='utf-8') as python_file:
                            for line in python_file:
                                line = line.strip()
                                if len(line.split()) > 1 and line.split()[0] == 'from':
                                    lib_name = (line.split()[1]).lower()
                                    if '.' in lib_name:
                                        lib_name = (lib_name.split('.')[0]).lower()
                                    self.from_libraries.add(lib_name)
        return self.from_libraries
    
    def filter_import_and_from_libraries(self):
        '''
        license 인스턴스의 get_import_libraries와 get_from_libraries들 중에서 다음과 같은 조건을 만족한다면, 제외시킵니다.
        1. self.get_dirs_and_files (b/c: 폴더이름이나 파이썬 파일의 고유명사라는 뜻이므로)
        2. 행여나, 빈 string 이 있다면 (b/c: 필터중에 걸러지지 못한 불순물들)
        3. '_' 언더스코어가 있다면 (b/c: 상대적인 파일 dependency들이므로..)
        최종적으로 나머지 파일들은,  final_libraries 모든 외부 라이브러리들을 담아주고 return 합니다.
        '''
        filtered_libraries = set()
        
        for lib in self.get_import_libraries():
            if (lib not in self.get_dirs_and_files()) and len(lib) > 0 and '_' not in lib:
                self.external_libraries.add(lib)
                
        for lib in self.get_from_libraries():
            if (lib not in self.get_dirs_and_files()) and len(lib) > 0 and '_' not in lib:
                self.external_libraries.add(lib)
                
        for sorted_lib in sorted(self.external_libraries):
            cleaned_lib = re.sub('[^A-Za-z0-9]','',sorted_lib)
            filtered_libraries.add(cleaned_lib)
        return sorted(filtered_libraries)
    
    def check_non_python_libraries(self):
        '''
        filter_import_and_from_libraries들 중에서 python standard libraries들이 있다면('get_python_standard_libraries' 사용), 
        그것들은 제외시키고, 포함이 안되어있는 나머지 라이브러리들을 그대로 추출한다.
        '''
        non_standard_libraries = set()
        for lib in self.filter_import_and_from_libraries():
            if lib not in self.get_python_standard_libraries():
                non_standard_libraries.add(lib)
        return non_standard_libraries
    
    def check_with_pip_freeze_list(self):
        '''
        기존의 python 내부에 설치되어있는 모든 라이브러리들과 버젼을 pip freeze command을 실행하여서 requirements.txt에 추출한다.
        추출 후에 ㅣ
        '''
        cmd = 'pip freeze > requirements.txt'
        os.system(cmd)
        
        default_lib_dict = {}
        about_page_licenses = set()
        double_check_fallbacks = set()
        
        with open('requirements.txt') as fp:
            for line in fp:
                line = line.strip()
                if '==' in line:
                    default_lib_dict[line.split('==')[0]] = line.split('==')[1]
        
        for lib in self.check_non_python_libraries():
            if lib in default_lib_dict.keys():
                about_page_licenses.add(lib)
            else:
                double_check_fallbacks.add(lib)
        
        return sorted(about_page_licenses), sorted(double_check_fallbacks)
class AboutDialog():
    """    
    About 정보를 보여주기 위한 다이얼로그로 아래처럼 페이지를 구성한다.

    [고정] MORAI Map Editor
    [고정] Copyright MORAI Inc. 2021
    [변겅] Version 0.4 (편집됨) - Fetch it from 'User.json' build PC (double-check with Hyein)
    
    ------------------(구분선)
    
    [Open Source Libraries]
    
    library_name, license_type 
    elevate, MIT
    multipledispatch, Apache 2
    lxml, BSD-3 ...

    """

    def __init__(self, window_title, page_title, contents):
        self.initUI(window_title, page_title, contents)

    def initUI(self, window_title, page_title, contents):
        # window 크기와 제목 설정
        # self.setFixedSize(400,400)
        # self.setWindowTitle(window_title)
        
        main_panel = Tk()
        main_panel.iconbitmap(mgeo_icon_path)
        main_panel.title('MapEditor (v.0.2)')
        main_panel.configure(bg='white')
        # Define the geometry of the window
        main_panel.geometry("400x400")
        main_panel.resizable(width=False, height=False)
        # main_panel.attributes('-toolwindow', True)

        license_frame = Frame(main_panel, width=10, height=10)
        license_frame.configure(bg='white')
        license_frame.pack()
        license_frame.place(anchor='n', relx=0.5, rely=0.01)

        # Create an object of tkinter ImageTk
        logo_img = Image.open(morai_logo_path)
        resized_logo_image= logo_img.resize((120,30), Image.ANTIALIAS)
        new_logo_image= ImageTk.PhotoImage(resized_logo_image, master=license_frame)
        # Create a Label Widget to display the text or Image
        label = Label(license_frame, image = new_logo_image, borderwidth=0)
        # label.image = new_logo_image
        label.pack()
        
        copyright_label = Label(license_frame, text='Copyright Morai Inc. 2022 \n All rights Reserved \n\n')
        copyright_label.configure(bg='white')
        copyright_label.place(anchor='n', relx=0.5, rely=0.3)
        copyright_label.pack()
        
        mgeo_label = Label(license_frame, text = 'MGeo MapEditor supports map data format conversion and \n modification for all geospatial and road network data. \n')
        mgeo_label.configure(bg='white')
        mgeo_label.pack()
        
        # txt = Text(license_frame, width = 50, height=100, borderwidth=0)
        # txt.pack()
        # txt.insert('1.0', "글자를 입력하세요\n")
        # txt.insert('2.0', "글자를 입력하세요\n")
        # txt.insert('3.0', "글자를 입력하세요\n")
        # txt.insert(END, "글자를 입력하세요\n")
        
        about_dialog_config_path = os.path.normpath(os.path.join(gui_path, 'config_about_dialog_default.json'))
        with open(about_dialog_config_path) as f:
            license_lst = json.load(f)
            f.close()
        license_txt = Text(license_frame, width = 50, height=100, borderwidth=0)
        for lib_key in license_lst: 
            # license_label = Label(license_frame, text='{}  {}   {}'.format(lib_key, license_lst[lib_key]))
            # license_label.configure(bg='white')
            license_txt.pack()
            license_txt.insert(END,'{}\t\t\t{}{}'.format(lib_key, '©' ,license_lst[lib_key]))
            # license_txt.bind("<Button-1>", lambda e: callback("http://www.google.com"))
            license_txt.insert(END, '\n')
            license_txt.configure(font=("Times New Roman", 10))
            
        license_txt.config(state=DISABLED)
        main_panel.mainloop()
       
        

        # self.main_layout = QVBoxLayout(self)
        # Initialiaze tab screen
        # self.license_page = QTextEdit()
        # self.license_page.setReadOnly(True)
        # self.license_page.append('MORAI Map Editor')
        # self.license_page.append('Copyright MORAI Inc. 2021')
        # self.license_page.append('Version {}'.format(morai_map_editor_ver['program_name'].split()[1][2:5]))
        # self.morai = QLabel()
        # self.morai_logo = QPixmap(morai_logo_path)
        # self.morai.setPixmap(self.morai_logo)
        # self.resize(self.morai_logo.width(), self.morai_logo.height())
        # self.license_page.append('-----------------------------------------------')
        # self.license_page.append('>>> library licenses to be added are as follows: ')
        # self.license_page.append('')
        # self.license_page.append('library_name     library_licenses')
        
        # 아래 코드는 Build PC에서 최초 build시에 한번만 run하고 나온 about_page_lookup 결과값들을 출력 후에, 
        # 기존의 src\proj_mgeo_editor_morai_opengl\GUI 경로에 있는 config_about_dialog_default.json과 비교해서
        # 새로 추가된 library들의 license pair들을 추가해주시면 됩니다.
        
        # licenses = LicenseOverhaul()
        # about_page_licenses, double_check_fallbacks = licenses.check_with_pip_freeze_list()
        # self.license_page.append('There are {} libraries to be licensed according to the search'.format(len(about_page_licenses)))
        # self.license_page.append('')
        # for lib in about_page_licenses:
        #     print(lib)
        
        # about_dialog_config_path = os.path.normpath(os.path.join(gui_path, 'config_about_dialog_default.json'))
        # with open(about_dialog_config_path) as f:
        #     license_lst = json.load(f)
        #     f.close()
        # for lib_key in license_lst: 
        #     self.license_page.append('{}     {}'.format(lib_key, license_lst[lib_key]))
        # self.main_layout.addWidget(self.license_page)
        # self.main_layout.addWidget(self.morai_logo)
        # self.setLayout(self.main_layout)
    
    # def showDialog(self):
    #     return super().exec_()

    def accept(self):
        self.done(0)

    def close(self):
        self.done(0)
