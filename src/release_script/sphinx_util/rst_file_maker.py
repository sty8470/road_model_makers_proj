import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../../'))) 

import shutil


class RstFileMaker:
    default_module = os.path.join(current_path, 'default_module.rst')
    default_modules = os.path.join(current_path, 'default_modules.rst')

    rst_dst = ''

    @classmethod
    def create_all(cls, rst_dst, src_folder_list):
        cls.rst_dst = rst_dst

        sub_folder_list = []

        for src_folder in src_folder_list:
            result = cls.create_module_files_for_this_path(src_folder, cls.rst_dst)
            if result:
                sub_folder_list.append(src_folder)
            print('[INFO] {}: {}'.format(src_folder, result))
        

        if len(src_folder_list) > 0: # Successful 
            print('---------- Copy below to index.rst file ----------')
            for sub_folder in sub_folder_list:
                print('   {}/modules'.format(os.path.basename(sub_folder)))


    @classmethod
    def create_module_files_for_this_path(cls, input_path, dst):
        file_list = os.listdir(input_path)

        # 아무런 파일이 없으면 False를 반환한다
        if len(file_list) == 0:
            return False

        # 해당 경로에 폴더를 생성한다
        folder_name = os.path.basename(input_path)
        folder_path = os.path.join(dst, folder_name)
        if not os.path.exists(folder_path):
            os.mkdir(folder_path)

        # 기본값
        module_result = False # 현재 폴더 내부에 유효한 py 파일이 있으면 True가 됨
        sub_folder_result = False # 하위 폴더에 (깊이 무관) 유요한 py 파일이 있으면 True가 됨

        #
        module_list = [] # python 파일 이름이 모이는 리스트
        sub_folder_list = [] # 폴더 이름이 모이는 리스트
        for each_file in file_list:     
            each_file_full_path = os.path.join(input_path, each_file)

            # ignore 대상을 걸러낸다
            if each_file in ['__pycache__']:
                continue
                        

            if os.path.isdir(each_file_full_path): # isdir 을 체크하려면, 반드시 full path로 만들어 체크해야만 한다!
                # 폴더이면, 하위 경로에 대해 동일한 작업을 recursive하게 수행한다
                result_for_this_sub_folder = cls.create_module_files_for_this_path(
                    input_path=each_file_full_path, dst=folder_path)
                
                if result_for_this_sub_folder: # 하위 폴더에 하나라도 파일이 있으면,
                    sub_folder_list.append(each_file)

            else:
                # 파일이면, 모듈이름으로 저장한다
                filename, file_extension = os.path.splitext(each_file)
                if file_extension == '.py' and\
                    (filename != '__init__') and\
                    ('test_' not in filename) and\
                    ('_test' not in filename):
                    module_list.append(filename)

        # 유효한 sub folder가 하나라도 존재하면,
        if len(sub_folder_list) > 0:
            sub_folder_result = True

        # 유효한 python module이 하나라도 존재하면,
        if len(module_list) > 0:
            module_result = True
            

        # 각각의 모듈 파일 생성
        for module in module_list:
            cls.create_new_module_file(module, dst=folder_path)
        
        # module 리스트에는 sub folder를 한다
        for sub_folder in sub_folder_list:
            module_list.append(sub_folder + '/modules')

        # modules 파일 생성
        if len(module_list) > 0:
            cls.create_new_modules_file(folder_name, module_list, dst=folder_path)

        return sub_folder_result or module_result


    @classmethod
    def create_new_module_file(cls, module_name, dst=None):
        with open(cls.default_module) as f:
            content = f.read()

        new_content = content.replace('[module_name]', module_name)
        
        if dst is not None:
            new_file = os.path.join(dst, module_name+'.rst')
        else:
            new_file = module_name+'.rst'
        
        with open(new_file, 'w') as f:
            f.write(new_content)    


    @classmethod
    def create_new_modules_file(cls, directory_name, modules_list, dst=None):
        with open(cls.default_modules) as f:
            content = f.read()

        new_content = content.replace('[directory_name]', directory_name)
        for module_name in modules_list:
            new_content += '   {}\n'.format(module_name)

        if dst is not None:
            new_file = os.path.join(dst, 'modules.rst')
        else:
            new_file = 'modules.rst'

        with open(new_file, 'w') as f:
            f.write(new_content) 



