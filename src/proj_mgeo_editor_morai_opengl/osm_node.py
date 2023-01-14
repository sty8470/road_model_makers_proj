
'''
osm format의 node 데이터를 담당하는 데이타 클래스.
후에 더욱 세분화 하도록...

'''
class OsmNodeData :
    def __init__(self) :
        self.id = ''
        self.lat = ''
        self.lon = ''
        self.ele = ''
        self.version = '1'
        self.visible = 'true'
        self.mgeo_id = ''

    def initNodeData(self, id, lat, lon, ele) :
        self.id = id
        self.lat = lat
        self.lon = lon
        self.ele = ele

    
    def initLinkPointData(self, link_id, lat, lon, ele) :
        self.id = link_id
        self.lat = lat
        self.lon = lon
        self.ele = ele
        

    def get_dic_node_data(self) :
        
        dic_node = dict()
        dic_node['id'] = str(self.id)
        dic_node['lat'] = str(self.lat)
        dic_node['lon'] = str(self.lon)
        dic_node['ele'] = str(self.ele)
        dic_node['version'] = self.version
        dic_node['visible'] = self.visible
        
        dic_node['mgeo_id'] = self.mgeo_id

        return dic_node
