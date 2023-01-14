import os
import sys
import re

current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../'))) 
sys.path.append(os.path.normpath(os.path.join(current_path, '../../'))) 
import test_file_upload.file_upload_download_manager as file_manager
import test_file_upload.test_mgeo as mgeo_test_manager


def file_upload(kind, mgeo_name = None, is_release = False):
    file_path = ''
    s3_bucket = ''
    bucket_path = ''
    
    file_dict=[]

    if kind == 'SIM':
        file_dir = os.path.join(current_path, '../../z_release')
        file_dir = os.path.normpath(file_dir)
        file_list = os.listdir(file_dir)
        s3_bucket = 'develop-morai-s3-bucket'
        
        for file_name in file_list:
            if file_name.__contains__('viewer') and file_name.__contains__('.zip'):
                written_time = os.path.getctime('{}/{}'.format(file_dir, file_name))
                file_dict.append((file_name, written_time))

        sotred_file_list = sorted(file_dict, key = lambda x:x[1], reverse= True)
        file_name = sotred_file_list[0][0]
        file_path = os.path.join(file_dir, file_name)
        bucket_path_debug = 'mgeo_mscenario_editor/mgeo_viewer/Debug/{}'.format(file_name)
        bucket_path_release = 'mgeo_mscenario_editor/mgeo_viewer/Release/{}'.format(file_name)
        file_manager.upload_file(file_path, s3_bucket, bucket_path_debug, True)
        file_manager.upload_file(file_path, s3_bucket, bucket_path_release, True)
        
    elif kind == 'INTERNAL':
        file_dir = os.path.join(current_path, '../../z_release')
        file_dir = os.path.normpath(file_dir)
        file_list = os.listdir(file_dir)
        s3_bucket = 'morai-core'
        for file_name in file_list:
            if file_name.__contains__('editor') and file_name.__contains__('.zip'):
                written_time = os.path.getctime('{}/{}'.format(file_dir, file_name))
                file_dict.append((file_name, written_time))

        sotred_file_list = sorted(file_dict, key = lambda x:x[1], reverse= True)
        file_name = sotred_file_list[0][0]
        file_path = os.path.join(file_dir, file_name)
        bucket_path = 'map_editor_internal_use/{}'.format(file_name)
        file_manager.upload_file(file_path, s3_bucket, bucket_path, True)
    
    elif kind == 'MGEO':
        file_dir = os.path.join(current_path, '../../data/temp/' + mgeo_name)
        file_dir = os.path.normpath(file_dir)
        mgeo_test_manager.run_test_one_map(file_dir, is_release)

        pass

    elif kind == 'SCENARIO':
        file_dir = os.path.join(current_path, '../../z_release')
        file_dir = os.path.normpath(file_dir)
        file_list = os.listdir(file_dir)
        s3_bucket = 'morai-core'
        for file_name in file_list:
            if file_name.lower().__contains__('scenario') and file_name.__contains__('.zip'):
                written_time = os.path.getctime('{}/{}'.format(file_dir, file_name))
                file_dict.append((file_name, written_time))

        sotred_file_list = sorted(file_dict, key = lambda x:x[1], reverse= True)
        file_name = sotred_file_list[0][0]
        file_path = os.path.join(file_dir, file_name)
        bucket_path = 'map_editor_internal_use/{}'.format(file_name)
        file_manager.upload_file(file_path, s3_bucket, bucket_path, True)



if __name__ == u'__main__':
    # print(sys.argv[1])
    if sys.argv.__len__() > 2 :
        mgeo_name = sys.argv[2]
        is_release = sys.argv[3]
        file_kind = sys.argv[1]
        result = file_upload(file_kind, mgeo_name = mgeo_name, is_release = is_release)
    elif sys.argv.__len__() > 1 :
        file_kind = sys.argv[1]
        result = file_upload(file_kind)
    

    #test
    # file_upload('MGEO', mgeo_name = 'R_KR_PG_KATRI', is_release = 'False')