import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))
sys.path.append(os.path.normpath(os.path.join(current_path, '../../')))

import json
import numpy as np

from lib.mgeo.class_defs import *
from lib.common.coord_trans_ll2utm import CoordTrans_LL2UTM

import avro.schema
from fastavro import reader

import base64
import struct
import re

from pyproj import Proj, Transformer, CRS

# boundary 에 따라 잘라내기 위해 사용
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
"""

def get_avro_files_path(input_path):
    path = {}
    folder_list = os.listdir(input_path)
    for folder in folder_list:
        try:
            avro_file_path = os.path.join(input_path, folder, 'part-r-00000.avro')
            if os.path.exists(avro_file_path):
                path[folder] = avro_file_path
            else:
                print('[WARNING] No avro file in {}\\{}'.format(input_path, folder))
        except:
            pass
    return path

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

def get_origin_fa(centerlines_path):
    with open(centerlines_path, 'rb') as f:
        for centerlines in reader(f):
            if 'attributes' in centerlines:
                attributes = centerlines['attributes']
                break
    point = [0, 0, 0]
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

# avro 파일
def convert_ddctType(ddcttype):
    tomtom_data = { "1122107113": "ArcType.RoadArc",
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
        "1710992299": "ValidityDirection.Positive"}

    return tomtom_data[str(ddcttype)]

def convert_string_to_points_avro(str_data):
    in_region = False
    str_data = base64.b64decode(str_data).decode('utf-8')
    data_type = re.sub('[^A-Za-z]', '', str_data)
    data_points = re.findall('[-]?\d+\.\d+', str_data)
    new_data_points = []
    if len(data_points)%3 == 0:
        for i in range(0, len(data_points), 3):
            point = [float(data_points[i]), float(data_points[i+1]), float(data_points[i+2])]
            in_region = extract_region(point)
            utm_num = utm_zone(point)
            east, north = CoordTrans_LL2UTM(utm_num).ll2utm(point[1], point[0])
            new_data_point = [east, north, point[2]]
            new_data_points.append(new_data_point)

    return data_type, new_data_points, in_region

def convert_string_to_points_json(str_data):
    data_type = re.sub('[^A-Za-z]', '', str_data)
    data_points = re.findall('[-]?\d+\.\d+', str_data)
    new_data_points = []
    if len(data_points)%3 == 0:
        for i in range(0, len(data_points), 3):
            point = [float(data_points[i]), float(data_points[i+1]), float(data_points[i+2])]
            utm_num = utm_zone(point)
            east, north = CoordTrans_LL2UTM(utm_num).ll2utm(point[1], point[0])
            new_data_point = [east, north, point[2]]
            new_data_points.append(new_data_point)

    return data_type, new_data_points

# 경도 기준
def utm_zone(point):
    lnt = point[0]
    lat = point[1]
    num = 180 + lnt
    zone_con = int(num//6)
    return zone_con+1

def transformer_point(point):
    utm_num = utm_zone(point)

    east, north = CoordTrans_LL2UTM(utm_num).ll2utm(point[1], point[0])
    new_point = [east, north, point[2]]
    return new_point


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
        east, north = CoordTrans_LL2UTM(10).ll2utm(point[1], point[0])
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
    lane_boundary.lane_type = lane_type
    lane_boundary.lane_width = lane_width
    lane_boundary.dash_interval_L1 = dash_interval_L1
    lane_boundary.dash_interval_L2 = dash_interval_L2
    lane_boundary.lane_shape = lane_shape

    return lane_boundary


def clear_boundary():
    global boundary_pt1
    global boundary_pt2

    boundary_pt1.clear()
    boundary_pt2.clear()


def set_boundary(self, b1, b2, b3, b4):
    '''
    b1, b2 - lat/lon pair #1
    b3, b4 - lat/lon pair #2
    '''
    global boundary_pt1
    global boundary_pt2

    boundary_pt1 = [b1, b2]
    boundary_pt2 = [b3, b4]


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
