import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
import vtk
import random
from lib.common import vtk_utils
from shp_common import *


def Draw2DLine(mapInfo):
    ret = None
    try:
        # 라인 색으로 사용할 것, 점, 라인
        colors = vtk.vtkUnsignedCharArray()
        colors.SetNumberOfComponents(3)
        pts = vtk.vtkPoints()
        lines = vtk.vtkCellArray()

        nLen = 0
        for strFile in mapInfo:
            color = [random.randrange(0, 255) for _ in range(3)]
            print("file:%s / color: %s" % (strFile, color))
            shapeRecords = mapInfo[strFile].shapeRecords()

            #if 'C1' not in strFile and 'C1' not in strFile :
            #    continue

            for shapeRecord in shapeRecords:
                flag = True

                for _dot in zip(shapeRecord.shape.points, shapeRecord.shape.z):
                    dot = (_dot[0][0], _dot[0][1], _dot[1])
                    pts.InsertNextPoint(dot)
                    line = vtk.vtkLine()
                    if flag:
                        flag = False
                        nLen = nLen + 1
                        continue
                    line.GetPointIds().SetId(0, nLen - 1)
                    line.GetPointIds().SetId(1, nLen)
                    lines.InsertNextCell(line)
                    colors.InsertNextTypedTuple(color)
                    nLen = nLen + 1

        linesPolyData = vtk.vtkPolyData()
        linesPolyData.SetPoints(pts)
        linesPolyData.SetLines(lines)
        linesPolyData.GetCellData().SetScalars(colors)
        ret = linesPolyData

        vtk_utils.show_poly_data(linesPolyData)
    except BaseException as e:
        print(e)
    return ret


if __name__ == '__main__':
    import os
    strDir = '../../rsc/map_data/shp_01_Seoul_AutonomousDrivingTestbed/HDMap_UTM52N'

    # Change StrDir to Absolute Path
    current_path = os.path.dirname(os.path.realpath(__file__))
    strDir = os.path.normcase(strDir)
    strDir = os.path.join(current_path, strDir)
    strDir = os.path.normpath(strDir)

    # Get Map Information
    mapInfo = read_shp_files(strDir)

    # Do Tasks
    Draw2DLine(mapInfo)