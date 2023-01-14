import os
import sys

class Define:    
    server_url =  "http://ec2-54-180-34-141.ap-northeast-2.compute.amazonaws.com"
    # developer_url = "http://ec2-52-78-167-130.ap-northeast-2.compute.amazonaws.com"
    #service_url = "http://ec2-54-180-34-141.ap-northeast-2.compute.amazonaws.com"
    #local_url = "http://10.110.51.53"
    
    port = "8080"
    refresh_time = 3
    session_check_interval = 5
    
    # app path 
    current_path = os.path.dirname(os.path.realpath(__file__))    
    print("current : ",current_path)
    sys.path.append(current_path)
    joinPath = os.path.join(current_path, '../')
    normPath = os.path.normpath(joinPath)
    print("append : ", normPath)
    sys.path.append(normPath)

    if __debug__:
        setting_file_path = os.path.join(current_path, 'setting.json')        
    else:        
        setting_file_path = os.path.join(current_path, '../setting.json')             

    user_file_path = os.path.join(current_path, '../proj_mgeo_editor_morai_opengl/User.json')
    default_user_file = os.path.join(current_path, '../proj_mgeo_editor_morai_opengl/GUI/Users/User_MORAI.json')

    # ui file path
    ui_folder_path = current_path + "//uic//"
    #sign_in_window_path = os.path.join(ui_folder_path, 'sign_in.ui')
    #sign_up_window_path = os.path.join(ui_folder_path, 'sign_up.ui')
    #launcher_window_path = os.path.join(ui_folder_path, 'launcher.ui')
    #userinfo_window_path = os.path.join(ui_folder_path, 'userinfo.ui')
    #edituser_window_path = os.path.join(ui_folder_path, 'edit_userinfo.ui')

    # ico_path 
    map_icon = os.path.join(current_path, 'map.ico')
    warning_icon = os.path.join(current_path, 'warning.png')
    userinfo_icon = os.path.join(current_path, 'user.png')
    edit_user_icon = os.path.join(current_path, 'edit.png')
    logout_icon = os.path.join(current_path, 'logout.png')

    # authentication
    valid_key_dict = {'ff2b43e855f86c1bccbc46be410b619028a8bd609bbcc3d501f67f3276a74249': 0x00000001}