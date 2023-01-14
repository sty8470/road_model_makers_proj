import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))

import shp_common
import shapefile


input_path = '../../rsc/map_data/shp_31_Code42_Sample/toGwacheonSample'

# Change StrDir to Absolute Path
current_path = os.path.dirname(os.path.realpath(__file__))   

# inputPath = os.path.normcase(inputPath)
input_path = os.path.join(current_path, input_path)
input_path = os.path.normpath(input_path)  

map_data = shp_common.read_shp_files(input_path)

""" 변경된 국토지리정보원 데이터 포맷
A1_NODE
A2_LINK
A2_LINK_PATH
B1_SAFETYSIGN
B2_SURFACELINKMARK
C1_TRAFFICLIGHT
C6_POSTPOINT
bbox
"""

sf = map_data['A2_LINK']

shapes = sf.shapes()
records  = sf.records()
fields = sf.fields
shapes[0].shapeType

A2_LINK_TypeName = shp_common.InspectData_GetTypeName(map_data['A2_LINK'])
A2_LINKPATH_TypeName = shp_common.InspectData_GetTypeName(map_data['A2_LINK_PATH'])

print('ENDED')

""" def read_shp_files(strDir): 다시 수정하기 """
# map_info = {}
# file_list = os.listdir(input_path)
# for each_file in file_list:
#     file_fullpath = os.path.join(input_path, each_file)
    
#     # TOOD(sglee)
#     # 기존 구현에 보면 os.path.isdir... 부분이 있는데 그 부분은 다 가져오진 않았음
#     # subdirectory가 있을때 처리하기 위함일듯
#     if os.path.isdir(os.path.join(input_path, each_file)):
#         continue

#     # 확장자 제거
#     each_file = each_file[:-4]

#     import platform
#     # 맥 체크용, 맥에서는 ansi안됨
#     if platform.system() =='Darwin':
#         mapInfo[each_file] = shapefile.Reader(os.path.join(input_path, each_file))
#     else:
#         mapInfo[each_file] = shapefile.Reader(os.path.join(input_path, each_file), encoding='ansi')
#         try:
#             # 파일마다 utf-8이랑 ansi가 섞여있어서 둘중 에러안나는걸로 로드하도록
#             mapInfo[each_file].shapeRecords()
#         except:
#             mapInfo[each_file] = shapefile.Reader(os.path.join(input_path, each_file))




