import vtk
import os
from lib.common import load_csv, display, file_io, vtk_utils


def LoadFromCsv(filename):
    csv = load_csv.read_csv_file_with_column_name(filename, skip_header=7)

    return csv


def DrawLine():
    try:
        strDir = '../rsc/map_data/csv_kcity_190515_PM0450_relpos_commadel'
        lstFiles = os.listdir(strDir)

        colors = vtk.vtkUnsignedCharArray()
        colors.SetNumberOfComponents(3)

        pts = vtk.vtkPoints()
        lines = vtk.vtkCellArray()
        len = 0
        for strFile in lstFiles:
            if not strFile.lower().endswith('.csv'):
                continue

            print(strFile)
            arrDots = LoadFromCsv(os.path.join(strDir, strFile))
            flag = True
            for dot in arrDots:
                pts.InsertNextPoint(dot)
                line = vtk.vtkLine()
                if flag:
                    flag = False
                    len = len + 1
                    continue
                line.GetPointIds().SetId(0, len - 1)
                line.GetPointIds().SetId(1, len)
                lines.InsertNextCell(line)
                len = len + 1

        linesPolyData = vtk.vtkPolyData()
        linesPolyData.SetPoints(pts)
        linesPolyData.SetLines(lines)

        return linesPolyData
    except BaseException as e:
        print(e)
    return None

if __name__ == '__main__':
    road_obj = DrawLine()
    if road_obj is not None:
        file_io.write_stl_and_obj(road_obj, 'test_road')
        display.show_vtkPolyData(road_obj)
