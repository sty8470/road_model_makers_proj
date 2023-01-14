import os 
import glob
import sys
import copy
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))

import json

# MGeo 데이터 배포 전 차선 변경 링크를 삭제하기 위한 스크립트
# root_folder_path : 배포할 MGeo 데이터 세트 ROOT 폴더 경로
def delete_change_link_for_release(root_folder_path):
    link_files = glob.glob(root_folder_path + "/**/link_set.json", recursive = True)

    for link_file in link_files:
        with open(link_file, 'r') as f:
            link_set = json.load(f)       
            
            link_set_copy = copy.deepcopy(link_set)
            for link in link_set_copy:
                if link["lazy_init"] == True:
                    link_set.remove(link)

        with open(link_file, 'w') as f:
            json.dump(link_set, f, indent=2)

    return
    
if __name__ == '__main__':
    args = sys.argv[1:]
    
    # delete_change_link_for_release('D:/test/ventura')

    if len(args) != 1:
        print('please enter 1 argument(mgeo root folder path).')
    else:
        delete_change_link_for_release(args[0])