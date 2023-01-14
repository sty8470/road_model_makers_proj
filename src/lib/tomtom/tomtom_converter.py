import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))
sys.path.append(os.path.normpath(os.path.join(current_path, '../../')))

from lib.common.logger import Logger

import json
import numpy as np

from lib.mgeo.class_defs import *
from lib.common.coord_trans_ll2utm import CoordTrans_LL2UTM

import avro.schema
from avro.datafile import DataFileReader, DataFileWriter
from avro.io import DatumReader, DatumWriter

import base64
import struct
import re

from pyproj import Proj, Transformer, CRS

# boundary 에 따라 잘라내기 위해 사용
global boundary_pt1
global boundary_pt2
boundary_pt1 = []
boundary_pt2 = []


"""
tomtom 에 있는 데이터 type 변경을 위한 함수
1. get_origin
2. convert_ddctType
3. convert_string_to_points : base64 to points
4. convert_points : LL2UTM(17) LatLng to UTM
5. getLeastMostSignificantBits : LSB/MSB to ID
6. is_out_of_xy_range
7. convert_string_to_laneType : lane_boundary code/color/width/shape 입력
8. clear_boundary : 추출 영역 설정 초기화
9. set_boundary : 추출 영역 설정
10. extract_region : 좌표가 추출 영역 안에 있는지 확인
"""

def read_avro_files(input_path):
    data = {}
    folder_list = os.listdir(input_path)
    for folder in folder_list:
        try:
            # read_path = os.path.join(input_path, folder)
            # data[folder] = DataFileReader(open(read_path+'\\part-r-00000.avro', 'rb'), DatumReader())
            data[folder] = DataFileReader(open(os.path.join(input_path, folder, 'part-r-00000.avro'), 'rb'), DatumReader())
        except:
            pass
    return data


def read_geojson_files(input_path):
    file_list = os.listdir(input_path)
    map_info = {}

    for each_file in file_list:
        file_full_path = os.path.join(input_path, each_file)
        
        # 디렉토리는 Skip
        if os.path.isdir(file_full_path):
            continue
        
        # geojson인지 체크
        filename, file_extension = os.path.splitext(each_file)
        if file_extension == '.geojson':
            # 처리
            with open(file_full_path, encoding='utf-8') as input_file:
                map_info[filename] = json.load(input_file)

    return map_info

def get_origin(centerlines):
    """    
    avro 파일 유형에서 laneCenterLine 데이터 첫번째 값으로
    원점과 UTM ZONE 찾음
    """

    try:
        attributes = centerlines[0]['attributes']
    except:
        attributes = centerlines.next()['attributes']
    for attri in attributes:
        if attri['ddctType'] == 244390646:
            for nattri in attri['nsoAttributes']:
                if nattri['ddctType'] == -121081017:
                    str_data = base64.b64decode(nattri['value']).decode('utf-8')
                    data_points = re.findall('[-]?\d+\.\d+', str_data)
                    ll_origin = [float(data_points[0]), float(data_points[1]), float(data_points[2])]
                    utm_num = utm_zone(ll_origin)
                    east, north = CoordTrans_LL2UTM(utm_num).ll2utm(ll_origin[1], ll_origin[0])
                    origin = [east, north, ll_origin[2]]
    return origin, utm_num


def convert_ddctType(ddcttype):
    """
    avro 파일에 ddctType
    """

    tomtom_data = { 
        "1122107113": "ArcType.RoadArc",
        "106595612": "BoundingBox",
        "1924495703": "BoundingBox.Height",
        "-2130631628": "BoundingBox.Width",
        "-1239460030": "ConnectionType.Continuation",
        "-1870692682": "ConnectionType.Intersect",
        "1977608019": "ConnectionType.Merge",
        "-381790251": "ConnectionType.Split",
        "-260453069": "DetailedGeometry",
        "-121081017": "DetailedGeometry.geometry",
        "-1663376657": "DetailedGeometry.type",
        "658391809": "DistanceAlong",
        "-224675254": "DistanceAlong.End",
        "-2020684723": "DistanceAlong.Start",
        "-1400588441": "FeatureWithDetailedGeometry",
        "-1227797831": "FeatureWithDetailedGeometry.Geometries",
        "1935344494": "JunctionArea",
        "2058682450": "JunctionArea.Geometries",
        "1170290987": "JunctionArea.LeftHandTraffic",
        "-728077823": "JunctionArea.TollRoad",
        "767220991": "JunctionArea.VerificationDate",
        "-1268011471": "LaneBorder",
        "-32884444": "LaneBorder.LaneBorderComponent",
        "2126486925": "LaneBorder.Length",
        "-1617743042": "LaneBorder.PassingRestriction",
        "2141407465": "LaneBorder.Width",
        "-1094000998": "LaneBorderComponent",
        "-1836887369": "LaneBorderComponent.BorderColor",
        "-1885629980": "LaneBorderComponent.BorderType",
        "979833510": "LaneBorderComponent.Geometries",
        "346157642": "LaneCenterLine",
        "-1291395400": "LaneCenterLine.EntranceLane",
        "-1777738272": "LaneCenterLine.ExitLane",
        "244390646": "LaneCenterLine.Geometries",
        "-1165827340": "LaneCenterLine.LaneType",
        "11320660": "LaneCenterLine.Length",
        "-572916081": "LaneCenterLine.OpposingTrafficPossible",
        "871265832": "LaneCenterLine.SourceQuality",
        "728941090": "LaneCenterLine.Width",
        "-1934776132": "LaneCenterLineOfLaneGroup",
        "370245627": "LaneConnection",
        "227334785": "LaneConnection.LaneConnectionType",
        "852205264": "LaneGroup",
        "-1299729752": "LaneGroup.Geometries",
        "-1356453923": "LaneGroup.LeftHandTraffic",
        "-100477259": "LaneGroup.VerificationDate",
        "-1555039619": "LaneGrouptoTrafficSign",
        "1655408688": "LaneTrajectory",
        "-1896996536": "LaneTrajectory.Geometries",
        "1714502638": "LaneTrajectory.Length",
        "-137148010": "LaneTrajectory.SourceQuality",
        "228036520": "LaneTrajectory.Width",
        "276179324": "LaneTrajectoryLine",
        "-1446342260": "LaneTrajectoryLine.Geometries",
        "-494030302": "LaneTrajectoryLine.Length",
        "-144975726": "LaneTrajectoryLine.SourceQuality",
        "-1506727788": "LaneTrajectoryLine.Width",
        "1720628291": "LaneTrajectoryLineofJunction",
        "985949935": "LaneTrajectorytoHorizontalLine",
        "-1922665639": "LaneTrajectorytoHorizontalLine.DistanceAlong",
        "-1237095426": "LeftBorderofLaneTrajectoryLine",
        "1518724947": "LeftLaneBorderOfLane",
        "-1524663433": "LeftLaneBorderOfLane.Reversed",
        "-1567018459": "LinePrecedence.DependantLines",
        "2011749460": "LinePrecedence.LineId",
        "1947317343": "NodeRelationType.Head",
        "-178585169": "NodeRelationType.Tail",
        "-841637267": "NodeType.Bifurcation",
        "-1157199008": "NodeType.Bivalent",
        "73076404": "NodeType.Convergence",
        "1281372111": "NodeType.Junction",
        "294780589": "PassingRestriction.LaneBorderpassingfromleftandright",
        "1485072440": "PassingRestriction.LaneBorderpassingnotallowed",
        "886768577": "PassingRestriction.LaneBorderpassingonlylefttoright",
        "-2092663395": "PassingRestriction.LaneBorderpassingonlyrighttoleft",
        "-271389233": "RightBorderofLaneTrajectoryLine",
        "-344801492": "RightLaneBorderOfLane",
        "-1553350266": "RightLaneBorderOfLane.Reversed",
        "2052975362": "RoadArea",
        "139837246": "RoadArea.Geometries",
        "1887235087": "RoadArea.LeftHandTraffic",
        "-571589925": "RoadArea.VerificationDate",
        "-1208863320": "RoadAreaConnection",
        "149298529": "RoadAreaConnection.RoadAreaConnectionType",
        "-332516781": "RoadCrossing",
        "-2031089843": "RoadCrossing.Geometries",
        "1735517825": "RoadCrossing.RoadCrossingType",
        "-497731961": "RoadCrossingToJunctionArea",
        "775659807": "RoadCrossingToLaneGroup",
        "1638808546": "RoadCrossingType.Bicycle",
        "1738865986": "RoadCrossingType.Pedestrian",
        "-938492224": "RoadFingerprinttoRoadNetworkArc",
        "-1972188011": "RoadNetworkArc",
        "-1670918253": "RoadNetworkArc.ArcType",
        "1575756521": "RoadNetworkArc.Length",
        "-1752492565": "RoadNetworkArc.TraversalLength",
        "1752572445": "RoadNetworkArctoRoadArea",
        "1485414783": "RoadNetworkFingerprint",
        "881821485": "RoadNetworkFingerprint.FormofWay",
        "-1829765038": "RoadNetworkFingerprint.FunctionalRoadClass",
        "-1078526519": "RoadNetworkNode",
        "-2136833717": "RoadNetworkNode.NodeType",
        "678332036": "RoadNetworkNodetoRoadNetworkArc",
        "-2010443732": "RoadNetworkNodetoRoadNetworkArc.NodeRelationType",
        "2034265829": "SpeedAssignment",
        "-2031122217": "SpeedAssignment.DistanceAlong",
        "-839240016": "SpeedAssignment.ValidityDirection",
        "-1999851982": "SpeedBump",
        "-589256178": "SpeedBump.Geometries",
        "-745676648": "SpeedBumpToLaneGroup",
        "223365818": "SpeedRestriction",
        "-1019393843": "SpeedRestriction.SpeedRestrictionInfo",
        "-1562784272": "SpeedRestrictionInfo",
        "1579600761": "SpeedRestrictionInfo.SpeedRestriction",
        "1508516011": "SpeedRestrictionInfo.SpeedRestrictionType",
        "1586625463": "SpeedRestrictionInfo.ValidityPeriod",
        "-540847512": "SpeedRestrictionInfo.VehicleType",
        "772807679": "SpeedRestrictionType.MaximumSpeed",
        "676080961": "SpeedRestrictionType.MinimumSpeed",
        "-1962778504": "SpeedRestrictionType.RecommendedSpeed",
        "1714622414": "SpeedRestrictionType.Undefined",
        "1579558": "TrafficLight",
        "795968688": "TrafficLight.FaceSize",
        "-442517407": "TrafficLight.TrafficLightType",
        "-1736719413": "TrafficSign",
        "903380502": "TrafficSign.AdditionalInfo",
        "-221155645": "TrafficSign.Category",
        "-1386077372": "TrafficSign.Color",
        "1546173379": "TrafficSign.FaceSize",
        "-541012267": "TrafficSign.Geometries",
        "-1692856105": "TrafficSign.Heading",
        "1380281186": "TrafficSign.Shape",
        "405386971": "TrafficSign.Subcategory",
        "956186098": "TrafficSign.VerificationDate",
        "-911235024": "TrajectoryBorder",
        "-1925349048": "TrajectoryBorder.Geometries",
        "1572529285": "TraversalEntry",
        "-461447586": "TraversalEntry.FromRoadArea",
        "-520465159": "TraversalEntry.Length",
        "312786323": "TraversalEntry.ToRoadArea",
        "-960198285": "ValidityDirection.Both",
        "-478645601": "ValidityDirection.Negative",
        "1710992299": "ValidityDirection.Positive"
        }

    return tomtom_data[str(ddcttype)]


def convert_str_to_point(data_points):
    # string(LatLng) > float list(utm)
    new_data_points = []
    if len(data_points)%3 == 0:
        for i in range(0, len(data_points), 3):
            point = [float(data_points[i]), float(data_points[i+1]), float(data_points[i+2])]
            in_region = extract_region(point)
            utm_num = utm_zone(point)
            east, north = CoordTrans_LL2UTM(utm_num).ll2utm(point[1], point[0])
            new_data_point = [east, north, point[2]]
            new_data_points.append(new_data_point)
    return new_data_points, in_region


def convert_string_to_points_avro(str_data):
    # avro 형식에서는 좌표정보가 base64로 저장
    str_data = base64.b64decode(str_data).decode('utf-8')
    data_type = re.sub('[^A-Za-z]', '', str_data)
    data_points = re.findall('[-]?\d+\.\d+', str_data)

    new_data_points, in_region = convert_str_to_point(data_points)

    return data_type, new_data_points, in_region


def convert_string_to_points_json(str_data):
    # json 형식(avro에서 파싱한 형태)에서는 base64이 lat/lng으로 파싱 저장
    data_type = re.sub('[^A-Za-z]', '', str_data)
    data_points = re.findall('[-]?\d+\.\d+', str_data)
    
    new_data_points, in_region = convert_str_to_point(data_points)
    return data_type, new_data_points



def utm_zone(point):
    # LatLng > utm_zone
    lnt = point[0]
    lat = point[1]
    num = 180 + lnt
    zone_con = int(num//6)
    return zone_con+1


def transformer_point(point):
    # point(LatLng) > point(utm), utm_zone
    utm_num = utm_zone(point)
    east, north = CoordTrans_LL2UTM(utm_num).ll2utm(point[1], point[0])
    new_point = [east, north, point[2]]
    return new_point, utm_num


def lat_lng_point(str_data):
    data_type = re.sub('[^A-Za-z]', '', str_data)
    data_points = re.findall('[-]?\d+\.\d+', str_data)
    new_data_points = []
    if len(data_points)%3 == 0:
        for i in range(0, len(data_points), 3):
            new_data_point = [float(data_points[i+1]), float(data_points[i]), float(data_points[i+2])]
            new_data_points.append(new_data_point)
    return data_type, new_data_points
    

def convert_points(points):
    new_data_points = []
    for point in points:
        utm_num = utm_zone(point)
        east, north = CoordTrans_LL2UTM(utm_num).ll2utm(point[1], point[0])
        new_data_point = [east, north, point[2]]
        new_data_points.append(new_data_point)
    return np.array(new_data_points)


def getLeastMostSignificantBits(s):
    sp = s.split("-")
    lsb_s = "".join(sp[-2:])
    lsb = int(lsb_s,16)
    if int(lsb_s[0],16)>7:
        # negative
        lsb = lsb-0x10000000000000000

    msb_s = "".join(sp[:3])
    msb = int(msb_s,16)
    if int(msb_s[0],16)>7:
        # negative
        msb = msb-0x10000000000000000

    return str('{}_{}'.format(lsb, msb))


def is_out_of_xy_range(points):

    center_point = [585354.95, 4512229.34]

    x = points[:,0]
    y = points[:,1]
    z = points[:,2]

    if x.max() < center_point[0] - 10000 or center_point[0] + 10000 < x.min():
        x_out = True
    else:
        x_out = False

    # y축에 대해
    if y.max() < center_point[1] - 10000 or center_point[1] + 10000 < y.min():
        y_out = True
    else:
        y_out = False
    return x_out or y_out



def convert_string_to_laneType(str_data, lane_boundary):
    
    # 차선이 2줄 이면 간격 50cm
    # BARRIER/GUARDRAIL → border
    # CURB → shoulder

    lane_type = 599
    lane_width = 0.15
    dash_interval_L1 = 3
    dash_interval_L2 = 3
    lane_shape = ["solid"]

    if str_data in ['BARRIER_CABLE',
                    'BARRIER_JERSEY',
                    'BARRIER_SOUND',
                    'CONCRETE_BARRIER']:
        lane_type = 199 #
        lane_width = 0.15
        dash_interval_L1 = 3
        dash_interval_L2 = 3
        lane_shape = ["Solid"]

    elif str_data in ['LEFT_CURB',
                        'RIGHT_CURB',
                        'BI_CURB']:
        lane_type = 101 # curb
        lane_width = 0.15
        dash_interval_L1 = 3
        dash_interval_L2 = 3
        lane_shape = ["Solid"]

    elif str_data in ['LONG_DASHED_LINE',
                        'NO_MARKING',
                        'SHADED_AREA_MARKING',
                        'SHORT_DASHED_LINE',
                        'SINGLE_SOLID_LINE',
                        'UNKNOWN']:
        lane_type = 103 # Lane marking 
        lane_width = 0.15
        if str_data == 'LONG_DASHED_LINE':
            dash_interval_L1 = 6
            dash_interval_L2 = 4
            lane_shape = ["Broken"]
        elif str_data == 'SHORT_DASHED_LINE':
            dash_interval_L1 = 4
            dash_interval_L2 = 1
            lane_shape = ["Broken"]
        elif str_data == 'NO_MARKING':
            dash_interval_L1 = 0
            dash_interval_L2 = 0
            lane_shape = ["NoMark"]
        else:
            dash_interval_L1 = 3
            dash_interval_L2 = 3
            lane_shape = ["Solid"]

    elif str_data in ['FENCE']: # Passing Restriction value 3
        lane_type = 1023 # Physical barriers
        lane_width = 0.15
        dash_interval_L1 = 3
        dash_interval_L2 = 3
        lane_shape = ["Solid"]

    elif str_data in ['UNKNOWN_BARRIER']: # Passing Restriction value 3
        lane_type = 1022 # Physical barriers
        lane_width = 0.15
        dash_interval_L1 = 3
        dash_interval_L2 = 3
        lane_shape = ["Solid"]

    elif str_data in ['GUARDRAIL']: # Passing Restriction value 3
        lane_type = 1021 # Physical barriers
        lane_width = 0.15
        dash_interval_L1 = 3
        dash_interval_L2 = 3
        lane_shape = ["Solid"]

    elif str_data in ['ROAD_BORDER',
                        'UNDEFINED_ROAD_BORDER']: # Passing Restriction value 3
        lane_type = 105 # Road border
        lane_width = 0.15
        dash_interval_L1 = 3
        dash_interval_L2 = 3
        lane_shape = ["Solid"]
    
    lane_boundary.lane_type_def = 'tomtom'
    lane_boundary.lane_type = [lane_type]
    lane_boundary.lane_width = lane_width
    lane_boundary.dash_interval_L1 = dash_interval_L1
    lane_boundary.dash_interval_L2 = dash_interval_L2
    lane_boundary.lane_shape = lane_shape
    lane_boundary.lane_type_offset = [0]

    return lane_boundary
    
def clear_boundary():
    global boundary_pt1
    global boundary_pt2

    boundary_pt1.clear()
    boundary_pt2.clear()

def set_boundary(b1, b2, b3, b4):
    '''
    b1, b2 - lat/lon pair #1
    b3, b4 - lat/lon pair #2
    '''
    global boundary_pt1
    global boundary_pt2

    boundary_pt1 = [b1, b2]
    boundary_pt2 = [b3, b4]
    print('pt1:{}, pt2{}'.format(str(boundary_pt1), str(boundary_pt2)))

def extract_region(coord_to_check):
    global boundary_pt1
    global boundary_pt2

    # boundry 가 설정되지 않으면 추출 영역으로 판단한다.
    if len(boundary_pt1) == 0 or len(boundary_pt2) == 0:
        return True

    within_lat = False
    within_lon = False
    lat_min = boundary_pt1[0]
    lat_max = boundary_pt2[0]
    lon_min = boundary_pt1[1]
    lon_max = boundary_pt2[1]
    lat_chk = coord_to_check[1]
    lon_chk = coord_to_check[0]

    if (lat_chk > lat_min
        and lat_chk < lat_max):
        within_lat =  True

    if (abs(lon_chk) > abs(lon_min)
        and abs(lon_chk) < abs(lon_max)):
        within_lon = True

    if (within_lat is True
        and within_lon is True):
        return True
    else:
        return False


def convert_sign(category, sub_category):

    # MUTCD 있는 것만 표시
    odr_signal_type = 'R1'
    odr_signal_sub_type = 1
    odr_signal_value = 0
    odr_signal_unit = ''

    if category == 'Cancellation':
        if sub_category == 'sub_category':
            pass
    elif category == 'InformationSign':
        if sub_category == 'Cul de sac':
            pass
        elif sub_category == 'Cyclist crossing':
            pass
        elif sub_category == 'Express road end':
            odr_signal_type = 'W19'
            odr_signal_sub_type = 4
        elif sub_category == 'Express road start':
            pass
        elif sub_category == 'Ferry':
            odr_signal_type = 'I'
            odr_signal_sub_type = 9
        elif sub_category == 'Highway end':
            pass
        elif sub_category == 'Highway start':
            pass
        elif sub_category == 'One Way':
            odr_signal_type = 'R6'
            odr_signal_sub_type = 1
        elif sub_category == 'One Way End':
            pass
        elif sub_category == 'Other':
            pass
        elif sub_category == 'Parking':
            pass
        elif sub_category == 'Pedestrian crossing':
            odr_signal_type = 'W11'
            odr_signal_sub_type = 2
        elif sub_category == 'Pedestrians zone':
            odr_signal_type = 'W11'
            odr_signal_sub_type = 2
        elif sub_category == 'Pedestrians zone cancellation':
            pass
        elif sub_category == 'Priority on narrow road':
            pass
        elif sub_category == 'School zone':
            odr_signal_type = 'S1'
            odr_signal_sub_type = 1
        elif sub_category == 'School zone cancellation':
            odr_signal_type = 'S5'
            odr_signal_sub_type = 2
        elif sub_category == 'Speed bump':
            odr_signal_type = 'W8'
            odr_signal_sub_type = 1
        elif sub_category == 'Truck route':
            pass
        elif sub_category == 'U Turn Allowed':
            odr_signal_type = 'R3'
            odr_signal_sub_type = '26a'
        elif sub_category == 'Unreadable':
            pass
        elif sub_category == 'Zebra crossing':
            pass

    elif category == 'LaneInformation':
        if sub_category == 'Lane added left':
            odr_signal_type = 'W4'
            odr_signal_sub_type = 3
        elif sub_category == 'Lane added right':
            odr_signal_type = 'W4'
            odr_signal_sub_type = 3
        elif sub_category == 'Lane ends':
            pass
        elif sub_category == 'Lane ends center':
            pass
        elif sub_category == 'Lane ends left':
            odr_signal_type = 'W4'
            odr_signal_sub_type = 1
        elif sub_category == 'Lane ends right':
            odr_signal_type = 'W4'
            odr_signal_sub_type = 1
        elif sub_category == 'Lane merge':
            odr_signal_type = 'W4'
            odr_signal_sub_type = 1
        elif sub_category == 'LaneInformation':
            pass

    elif category == 'Mandatory':
        if sub_category == 'Maneuver':
            pass
        elif sub_category == 'Other':
            pass
        elif sub_category == 'Unreadable':
            pass

    elif category == 'Name':
        if sub_category == 'Brunnel Name':
            pass
        elif sub_category == 'River Name':
            pass
        elif sub_category == 'Street Name':
            pass
        
    elif category == 'Overtaking':
        if sub_category == 'Cancellation':
            pass
        elif sub_category == 'Start':
            pass

    elif category == 'OvertakingLane':
        if sub_category == 'Overtaking lane':
            pass

    elif category == 'POI':
        odr_signal_type = 'E5'
        odr_signal_sub_type = 1

    elif category == 'Priority':
        if sub_category == 'Priority Road':
            pass
        elif sub_category == 'Priority Road Cancellation':
            pass
        elif sub_category == 'Priority Subplate':
            pass


    elif category == 'Prohibition':
        if sub_category == 'Hazardous Material':
            pass
        elif sub_category == 'Lane Dependent Maximum Dimension':
            pass
        elif sub_category == 'Maximum Dimension':
            pass
        elif sub_category == 'No Entry':
            odr_signal_type = 'R5'
            odr_signal_sub_type = 1
        elif sub_category == 'No parking':
            odr_signal_type = 'R8'
            odr_signal_sub_type = 3
        elif sub_category == 'No pedestrians':
            odr_signal_type = 'R9'
            odr_signal_sub_type = 3
        elif sub_category == 'No Stopping':
            odr_signal_type = 'R8'
            odr_signal_sub_type = 5
        elif sub_category == 'No turn':
            odr_signal_type = 'R3'
            odr_signal_sub_type = 3
        elif sub_category == 'No Turn Left':
            odr_signal_type = 'R3'
            odr_signal_sub_type = 2
        elif sub_category == 'No Turn Right':
            odr_signal_type = 'R3'
            odr_signal_sub_type = 1
        elif sub_category == 'No U Turn':
            odr_signal_type = 'R3'
            odr_signal_sub_type = 4
        elif sub_category == 'No waiting':
            pass
        elif sub_category == 'No way':
            odr_signal_type = 'R3'
            odr_signal_sub_type = 27
        elif sub_category == 'Other':
            pass
        elif sub_category == 'Prohibition on narrow road':
            pass
        elif sub_category == 'Unreadable':
            pass
        elif sub_category == 'Vehicle Restriction':
            pass


    elif category == 'RailwayCrossing':
        if sub_category == 'Cross':
            odr_signal_type = 'R15'
            odr_signal_sub_type = 1
        elif sub_category == 'Guarded warning':
            odr_signal_type = 'W3'
            odr_signal_sub_type = 3
        elif sub_category == 'Railway Warning':
            odr_signal_type = 'W3'
            odr_signal_sub_type = 3
        elif sub_category == 'Unguarded':
            odr_signal_type = 'W3'
            odr_signal_sub_type = 3
        elif sub_category == 'Unguarded warning':
            odr_signal_type = 'W3'
            odr_signal_sub_type = 3

    elif category == 'RNR':
        odr_signal_type = 'M1'
        odr_signal_sub_type = 1
        odr_signal_value = 101

    elif category == 'SignPost':
        odr_signal_type = 'E5'
        odr_signal_sub_type = 1

    elif category == 'Speed limit warning No Value':
        pass

    elif category == 'SpeedRestriction':
        if sub_category == 'BUA':
            pass
        elif sub_category == 'BUA Cancellation':
            pass
        elif sub_category == 'Day/Night':
            pass
        elif sub_category == 'End Day/Night':
            pass
        elif sub_category == 'Lane Dependent Speed':
            pass
        elif sub_category == 'Minimum Speed':
            odr_signal_type = 'R2'
            odr_signal_sub_type = '4P'
        elif sub_category == 'Minimum Speed Cancellation':
            pass
        elif sub_category == 'Recommended Speed':
            odr_signal_type = 'W13'
            odr_signal_sub_type = '1'
            odr_signal_value = 40
            odr_signal_unit = 'mph'
        elif sub_category == 'Recommended Speed Cancellation':
            pass
        elif sub_category == 'Residential Area':
            pass
        elif sub_category == 'Residential Area Cancellation':
            pass
        elif sub_category == 'Speed':
            odr_signal_type = 'R2'
            odr_signal_sub_type = '1'
            odr_signal_value = 50
            odr_signal_unit = 'mph'
        elif sub_category == 'Speed Cancellation':
            pass
        elif sub_category == 'Zone':
            pass
        elif sub_category == 'Zone Cancellation':
            pass
        elif sub_category == 'Zone Cancellation No Value':
            pass
        elif sub_category == 'Zone No Value':
            pass

    elif category == 'Stop':
        odr_signal_type = 'R1'
        odr_signal_sub_type = 1

    elif category == 'TollRoad':
        pass
    elif category == 'Undefined':
        pass
    elif category == 'Variable':
        pass
    elif category == 'Warning':
        if sub_category == 'Accident hazard':
            pass
        elif sub_category == 'Aircraft':
            pass
        elif sub_category == 'Animal crossing':
            pass
        elif sub_category == 'Avalanche area':
            pass
        elif sub_category == 'Bus':
            pass
        elif sub_category == 'Changing to left lane':
            pass
        elif sub_category == 'Changing to right lane':
            pass
        elif sub_category == 'Children':
            odr_signal_type = 'S1'
            odr_signal_sub_type = 1
        elif sub_category == 'Congestion hazard':
            pass
        elif sub_category == 'Cross wind':
            pass
        elif sub_category == 'Congestion hazard':
            pass
        elif sub_category == 'Cyclist':
            pass
        elif sub_category == 'Dangerous curve':
            pass
        elif sub_category == 'Dead end':
            odr_signal_type = 'W14'
            odr_signal_sub_type = 1
        elif sub_category == 'Divided highway end':
            odr_signal_type = 'W6'
            odr_signal_sub_type = 2
        elif sub_category == 'Divided highway start':
            odr_signal_type = 'W6'
            odr_signal_sub_type = 1
        elif sub_category == 'Divided road end':
            pass
        elif sub_category == 'Divided road start':
            pass
        elif sub_category == 'Exit left':
            pass
        elif sub_category == 'Exit right':
            pass
        elif sub_category == 'Falling rocks':
            pass
        elif sub_category == 'Fire trucks':
            pass
        elif sub_category == 'Foggy area':
            odr_signal_type = 'W8'
            odr_signal_sub_type = 22
        elif sub_category == 'General danger':
            pass
        elif sub_category == 'Icy conditions':
            pass
        elif sub_category == 'Intersection':
            pass
        elif sub_category == 'Intersection with priority to the right':
            pass
        elif sub_category == 'Left junction':
            odr_signal_type = 'M2'
            odr_signal_sub_type = 2
        elif sub_category == 'Left lane closing':
            pass
        elif sub_category == 'Left merging traffic':
            pass
        elif sub_category == 'Loose gravel':
            pass
        elif sub_category == 'Maximum Dimension':
            pass
        elif sub_category == 'Movable bridge':
            pass
        elif sub_category == 'Narrow bridge':
            odr_signal_type = 'W5'
            odr_signal_sub_type = 2
        elif sub_category == 'Other':
            pass
        elif sub_category == 'Pedestrian crossing':
            odr_signal_type = 'W11'
            odr_signal_sub_type = 2
        elif sub_category == 'Pedestrian crossing ahead':
            odr_signal_type = 'W11'
            odr_signal_sub_type = 2
        elif sub_category == 'Pedestrians':
            pass
        elif sub_category == 'Priority Road':
            pass
        elif sub_category == 'Right lane closing':
            pass
        elif sub_category == 'Road branch':
            pass
        elif sub_category == 'Road closed':
            odr_signal_type = 'R11'
            odr_signal_sub_type = 2
        elif sub_category == 'Road narrows':
            odr_signal_type = 'W5'
            odr_signal_sub_type = 1
        elif sub_category == 'Road narrows left':
            pass
        elif sub_category == 'Road narrows right':
            pass
        elif sub_category == 'Road Works':
            pass
        elif sub_category == 'Roundabout':
            pass
        elif sub_category == 'Sharp curve left':
            pass
        elif sub_category == 'Sharp curve right':
            pass
        elif sub_category == 'Shoulder':
            pass
        elif sub_category == 'Slippery road':
            pass
        elif sub_category == 'Speed bump':
            pass
        elif sub_category == 'Speed limit warning':
            pass
        elif sub_category == 'Speed limit warning No Value':
            pass
        elif sub_category == 'Steep hill down':
            pass
        elif sub_category == 'Steep hill up':
            pass
        elif sub_category == 'Stop ahead':
            odr_signal_type = 'W3'
            odr_signal_sub_type = 1
        elif sub_category == 'Traffic Lights':
            odr_signal_type = 'W3'
            odr_signal_sub_type = 3
        elif sub_category == 'Trucks':
            odr_signal_type = 'W11'
            odr_signal_sub_type = 10
        elif sub_category == 'Two Way Traffic':
            odr_signal_type = 'W6'
            odr_signal_sub_type = 3
        elif sub_category == 'Uneven road':
            pass
        elif sub_category == 'Unreadable':
            pass
        elif sub_category == 'Wild life':
            pass
        elif sub_category == 'Wind':
            pass
        elif sub_category == 'Winding road starting left':
            pass
        elif sub_category == 'Winding road starting right':
            pass
        elif sub_category == 'Yield':
            odr_signal_type = 'R1'
            odr_signal_sub_type = 2
        elif sub_category == 'Yield ahead':
            odr_signal_type = 'W3'
            odr_signal_sub_type = 2
        elif sub_category == 'Yield the right-of-way':
            odr_signal_type = 'R1'
            odr_signal_sub_type = 2
            
    return odr_signal_type, odr_signal_sub_type, odr_signal_value, odr_signal_unit
