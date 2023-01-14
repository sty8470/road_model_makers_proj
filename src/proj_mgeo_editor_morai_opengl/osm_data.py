import lxml.etree as etree

class OsmDataBase :
    def __init__(self):
        self.id = ''
        self.visible = 'true'
        self.version = '1'


class OsmNodeData(OsmDataBase) :
    def __init__(self):
        super().__init__()
        self.lat = ''
        self.lon = ''
        self.ele = ''
        self.mgeo_id = ''

    def setNodeData(self, id, lat, lon, ele) :
        self.id = id
        self.lat = lat
        self.lon = lon
        self.ele = ele

    def createXmlElement(self, root) :
        sub_element = etree.SubElement(root, "node")
        sub_element.set("id", str(self.id))
        sub_element.set("lat", str(self.lat))
        sub_element.set("lon", str(self.lon))
        sub_element.set("version", self.version)
        sub_element.set("visible", self.visible)
        
        # mgeo id
        mgeo_id = etree.SubElement(sub_element, "tag")
        mgeo_id.set("k", "mgeo_id")
        mgeo_id.set("v", self.mgeo_id)

        # ele
        ele_ele = etree.SubElement(sub_element, "tag")
        ele_ele.set("k", "ele")
        ele_ele.set("v", str(self.ele))



class OsmWayData(OsmDataBase) :
    def __init__(self):
        super().__init__()
        self.type = ''
        self.subtype = ''
        self.node_list = list()

    def addNodeId(self, node_id) :
        self.node_list.append(node_id)

    def createXmlElement(self, root) :
        sub_element = etree.SubElement(root, "way")
        sub_element.set("id", str(self.id))
        sub_element.set("version", "1")
        sub_element.set("visible", "true")

        for k in self.node_list :
            nd_element = etree.SubElement(sub_element, "nd")
            nd_element.set("ref", str(k))

        type_element = etree.SubElement(sub_element, "tag")
        type_element.set("k", "type")
        type_element.set("v", self.type)

        sub_type_element = etree.SubElement(sub_element, "tag")
        sub_type_element.set("k", "subtype")
        sub_type_element.set("v", self.subtype)


class OsmLaneletData(OsmDataBase) :
    def __init__(self):
        super().__init__()
        self.type = 'lanelet'
        self.subtype = 'road'
        self.one_way = 'yes'
        self.left = ''
        self.right = ''
        self.turn_dir = None
    
    def createXmlElement(self, root) :
        sub_element = etree.SubElement(root, "relation")
        sub_element.set("id", str(self.id))
        sub_element.set("visible", "true")
        sub_element.set("version", "1")

        # member (left)
        left_lane = etree.SubElement(sub_element, "member")
        left_lane.set("type", "way")
        left_lane.set("ref", str(self.left))
        left_lane.set("role", "left")
        
        # member (right)
        right_lane = etree.SubElement(sub_element, "member")
        right_lane.set("type", "way")
        right_lane.set("ref", str(self.right))
        right_lane.set("role", "right")

        # oneway.(일방 통행)
        waytype = etree.SubElement(sub_element, "tag")
        waytype.set("k", "one_way")
        waytype.set("v", self.one_way)
        # road
        subtype = etree.SubElement(sub_element, "tag")
        subtype.set("k", "subtype")
        subtype.set("v", self.subtype)
        # lanelet
        tag_type = etree.SubElement(sub_element, "tag")
        tag_type.set("k", "type")
        tag_type.set("v", self.type)

