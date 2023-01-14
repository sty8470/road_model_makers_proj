import vtk
import os
import shapefile
import random
import numpy as np
import math
from lib.common import file_io
from lib.common import vtk_utils
from shp_common import *


def DrawPlot(mapInfo):
    try:
        import matplotlib.pyplot as plt
        plt.figure()

        for strFile in mapInfo:
            if 'ROAD_EDGE' not in strFile and 'ROAD_NODE' not in strFile:
                continue
            shapeRecords = mapInfo[strFile].shapeRecords()
            color = [random.randrange(0, 255) for _ in range(3)]

            for shapeRecord in shapeRecords:
                xyz = [GetLocation(i[0], i[1], 0) for i in shapeRecord.shape.points[:]]
                x = [i[0] for i in xyz[:]]
                y = [i[1] for i in xyz[:]]
                plt.plot(x, y, color=[color[0] / 255, color[1] / 255, color[2] / 255])

        plt.show()
    except BaseException as e:
        print('---------- [ERROR] ----------')
        print(e)


if __name__ == '__main__':
    import os
    strDir = '../rsc/map_data/shp_HDMap_Uiwang_190213_WGS'

    # Change StrDir to Absolute Path
    current_path = os.path.dirname(os.path.realpath(__file__))   
    strDir = os.path.normcase(strDir)
    strDir = os.path.join(current_path, strDir)
    strDir = os.path.normpath(strDir)    

    # Get Map Information
    mapInfo = read_shp_files(strDir)

    # Do Tasks
    DrawPlot(mapInfo)
