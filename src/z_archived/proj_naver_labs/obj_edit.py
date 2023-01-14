#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../'))) # mgeo가 있는 경로를 추가한다.

import vtk
import numpy as np

from lib.common import display, file_io, vtk_utils

def get_obj_file_names(input_path):
    file_list = os.listdir(input_path)
    file_names = list()

    for each_file in file_list:
        file_full_path = os.path.join(input_path, each_file)
        
        # 디렉토리는 Skip
        if os.path.isdir(file_full_path):
            continue
        
        # geojson인지 체크
        filename, file_extension = os.path.splitext(each_file)
        if file_extension == '.obj':
            file_names.append(filename)

    return file_names


def main(display=False):
    input_dir = os.path.join(current_path, '../../rsc/naver_labs_data/03_Buildings')
    input_dir = os.path.normpath(input_dir)
    
    output_dir = os.path.join(input_dir, 'new_origin/')

    print('[INFO] input_dir : ', input_dir)
    print('[INFO] output_dir: ', output_dir)

    file_name_list = get_obj_file_names(input_dir)
    for file_name in file_name_list:
        input_file = os.path.join(input_dir, file_name+'.obj')
        output_file = os.path.join(output_dir, file_name)

        # TODO: 여기서 OBJImporter 같은 걸 이용하면
        # MTL, Texture를 쓸 수 있어보이는데
        # 뭔가 안될까?
        # OBJImporter, OBJExporter에는
        # MTL, Texture 같은걸 설정할 수 있어보임

        # OBJReader를 이용, obj 파일에서 vtkPolyData 인스턴스를 받아온다
        # >> 3D 모델 그 자체를 나타내는 인스턴스
        reader = vtk.vtkOBJReader()
        reader.SetFileName(input_file)
        reader.Update()
        poly_data = reader.GetOutput()
        
        # vtkPoints 인스턴스를 받아온다 
        points = poly_data.GetPoints()

        # 대체할 새로운 vtkPoint 인스턴스
        new_points = vtk.vtkPoints() 
        
        # 현재 모든 좌표를 받아오고,
        # 여기서 원점을 뺀 좌표를, 별도의 vtkPoint Object로 넣어준다
        origin = np.array([313008.55819801, 4161698.62836801, 35.66435583])
        
        num_points = points.GetNumberOfPoints() 
        for i in range(0, num_points):
            p = points.GetPoint(i)
            # print('i = {}, p ='.format(i), p)

            new_p = np.array(p) - origin
            new_p = new_p.tolist()
            new_points.InsertPoint(i, new_p)

        poly_data.SetPoints(new_points)

        if display:
            # 이제는 이 새로운 poly_data를 출력해본다
            display.show_vtkPolyData(poly_data)

        file_io.write_obj(poly_data, output_file)

    print('END')


if __name__ == '__main__': 
    main()