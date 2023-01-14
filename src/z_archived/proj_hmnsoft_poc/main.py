import lib.common.path_utils as path_utils
import from_shp_draw_lane as laneside
import from_shp_draw_road as roadnode
import from_shp_draw_edge as roadedge

if __name__ == '__main__':
    import os, datetime

    datetime_str = path_utils.get_datetime_str(datetime.datetime.now())

    inputDir = '../rsc/map_data/shp_HDMap_Uiwang_190213_WGS'
    outputDir = '../output/RoadModel_{}'.format(datetime_str)
    
    # Change inputFile to Absolute Path
    current_path = os.path.dirname(os.path.realpath(__file__))
    # inputFile = os.path.normcase(inputFile)
    inputDir = os.path.join(current_path, inputDir)
    inputDir = os.path.normpath(inputDir)

    # Change output to Absolute Path
    # outputFile = os.path.normcase(outputFile)
    outputDir = os.path.join(current_path, outputDir)
    outputDir = os.path.normpath(outputDir)

    # Check if the output path exists & Make
    if not os.path.isdir(outputDir):
        os.makedirs(outputDir)

    print('[INFO] input  path: {}'.format(inputDir))
    print('[INFO] output path: {}'.format(outputDir))

    # 출력 파일 옵션명 정하기
    # from_shp_common에 있는 GetLocation 함수에서
    # Z를 사용하지 않음을 기본 옵션으로 쓸 때는 NoZ를 붙여서 구분
    # TODO(sglee) 나중에 이 부분도 자동으로 되도록
    optionInfo = 'NoZ_' + datetime_str
    # optionInfo = datetime_str

    mapInfo = laneside.read_shp_files(inputDir)

    # STEP01-02 : BaseRoad From Lane Side & Lanes From LaneSide
    print('[INFO] Making a RoadBase model (From LaneSide) & Lane models...')
    laneside.DrawRoadBase(mapInfo, outputDir, optionText=optionInfo)
    laneside.DrawLane(mapInfo, outputDir, optionText=optionInfo)
    print('[INFO] Finished')

    # STEP03 : BaseRoad From RoadNode
    print('[INFO] Making a RoadBase model (From RoadNode) ...')
    roadnode.DrawRoadBase(mapInfo, outputDir, optionText=optionInfo)
    print('[INFO] Finished')

    # STEP04 : Draw RoadEdges
    print('[INFO] Making RoadEdge models...')
    roadedge.DrawEdge(mapInfo, outputDir, optionText=optionInfo)
    print('[INFO] Finished')

    print('[INFO] Road Model Build Finished')