import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))

from shp_common import *
import shapefile

from shp_transform import shp_transform
trans_obj = shp_transform()

def ex1():
    w = shapefile.Writer(target='output/test01/test_out', shapeType=shapefile.POLYLINEZ)
    w.shapeType = 1

    # DBF에 어떤 필드가 있을 것인지를 미리 선언
    w.field('TEXT', 'C')
    w.field('SHORT_TEXT', 'C', size=5)
    w.field('LONG_TEXT', 'C', size=250)

    # SHP에 geometry를 하나 추가, DBF 데이터를 추가
    w.null()
    w.record('HELLO', 'World', 'World'*10)

    # 파일 닫기
    w.close()

def ex2():
    strDir = '../../rsc/map_data/shp_03_Sungnam_PangyoZeroCity/HDMap_UTM52N'
            
    # Change StrDir to Absolute Path
    current_path = os.path.dirname(os.path.realpath(__file__))   
    strDir = os.path.normcase(strDir)
    strDir = os.path.join(current_path, strDir)
    strDir = os.path.normpath(strDir)    

    print('strDir:', strDir)

    # Get Map Information
    mapInfo = read_shp_files(strDir)

    # ShapeRecords에 접근하는 방법. 
    sf = mapInfo['A3_LINK']

    # shp 파일, dbf 파일
    shapes = sf.shapes()
    records  = sf.records()
    fields = sf.fields
    
    one_shp_obj = shapes[0]
    one_dbf_obj = records[0]

    print('type(one_shp_obj): ', type(one_shp_obj))
    print('type(one_dbf_obj): ', type(one_dbf_obj))


    w = shapefile.Writer(target='output/test01/test_out',\
        shapeType=shapefile.POLYLINEZ)

    # DBF 필드 정의 
    w.fields.append(fields[1])
    w.fields.append(fields[2])
    w.fields.append(fields[3])

    # shp, dbf 데이터 복사
    w.shape(one_shp_obj)
    w.record(*one_dbf_obj[0:3])

    w.close()

    print('---------- [TEST ENDS] ---------')

def __create_a1_lane_a1_barrier(sf, output_path, output_name_suffix=''):
    global trans_obj

    # 기존의 shp 파일, dbf 파일
    shapes = sf.shapes()
    records  = sf.records()
    fields = sf.fields
    shapes[0].shapeType
    
    # 새로 작성할 shp 파일, dbf 파일을 write하는 객체 생성
    output_file_full_name = output_path + '/' + '03_LANE' + output_name_suffix
    w_lane = shapefile.Writer(target=output_file_full_name,\
        shapeType=shapes[0].shapeType)

    output_file_full_name = output_path + '/' + '04_BARRIER' + output_name_suffix
    w_barrier = shapefile.Writer(target=output_file_full_name,\
        shapeType=shapes[0].shapeType)

    dbf_field_names_lane = list()
    for idx in [1,2,3,4]:
        w_lane.fields.append(fields[idx])
        dbf_field_names_lane.append(fields[idx][0])

    dbf_field_names_barrier = list()
    for idx in [1,2]:
        w_barrier.fields.append(fields[idx])
        dbf_field_names_barrier.append(fields[idx][0])
    
    # fields[5]의 경우, NGII에서는 'BARRIER'라고 되어있다. 
    # 그런데 이걸 output에 저장할때에는 'BARRIERTYPE'으로 바꾸고 싶다.
    w_barrier.fields.append(['BARRIERTYPE', fields[5][1], fields[5][2], fields[5][3]])
    dbf_field_names_barrier.append('BARRIER')

    # [STEP #2] shp, dbf 데이터 복사 (object 하나씩 하나씩))
    for i in range(len(shapes)):
        
        # DBF 정보를 보고 어느쪽으로 추가할지 결정한다
        dbf_rec = records[i]

        # SHP 데이터를 tranform 해둔다
        shp_obj = trans_obj.transform(shapes[i])

        if dbf_rec['CODE'] == '1':
            # shp 데이터 복사
            w_lane.shape(shp_obj)
            
            # dbf 데이터 복사를 하기 위해
            # 유지해야할 dbf 데이터를 리스트로 만든다        
            dbf_to_put = list()
            for field_name in dbf_field_names_lane:
                dbf_to_put.append(dbf_rec[field_name])
            # dbf 데이터 복사
            w_lane.record(*dbf_to_put)

        elif dbf_rec['CODE'] == '2':

            # shp 데이터 복사
            w_barrier.shape(shp_obj)

            # dbf 데이터 복사를 하기 위해
            # 유지해야할 dbf 데이터를 리스트로 만든다        
            dbf_to_put = list()
            for field_name in dbf_field_names_barrier:
                dbf_to_put.append(dbf_rec[field_name])
            # dbf 데이터 복사
            w_barrier.record(*dbf_to_put)

        else:
            raise BaseException('Unexpected dbf record')


    w_lane.close()
    w_barrier.close()

def __create_cloned(sf, dbf_field_to_keep, output_path, output_name):
    global trans_obj

    # 기존의 shp 파일, dbf 파일
    shapes = sf.shapes()
    records  = sf.records()
    fields = sf.fields
    shapes[0].shapeType
    # 새로 작성할 shp 파일, dbf 파일을 write하는 객체 생성
    output_file_full_name = output_path + '/' + output_name
    w = shapefile.Writer(target=output_file_full_name,\
        shapeType=shapes[0].shapeType)

    dbf_field_names = list()
    for idx in dbf_field_to_keep:
        w.fields.append(fields[idx])
        dbf_field_names.append(fields[idx][0])

    # [STEP #2] shp, dbf 데이터 복사 (object 하나씩 하나씩))
    for i in range(len(shapes)):
        
        # shp 데이터 복사
        shp_obj = trans_obj.transform(shapes[i])
        w.shape(shp_obj)

        # dbf 데이터 복사를 하기 위해
        # 유지해야할 dbf 데이터를 리스트로 만든다
        dbf_rec = records[i]
        dbf_to_put = list()
        for field_name in dbf_field_names:
            dbf_to_put.append(dbf_rec[field_name])
        
        # dbf 데이터 복사
        w.record(*dbf_to_put)

    w.close()

def convert_to_vz_sample_format():
    area_code = u'서울 상암'

    if area_code == u'서울 상암':
        # 서울 상암 자율주행테스트베드 (LG유플러스상암사옥으로 검색)
        inputPath = '../../rsc/map_data/shp_01_Seoul_AutonomousDrivingTestbed/HDMap_UTM52N'
        outputPath = '../../output/shp_01_Seoul_AutonomousDrivingTestbed/release2'
        # origin_point = [313266.465, 4161467.203] # first node point
    
    elif area_code == u'판교 제로시티':
        # 판교 제로시티 
        inputPath = '../../rsc/map_data/shp_03_Sungnam_PangyoZeroCity/HDMap_UTM52N'
        outputPath = '../../output/shp_03_Sungnam_PangyoZeroCity/release'
        # origin_point = [331863.9619974309, 4142374.7420254853] # first node point

    elif area_code == u'경부고속도로':
        """ SEC 선택은 수동으로 주석 처리/해제를 통해 해야 함 """
        # 경부고속도로 (SEC 01)
        # inputPath = '../../rsc/map_data/shp_06_NatlExpress_No1_EN/SEC01_YangjaeIC-SeoulTG/HDMap_UTM52N'
        # outputPath = '../../output/shp_06_NatlExpress_No1_EN/SEC01/release'

        # 경부고속도로 (SEC 02A)
        # inputPath = '../../rsc/map_data/shp_06_NatlExpress_No1_EN/SEC02A_SeoulTG/HDMap_UTM52N'
        # outputPath = '../../output/shp_06_NatlExpress_No1_EN/SEC02/release'

        # 경부고속도로 (SEC 02B)
        inputPath = '../../rsc/map_data/shp_06_NatlExpress_No1_EN/SEC02B_SeoulTG-SingalJCT/HDMap_UTM52N'
        outputPath = '../../output/shp_06_NatlExpress_No1_EN/SEC02B/release'    

        # [NOTE1*] 경부고속도로와 같이 section이 나뉘어진 경우, 같은 점을 기준으로 transform을 수행해야한다.
        # 따라서, origin point를 따로 설정해준다
        # origin point 설정 방법은 shp_transform.transform 함수 내부에서 첫번째 점이 입력되어 init 하는 지점에 breakpoint를 찍어놓고
        # 디버그 모드로 실행을 한다. 그러면 첫번째 점이 입력될 때 중단되므로 값을 읽어낼 수 있다.
        # 현재는 shp 파일들을 읽은 다음, C1_NODE부터 검색하므로, C1_NODE의 첫번째 점의 값을 읽는 것이다.
        origin_point = [330852.004, 4142221.346]
        trans_obj.manual_init(origin_point)

    elif area_code == u'대구 수성알파시티':
        """ SEC 선택은 수동으로 주석 처리/해제를 통해 해야 함 """

        # inputPath = '../../rsc/map_data/shp_04_Daegu_SuseongAlphaCity/SEC01/HDMap_UTM52N'
        # outputPath = '../../output/shp_04_Daegu_SuseongAlphaCity/SEC01/release'

        inputPath = '../../rsc/map_data/shp_04_Daegu_SuseongAlphaCity/SEC02/HDMap_UTM52N'
        outputPath = '../../output/shp_04_Daegu_SuseongAlphaCity/SEC02/release'

        # section이 나뉘어진 경우, 같은 점을 기준으로 transform을 수행해야한다.
        # 따라서, origin point를 따로 설정해준다
        # origin point 설정 방법은 경부고속도로 코드 쪽의 주석을 참조 [NOTE1*]
        origin_point = [471421.963, 3965524.601]
        trans_obj.manual_init(origin_point)
    else:
        raise BaseException('[ERROR] Undefined area_code!!!')


    
    output_suffix = ''

    # Change StrDir to Absolute Path
    current_path = os.path.dirname(os.path.realpath(__file__))   
    # inputPath = os.path.normcase(inputPath)
    inputPath = os.path.join(current_path, inputPath)
    inputPath = os.path.normpath(inputPath)    


    # Change output to Absolute Path
    # outputPath = os.path.normcase(outputPath)
    outputPath = os.path.join(current_path, outputPath)
    outputPath = os.path.normpath(outputPath)

    # Check if the output path exists
    # outputPath = os.path.dirname(outputPath)
    if not os.path.isdir(outputPath):
        os.makedirs(outputPath)
    
    print('[INFO] input  path:', inputPath)
    print('[INFO] output path:', outputPath)

    # Get Map Information
    mapInfo = read_shp_files(inputPath)


    """ C1_NODE -> 01_NODE """
    shp_class = 'C1_NODE'
    output_class = '01_NODE'
    dbf_field_to_keep = [1,2]
    # 1 LINKID    NODEID
    # 2 NODETYPE  NODETYPECODE
    if shp_class in mapInfo:
        __create_cloned(
            sf=mapInfo[shp_class],
            dbf_field_to_keep=dbf_field_to_keep,
            output_path=outputPath,
            output_name=output_class+output_suffix)
        print('[INFO] {0} -> {1} : OK'.format(shp_class.ljust(25), output_class.ljust(30)))
    else:
        print('[INFO] {0} -> {1} : NOT EXIST'.format(shp_class.ljust(25), output_class.ljust(30)))   


    """ A3_LINK -> 02_LINK """
    shp_class = 'A3_LINK'
    output_class = '02_LINK'
    dbf_field_to_keep = [1,2,3,4,5,8]
    # 1 LINKID    VARCHAR
    # 2 FROMNODE  VARCHAR
    # 3 TONODE    VARCHAR
    # 4 LENGTH    NUM 16,2 
    # 5 ROADTYPE  ROADTYPECODE
    # 8 LANE      NUM 4   
    if shp_class in mapInfo:
        __create_cloned(
            sf=mapInfo[shp_class],
            dbf_field_to_keep=dbf_field_to_keep,
            output_path=outputPath,
            output_name=output_class+output_suffix)
        print('[INFO] {0} -> {1} : OK'.format(shp_class.ljust(25), output_class.ljust(30)))
    else:
        print('[INFO] {0} -> {1} : NOT EXIST'.format(shp_class.ljust(25), output_class.ljust(30)))


    """ A1 LANE -> 03_LANE, 04_BARRIER """
    shp_class = 'A1_LANE'
    output_class = '03_LANE, 04_BARRIER'
    dbf_field_to_keep = [1,2,3,4,5,7]
    # 1 R_LINKID    VARCHAR
    # 2 L_LINKID    VARCHAR
    # 3 LANETYPE    LANETYPECODE
    # 4 LANECODE    LANECODE
    # 5 BARRIER     BARRIERCODE
    # 7 CODE
    if shp_class in mapInfo:
        __create_a1_lane_a1_barrier(
            sf=mapInfo[shp_class],
            output_path=outputPath,
            output_name_suffix=output_suffix)
        print('[INFO] {0} -> {1} : OK'.format(shp_class.ljust(25), output_class.ljust(30)))
    else:
        print('[INFO] {0} -> {1} : NOT EXIST'.format(shp_class.ljust(25), output_class.ljust(30)))


    """ B2_SURFSIGN_POINT -> 05_DIRSIGN """
    shp_class = 'B2_SURFSIGN_POINT'
    output_class = '05_DIRSIGN'
    dbf_field_to_keep = [1,2,4]
    # 1 LINKID    VARCHAR
    # 2 SIGNTYPE  VARCHAR
    # 3 CODE      DIRECTIONSIGNTYPECODE (1 or 2)
    if shp_class in mapInfo:
        __create_cloned(
            sf=mapInfo[shp_class],
            dbf_field_to_keep=dbf_field_to_keep,
            output_path=outputPath,
            output_name=output_class+output_suffix)
        print('[INFO] {0} -> {1} : OK'.format(shp_class.ljust(25), output_class.ljust(30)))
    else:
        print('[INFO] {0} -> {1} : NOT EXIST'.format(shp_class.ljust(25), output_class.ljust(30)))


    """ B2_SURFSIGN_LINE -> 06_INTERSECTION_LINE """
    shp_class = 'B2_SURFSIGN_LINE'
    output_class = '06_INTERSECTION_LINE'
    dbf_field_to_keep = [1,2,3,4,5,6]
    # 1 LINKID    VARCHAR
    # 2 FROMNODE  VARCHAR
    # 3 TONODE    VARCHAR
    # 4 FROMLINK  VARCHAR
    # 5 TOLINK    VARCHAR
    # 6 SIGNTYPE  LINETYPECODE (1 or 2)
    if shp_class in mapInfo:
        __create_cloned(
            sf=mapInfo[shp_class],
            dbf_field_to_keep=dbf_field_to_keep,
            output_path=outputPath,
            output_name=output_class+output_suffix)
        print('[INFO] {0} -> {1} : OK'.format(shp_class.ljust(25), output_class.ljust(30)))
    else:
        print('[INFO] {0} -> {1} : NOT EXIST'.format(shp_class.ljust(25), output_class.ljust(30)))


    """ B1_SIGNAL_POINT -> 11_TRAFFIC_LIGHT """
    shp_class = 'B1_SIGNAL_POINT'
    output_class = '11_TRAFFIC_LIGHT'
    dbf_field_to_keep = [1,2]
    # 1 LINKID    VARCHAR
    # 2 SIGNTYPE  VARCHAR
    if shp_class in mapInfo:
        __create_cloned(
            sf=mapInfo[shp_class],
            dbf_field_to_keep=dbf_field_to_keep,
            output_path=outputPath,
            output_name=output_class+output_suffix)
        print('[INFO] {0} -> {1} : OK'.format(shp_class.ljust(25), output_class.ljust(30)))
    else:
        print('[INFO] {0} -> {1} : NOT EXIST'.format(shp_class.ljust(25), output_class.ljust(30)))


    """ A2_STOP -> 12_STOP_LINE """
    shp_class = 'A2_STOP'
    output_class = '12_STOP_LINE'
    dbf_field_to_keep = [1,2]
    # 1 LINKID      VARCHAR
    # 2 CODE        VARCHAR
    if shp_class in mapInfo:
        __create_cloned(
            sf=mapInfo[shp_class],
            dbf_field_to_keep=dbf_field_to_keep,
            output_path=outputPath,
            output_name=output_class+output_suffix)
        print('[INFO] {0} -> {1} : OK'.format(shp_class.ljust(25), output_class.ljust(30)))
    else:
        print('[INFO] {0} -> {1} : NOT EXIST'.format(shp_class.ljust(25), output_class.ljust(30)))


    """ B2_SURFSIGN_PLANE -> 13_SURFSIGN_PLANE"""
    shp_class = 'B2_SURFSIGN_PLANE'
    output_class = '13_SURFSIGN_PLANE'
    dbf_field_to_keep = [1,2,3,4]
    # 1 LINKID    VARCHAR
    # 2 NODEID    VARCHAR
    # 3 SIGNTYPE  PLANESIGNCODE
    # 4 LOC       PLACETYPECODE (1 or 2)
    if shp_class in mapInfo:
        __create_cloned(
            sf=mapInfo[shp_class],
            dbf_field_to_keep=dbf_field_to_keep,
            output_path=outputPath,
            output_name=output_class+output_suffix)
        print('[INFO] {0} -> {1} : OK'.format(shp_class.ljust(25), output_class.ljust(30)))
    else:
        print('[INFO] {0} -> {1} : NOT EXIST'.format(shp_class.ljust(25), output_class.ljust(30)))


    """ B1_SIGN_POINT -> 14_TRAFFIC_SIGN"""
    shp_class = 'B1_SIGN_POINT'
    output_class = '14_TRAFFIC_SIGN'
    dbf_field_to_keep = [1,2]
    # 1 LINKID    VARCHAR
    # 2 SIGNTYPE  VARCHAR
    if shp_class in mapInfo:
        __create_cloned(
            sf=mapInfo[shp_class],
            dbf_field_to_keep=dbf_field_to_keep,
            output_path=outputPath,
            output_name=output_class+output_suffix)
        print('[INFO] {0} -> {1} : OK'.format(shp_class.ljust(25), output_class.ljust(30)))
    else:
        print('[INFO] {0} -> {1} : NOT EXIST'.format(shp_class.ljust(25), output_class.ljust(30)))

    
    """ B3_POST_POINT -> 15_POST """
    shp_class = 'B3_POST_POINT'
    output_class = '15_POST'
    dbf_field_to_keep = [1,2]
    # 1 LINKID    VARCHAR
    # 2 CODE      POSTTYPECODE
    if shp_class in mapInfo:
        __create_cloned(
            sf=mapInfo[shp_class],
            dbf_field_to_keep=dbf_field_to_keep,
            output_path=outputPath,
            output_name=output_class+output_suffix)
        print('[INFO] {0} -> {1} : OK'.format(shp_class.ljust(25), output_class.ljust(30)))
    else:
        print('[INFO] {0} -> {1} : NOT EXIST'.format(shp_class.ljust(25), output_class.ljust(30)))


    """ B2_NOAUTONOMOUS_PLANE -> 16_SELFDRV_RESTRICTED_AREA"""
    shp_class = 'B2_NOAUTONOMOUS_PLANE'
    output_class = '16_SELFDRV_RESTRICTED_AREA'
    dbf_field_to_keep = [1,2]
    # 1 LINKID    VARCHAR
    # 2 SIGNTYPE  CARESIGNTYPECODE
    if shp_class in mapInfo:
        __create_cloned(
            sf=mapInfo[shp_class],
            dbf_field_to_keep=dbf_field_to_keep,
            output_path=outputPath,
            output_name=output_class+output_suffix)
        print('[INFO] {0} -> {1} : OK'.format(shp_class.ljust(25), output_class.ljust(30)))
    else:
        print('[INFO] {0} -> {1} : NOT EXIST'.format(shp_class.ljust(25), output_class.ljust(30)))


    """ C2_KM_POST -> 21_KM_POST"""
    shp_class = 'C2_KM_POST'
    output_class = '21_KM_POST'
    dbf_field_to_keep = [1,2]
    # 1 LINKID    VARCHAR
    # 2 CODE      POSTTYPECODE
    if shp_class in mapInfo:
        __create_cloned(
            sf=mapInfo[shp_class],
            dbf_field_to_keep=dbf_field_to_keep,
            output_path=outputPath,
            output_name=output_class+output_suffix)
        print('[INFO] {0} -> {1} : OK'.format(shp_class.ljust(25), output_class.ljust(30)))
    else:
        print('[INFO] {0} -> {1} : NOT EXIST'.format(shp_class.ljust(25), output_class.ljust(30)))

def ex4():
    global shp_transform_obj
    shp_transform_obj.transform(1)
    pass

if __name__ == '__main__':
    print('---------- [MAIN STARTS] ---------')

    convert_to_vz_sample_format()

    print('---------- [MAIN ENDS] ---------')
