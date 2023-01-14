import lxml.etree as etree
import numpy as np

def get_s(x):
    return x.s

def xml_get_attrib(xml, name, type = None, default=None) :
    ret = default
    if name in xml.attrib :
        if type == None : 
            ret = xml.attrib[name]
        else :  
            ret = type(xml.attrib[name])
    return ret

def make_list_by_tag(xml, tag, type) :
    tag_item_all = xml.findall(tag)
    tag_item_list = list()
    for tag_item in tag_item_all :
        if type == XodrPolynomial :
            if 's' not in tag_item.attrib and 'sOffset' not in tag_item.attrib:
                continue
        tag_item_list.append(type(tag_item))

    return tag_item_list

def set_length(list_all, total_length):
    list_new = list()
    s_current = float(0)
    s_next = float(0)
    for list_idx, list_item in enumerate(list_all) :
        s_next = list_all[list_idx + 1].s if list_idx < (len(list_all)-1) else total_length
        length = s_next - s_current
        s_current = s_next
        list_item.set_length(length)
        list_new.append(list_item)

    return list_new

class XodrRoadLink:
    def __init__(self, xml):
        self.elementType = xml_get_attrib(xml, 'elementType')
        self.elementId = xml_get_attrib(xml, 'elementId')
        self.contactPoint = xml_get_attrib(xml, 'contactPoint')

#s, a, b, c, d
class XodrPolynomial:
    def __init__(self, polynomial_type_xml):
        if 's' in polynomial_type_xml.attrib:
            self.s = xml_get_attrib(polynomial_type_xml, 's', float, 0.0)
        elif 'sOffset' in polynomial_type_xml.attrib:
            self.s = xml_get_attrib(polynomial_type_xml, 'sOffset', float, 0.0)
        self.a = xml_get_attrib(polynomial_type_xml, 'a', float)
        self.b = xml_get_attrib(polynomial_type_xml, 'b', float)
        self.c = xml_get_attrib(polynomial_type_xml, 'c', float)
        self.d = xml_get_attrib(polynomial_type_xml, 'd', float)

class XodrLaneHeight:
    def __init__(self, xml):
        self.s = xml_get_attrib(xml, 'sOffset', float, 0.0)
        self.inner = xml_get_attrib(xml, 'inner', float)
        self.outer = xml_get_attrib(xml, 'outer', float)

class XodrRoadMark:
    def __init__(self, xml):
        self.s = xml_get_attrib(xml, 'sOffset', float, 0.0)
        self.lane_change = xml_get_attrib(xml, 'laneChange')
        self.type = xml_get_attrib(xml, 'type')
        self.color = xml_get_attrib(xml, 'color')
        self.width = xml_get_attrib(xml, 'width', float, 0.0)

class XodrLane:
    def __init__(self, lane_xml):
        self.id = xml_get_attrib(lane_xml, 'id', int)
        self.type = xml_get_attrib(lane_xml, 'type')

        width_list = make_list_by_tag(lane_xml, "./width", XodrPolynomial)
        self.width_list = sorted(width_list, key=get_s)

        height_list = make_list_by_tag(lane_xml, "./height", XodrLaneHeight)
        self.height_list = sorted(height_list, key=get_s)

        self.predecessor = None
        self.successor = None

        predecessor = lane_xml.find("./link/predecessor")
        if not predecessor == None :
            self.predecessor = xml_get_attrib(predecessor, 'id', int)

        successor = lane_xml.find("./link/successor")
        if not successor == None :
            self.successor = xml_get_attrib(successor, 'id', int)

        self.lane_change_left = False
        self.lane_change_right = False
        road_mark_list = make_list_by_tag(lane_xml, "./roadMark", XodrRoadMark)
        self.road_mark_list = road_mark_list
        
        for road_mark in road_mark_list :
            if road_mark.lane_change == "both" :
                self.lane_change_left = True
                self.lane_change_right = True
            elif road_mark.lane_change == "increase" :
                self.lane_change_left = True
            elif road_mark.lane_change == "decrease" :
                self.lane_change_right = True

class XodrLaneSection:
    def __init__(self, lane_section_xml):
        self.s = xml_get_attrib(lane_section_xml, 's', float, 0.0)

        self.left_lane_list = make_list_by_tag(lane_section_xml, "./left/lane", XodrLane)
        self.right_lane_list = make_list_by_tag(lane_section_xml, "./right/lane", XodrLane)
        center_lane_list = make_list_by_tag(lane_section_xml, "./center/lane", XodrLane)
        self.center_lane = center_lane_list[0]

        self.left_lane_list = sorted(self.left_lane_list, key=lambda x:x.id, reverse=False)
        self.right_lane_list = sorted(self.right_lane_list, key=lambda x:x.id, reverse=True)

    def set_length(self, length):
        self.length = length

class XodrValidity :
    def __init__(self, xml):
        self.from_lane = xml_get_attrib(xml, 'fromLane', int)
        self.to_lane = xml_get_attrib(xml, 'toLane', int)

class XodrSignal:
    def __init__(self, signal_xml):
        self.id = xml_get_attrib(signal_xml, 'id')
        self.name = xml_get_attrib(signal_xml, 'name')
        self.s = xml_get_attrib(signal_xml, 's', float, 0.0)
        self.t = xml_get_attrib(signal_xml, 't', float, 0.0)
        self.z_offset = xml_get_attrib(signal_xml, 'zOffset', float, 0.0)
        self.h_offset = xml_get_attrib(signal_xml, 'hOffset', float, 0.0)
        self.roll = xml_get_attrib(signal_xml, 'roll', float, 0.0)
        self.pitch = xml_get_attrib(signal_xml, 'pitch', float, 0.0)
        self.orientation = xml_get_attrib(signal_xml, 'orientation')
        self.dynamic = xml_get_attrib(signal_xml, 'dynamic')
        self.country = xml_get_attrib(signal_xml, 'country')
        self.type = xml_get_attrib(signal_xml, 'type')
        self.subtype = xml_get_attrib(signal_xml, 'subtype')
        self.value = xml_get_attrib(signal_xml, 'value', float)
        self.text = xml_get_attrib(signal_xml, 'hOffset')
        self.unit = xml_get_attrib(signal_xml, 'unit')
        self.height = xml_get_attrib(signal_xml, 'height', float)
        self.width = xml_get_attrib(signal_xml, 'width', float)

        self.validity_list = make_list_by_tag(signal_xml, "./validity", XodrValidity)

class XodrCornerRoad:
    def __init__(self, xml):
        self.s = xml_get_attrib(xml, 's', float, 0.0)
        self.t = xml_get_attrib(xml, 't', float, 0.0)

class XodrCornerLocal:
    def __init__(self, xml):
        self.u = xml_get_attrib(xml, 'u', float, 0.0)
        self.v = xml_get_attrib(xml, 'v', float, 0.0)
        self.z = xml_get_attrib(xml, 'z', float, 0.0)
        self.height = xml_get_attrib(xml, 'height', float, 0.0)

class XodrUserData :
    def __init__(self, xml):
        self.code = xml_get_attrib(xml, 'code')
        self.value = xml_get_attrib(xml, 'value')

class XodrObject:
    def __init__(self, xml):
        self.id = xml_get_attrib(xml, 'id')
        self.name = xml_get_attrib(xml, 'name')
        self.s = xml_get_attrib(xml, 's', float, 0.0)
        self.t = xml_get_attrib(xml, 't', float, 0.0)
        self.z_offset = xml_get_attrib(xml, 'zOffset', float, 0.0)
        self.hdg = xml_get_attrib(xml, 'hdg', float, 0.0)
        self.roll = xml_get_attrib(xml, 'roll', float, 0.0)
        self.pitch = xml_get_attrib(xml, 'pitch', float, 0.0)
        self.orientation = xml_get_attrib(xml, 'orientation')
        self.type = xml_get_attrib(xml, 'type')
        self.height = xml_get_attrib(xml, 'height', float)
        self.width = xml_get_attrib(xml, 'width', float)
        self.length = xml_get_attrib(xml, 'length', float)

        self.corner_road_list = make_list_by_tag(xml, "./outline/cornerRoad", XodrCornerRoad)
        self.corner_local_list = make_list_by_tag(xml, "./outline/cornerLocal", XodrCornerLocal)
        self.userdata_list = make_list_by_tag(xml, "./userData", XodrUserData)

class XodrSignalRef:
    def __init__(self, xml):
        self.id = xml_get_attrib(xml, 'id')
        self.s = xml_get_attrib(xml, 's', float, 0.0)
        self.t = xml_get_attrib(xml, 't', float, 0.0)
        self.orientation = xml_get_attrib(xml, 'orientation')
        self.validity_list = make_list_by_tag(xml, "./validity", XodrValidity)

class XodrSpeed:
    def __init__(self, xml):
        self.max = xml_get_attrib(xml, 'max', float)
        self.unit = xml_get_attrib(xml, 'unit')

class XodrType:
    def __init__(self, xml):
        self.s = xml_get_attrib(xml, 's', float, 0.0)
        self.type = xml_get_attrib(xml, 'type')
        self.speed_unit = None
        self.speed_max = None
        speed_list = make_list_by_tag(xml, "./speed", XodrSpeed)
        if len(speed_list) > 0 :
            self.speed_unit = speed_list[0].unit
            self.speed_max = speed_list[0].max

class XodrGeometry:
    def __init__(self, geometry_xml):
        self.s = xml_get_attrib(geometry_xml, 's', float, 0.0)
        self.x = xml_get_attrib(geometry_xml, 'x', float)
        self.y = xml_get_attrib(geometry_xml, 'y', float)
        self.hdg = xml_get_attrib(geometry_xml, 'hdg', float)
        self.length = xml_get_attrib(geometry_xml, 'length', float)

        self.geo_type = None
        if(not (geometry_xml.find("./line") == None)) :
            self.geo_type = "line"
        elif(not (geometry_xml.find("./arc") == None)) :
            self.geo_type = "arc"
            arc = geometry_xml.find("./arc")
            self.arc_curvature = xml_get_attrib(arc, 'curvature', float)
        elif(not (geometry_xml.find("./spiral") == None)) :
            self.geo_type = "spiral"
            spiral = geometry_xml.find("./spiral")
            self.spiral_curvStart = xml_get_attrib(spiral, 'curvStart', float)
            self.spiral_curvEnd = xml_get_attrib(spiral, 'curvEnd', float)
        elif(not (geometry_xml.find("./poly3") == None)) :
            self.geo_type = "poly3"
            poly3 = geometry_xml.find("./poly3")
            self.poly3_a = xml_get_attrib(poly3, 'a', float)
            self.poly3_b = xml_get_attrib(poly3, 'b', float)
            self.poly3_c = xml_get_attrib(poly3, 'c', float)
            self.poly3_d = xml_get_attrib(poly3, 'd', float)
        elif(not (geometry_xml.find("./paramPoly3") == None)) :
            self.geo_type = "paramPoly3"
            paramPoly3 = geometry_xml.find("./paramPoly3")
            self.paramPoly3_aU = xml_get_attrib(paramPoly3, 'aU', float)
            self.paramPoly3_bU = xml_get_attrib(paramPoly3, 'bU', float)
            self.paramPoly3_cU = xml_get_attrib(paramPoly3, 'cU', float)
            self.paramPoly3_dU = xml_get_attrib(paramPoly3, 'dU', float)
            self.paramPoly3_aV = xml_get_attrib(paramPoly3, 'aV', float)
            self.paramPoly3_bV = xml_get_attrib(paramPoly3, 'bV', float)
            self.paramPoly3_cV = xml_get_attrib(paramPoly3, 'cV', float)
            self.paramPoly3_dV = xml_get_attrib(paramPoly3, 'dV', float)
            self.paramPoly3_pRange = xml_get_attrib(paramPoly3, 'pRange')
            if self.paramPoly3_pRange == None :
                self.paramPoly3_pRange = "normalized"

    def gen_paramPoly3_points(self) :
        if self.geo_type != "paramPoly3" :
            return
        p_interval = 0.01
        p_length = 1.0
        p = 0.0
        s = 0.0
        aU = self.paramPoly3_aU
        bU = self.paramPoly3_bU
        cU = self.paramPoly3_cU
        dU = self.paramPoly3_dU
        aV = self.paramPoly3_aV
        bV = self.paramPoly3_bV
        cV = self.paramPoly3_cV
        dV = self.paramPoly3_dV

        self.points = dict()
        if self.paramPoly3_pRange != "normalized":
            p_length = self.length
            p_interval = p_interval * self.length

        u_prev = aU
        v_prev = aV
        while p <= p_length :
            u = aU + bU*p + cU*p*p + dU*p*p*p
            v = aV + bV*p + cV*p*p + dV*p*p*p

            du = u-u_prev
            dv = v-v_prev
            
            s += np.sqrt(du*du + dv*dv)

            self.points[s] = [s, u, v, p]
            p += p_interval
            u_prev = u
            v_prev = v

    def get_point_by(self, s) :
        prev_pnt = [0,0,0,0]
        next_pnt = [0,0,0,0]
        for pnt_idx in self.points:
            pnt = self.points[pnt_idx]
            if pnt[0] >= s :
                next_pnt = pnt
                break
            prev_pnt = pnt

        weight = 0
        if (next_pnt[0] - prev_pnt[0]) != 0:
            weight = (next_pnt[0] - s) / (next_pnt[0] - prev_pnt[0])

        u = weight * prev_pnt[1] + (1.0 - weight) * next_pnt[1]
        v = weight * prev_pnt[2] + (1.0 - weight) * next_pnt[2]
        p = weight * prev_pnt[3] + (1.0 - weight) * next_pnt[3]

        return u, v, p

class XodrRoad:
    def __init__(self, road_xml):
        #road index
        self.id = xml_get_attrib(road_xml, 'id')
        self.length = xml_get_attrib(road_xml, 'length', float)
        self.junction = xml_get_attrib(road_xml, 'junction')

        #link
        self.predecessor = None
        predecessor_list = make_list_by_tag(road_xml, "./link/predecessor", XodrRoadLink)
        if len(predecessor_list) > 0 :
            self.predecessor = predecessor_list[0]

        self.successor = None
        successor_list = make_list_by_tag(road_xml, "./link/successor", XodrRoadLink)
        if len(successor_list) > 0 :
            self.successor = successor_list[0]

        #geometry
        geometry_list = make_list_by_tag(road_xml, "./planView/geometry", XodrGeometry)
        self.geometry_list = sorted(geometry_list, key=get_s)

        for geometry_item in self.geometry_list:
            if geometry_item.geo_type == "paramPoly3":
                geometry_item.gen_paramPoly3_points()

        #lane offset
        lane_offset_list = make_list_by_tag(road_xml, "./lanes/laneOffset", XodrPolynomial)
        self.lane_offset_list = sorted(lane_offset_list, key=get_s)

        #lane section
        lane_section_list = make_list_by_tag(road_xml, "./lanes/laneSection", XodrLaneSection)
        self.lane_section_list = sorted(lane_section_list, key=get_s)
        self.lane_section_list = set_length(self.lane_section_list, self.length)

        #elevation
        elevation_list = make_list_by_tag(road_xml, "./elevationProfile/elevation", XodrPolynomial)
        self.elevation_list = sorted(elevation_list, key=get_s)

        #super elevation
        super_elevation_list = make_list_by_tag(road_xml, "./lateralProfile/superelevation", XodrPolynomial)
        self.super_elevation_list = sorted(super_elevation_list, key=get_s)

        #signals
        self.signal_list = make_list_by_tag(road_xml, "./signals/signal", XodrSignal)

        #signal ref
        self.signal_ref_list = make_list_by_tag(road_xml, "./signals/signalReference", XodrSignalRef)

        #type
        self.type_list = make_list_by_tag(road_xml, "./type", XodrType)

        #object
        self.object_list = make_list_by_tag(road_xml, "./objects/object", XodrObject)

class XodrLaneLink :
    def __init__(self, lane_link_xml) :
        self.from_link = xml_get_attrib(lane_link_xml, 'from', int)
        self.to_link = xml_get_attrib(lane_link_xml, 'to', int)

class XodrConnection:
    def __init__(self, connection_xml) :
        self.id = xml_get_attrib(connection_xml, 'id')
        self.incoming_road = xml_get_attrib(connection_xml, 'incomingRoad')
        self.connecting_road = xml_get_attrib(connection_xml, 'connectingRoad')
        self.contact_point = xml_get_attrib(connection_xml, 'contactPoint')

        self.lane_link_list = make_list_by_tag(connection_xml, "./laneLink", XodrLaneLink)

class XodrJunction:
    def __init__(self, junction_xml) :
        self.id = xml_get_attrib(junction_xml, 'id')
        self.connection_list = make_list_by_tag(junction_xml, "./connection", XodrConnection)

class XodrControl :
    def __init__(self, control_xml) :
        self.signal_id = xml_get_attrib(control_xml, 'signalId')
        self.type = xml_get_attrib(control_xml, 'type')

class XodrController:
    def __init__(self, controller_xml) :
        self.id = xml_get_attrib(controller_xml, 'id')
        self.name = xml_get_attrib(controller_xml, 'name')
        self.control_list = make_list_by_tag(controller_xml, "./control", XodrControl)
