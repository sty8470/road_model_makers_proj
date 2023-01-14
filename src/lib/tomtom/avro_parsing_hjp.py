import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))
sys.path.append(os.path.normpath(os.path.join(current_path, '../../')))

import avro.schema
from avro.datafile import DataFileReader, DataFileWriter
from avro.io import DatumReader, DatumWriter

import json
import uuid
import base64
import time

from lib.tomtom.tomtom_converter import *

class tt_avro_data_parse(object):

    def __init__(self):
        self.package_final = list()
        self.boundary_pt1 = [0, 0]
        self.boundary_pt2 = [0, 0]


    def convert_to_hex(self, str_input):
        # account for negative int uint values
        int_input = int(str_input)

        if int_input < 0:
            hex_output = format(int_input + 2**64, 'x')
        else:
            hex_output = format(int_input, 'x')
        
        return hex_output


    def set_boundary(self, b1, b2, b3, b4):
        '''
        b1, b2 - lat/lon pair #1
        b3, b4 - lat/lon pair #2
        '''
        self.boundary_pt1 = [b1, b2]
        self.boundary_pt2 = [b3, b4]


    def extract_region(self, coord_to_check):
        within_lat = False
        within_lon = False
        lat_min = self.boundary_pt1[0]
        lat_max = self.boundary_pt2[0]
        lon_min = self.boundary_pt1[1]
        lon_max = self.boundary_pt2[1]
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


    def parse_lane_group(self, entity_data, lane_group_data):
        in_region = False
        # attributes
        for attribute in lane_group_data['attributes']:

            if attribute['ddctType'] == -1299729752:
                # attribute - detailed geometry
                detailed_geo = list()
                detailed_geo_bin = attribute['nsoAttributes'][1]['value'].encode('utf-8')
                decoded = base64.b64decode(detailed_geo_bin)
                detailed_geo_str = decoded.decode('utf-8')

                # convert linestring to float
                coord_str, coord_list = lat_lng_point(detailed_geo_str)
                # coord_list = coord_str.split(', ')
                coord_converted = (0, 0, 0)
                for coord in coord_list:
                    x = float(coord[0])
                    y = float(coord[1])
                    z = float(coord[2])
                    coord_converted = (x, y, z)
                    detailed_geo.append(coord_converted)

                in_region = self.extract_region(coord_converted)

        package = {
            'entity':lane_group_data['entity'],
            'attributes':lane_group_data['attributes'],
            'associations':lane_group_data['associations']
        }

        return package, in_region


    def parse_lane_center_line(self, entity_data, lane_centerline_data):
        in_region = False
        # attributes
        for attribute in lane_centerline_data['attributes']:
            prv_lane_id = None
            nxt_lane_id = None

            if attribute['ddctType'] == 244390646:
                # attribute - detailed geometry
                detailed_geo = list()
                detailed_geo_bin = attribute['nsoAttributes'][1]['value'].encode('utf-8')
                decoded = base64.b64decode(detailed_geo_bin)
                detailed_geo_str = decoded.decode('utf-8')

                # convert linestring to float
                coord_str = detailed_geo_str[12:-1]
                coord_list = coord_str.split(', ')
                for coord in coord_list:
                    xyz = coord.split(' ')
                    x = float(xyz[0])
                    y = float(xyz[1])
                    z = float(xyz[2])
                    coord_converted = (x, y, z)
                    detailed_geo.append(coord_converted)

                in_region = self.extract_region(coord_converted)

            elif attribute['ddctType'] == -1165827340:
                # attribute - lane type
                lane_type = attribute['value']

            elif attribute['ddctType'] == 11320660:
                # attribute - length
                length = attribute['value']

            elif attribute['ddctType'] == -572916081:
                # attribute - opposing traffic
                opp_traffic = attribute['value']

            elif attribute['ddctType'] == 871265832:
                # attribute - source quality
                src_quality = attribute['value']

            elif attribute['ddctType'] == 728941090:
                # attribute - width
                width = attribute['value']

        # geometry

        # associations
        for association in lane_centerline_data['associations']:
            assoc_uuid_msb = self.convert_to_hex(association['otherFeature']['UUID']['mostSigBits'])
            assoc_uuid_lsb = self.convert_to_hex(association['otherFeature']['UUID']['leastSigBits'])
            assoc_uuid = uuid.UUID(assoc_uuid_msb + assoc_uuid_lsb)
            
            if association['entity']['ddctType'] == 370245627:
                # association - lane connection
                if association['associationType'] == 'TARGET':
                    nxt_lane_id = assoc_uuid.hex
                elif association['associationType'] == 'SOURCE':
                    prv_lane_id = assoc_uuid.hex

            elif association['entity']['ddctType'] == 1518724947:
                # association - left lane border
                left_lane_id = assoc_uuid.hex

            elif association['entity']['ddctType'] == -344801492:
                # association = right lane border
                right_lane_id = assoc_uuid.hex

            elif association['entity']['ddctType'] == -1934776132:
                # association - lane group
                lane_grp_id = assoc_uuid.hex

        # package everything into simplfied json
        pack_entity = {
            'id':entity_data
        }

        pack_attrib = {
            'detail_geo':detailed_geo,
            'lane_type':lane_type,
            'width':width,
            'length':length,
            'opposing':opp_traffic,
            'src_qual':src_quality
        }

        pack_assoc = {
            'prv_lane':prv_lane_id,
            'nxt_lane':nxt_lane_id,
            'left':left_lane_id,
            'right':right_lane_id,
            'grp':lane_grp_id
        }

        package = {
            'entity':pack_entity,
            'attributes':pack_attrib,
            'associations':pack_assoc
        }

        return package, in_region


    def parse_lane_border(self, entity_data, lane_border_data):
        # attributes
        in_region = False
        left_lane_id = None
        right_lane_id = None

        for attribute in lane_border_data['attributes']:
            width = None

            if attribute['ddctType'] == -32884444:
                # attribute - lane border component
                for nonspatialobj in attribute['nsoAttributes']:
                    if nonspatialobj['ddctType'] == 979833510:
                        # border geometry
                        detailed_geo = list()
                        detailed_geo_bin = nonspatialobj['nsoAttributes'][1]['value'].encode('utf-8')
                        decoded = base64.b64decode(detailed_geo_bin)
                        detailed_geo_str = decoded.decode('utf-8')

                        # convert linestring to float
                        coord_str = detailed_geo_str[12:-1]
                        coord_list = coord_str.split(', ')
                        for coord in coord_list:
                            xyz = coord.split(' ')
                            x = float(xyz[0])
                            y = float(xyz[1])
                            z = float(xyz[2])
                            coord_converted = (x, y, z)
                            detailed_geo.append(coord_converted)

                        in_region = self.extract_region(coord_converted)

                    elif nonspatialobj['ddctType'] == -1836887369:
                        # border color
                        border_color = nonspatialobj['value']
                    elif nonspatialobj['ddctType'] == -1885629980:
                        # border type
                        border_type = nonspatialobj['value']


            elif attribute['ddctType'] == 2126486925:
                # attribute - length
                length = attribute['value']

            elif attribute['ddctType'] == 2141407465:
                # attribute - width
                width = attribute['value']

            elif attribute['ddctType'] == -1617743042:
                # attribute - passing restrictions
                if attribute['value']['ddctType'] == 294780589:
                    pass_restrict = 'allowed'
                elif attribute['value']['ddctType'] == 1485072440:
                    pass_restrict = 'notallowed'
                elif attribute['value']['ddctType'] == 886768577:
                    pass_restrict = 'L2R'
                elif attribute['value']['ddctType'] == -2092663395:
                    pass_restrict = 'R2L'

        # geometry

        # associations
        for association in lane_border_data['associations']:
            assoc_uuid_msb = self.convert_to_hex(association['otherFeature']['UUID']['mostSigBits'])
            assoc_uuid_lsb = self.convert_to_hex(association['otherFeature']['UUID']['leastSigBits'])
            assoc_uuid = uuid.UUID(assoc_uuid_msb + assoc_uuid_lsb)
            
            if association['entity']['ddctType'] == 1518724947:
                # association - left lane border
                left_lane_id = assoc_uuid.hex
                
                if association['otherFeature']['ddctType'] == 346157642:
                    # association - lane center line
                    pass

            elif association['entity']['ddctType'] == -344801492:
                # association - right lane border
                right_lane_id = assoc_uuid.hex

                if association['otherFeature']['ddctType'] == 346157642:
                    # association - lane center line
                    pass


        # package
        pack_entity = {
            'id':entity_data
        }

        pack_attrib = {
            'detail_geo':detailed_geo_str,
            'color':border_color,
            'type':border_type,
            'width':width,
            'length':length,
            'pass_restrict':pass_restrict
        }

        pack_assoc = {
            'left':left_lane_id,
            'right':right_lane_id
        }

        package = {
            'entity':pack_entity,
            'attributes':pack_attrib,
            'associations':pack_assoc
        }

        return package, in_region


    def main(self):
        # working variables for main()
        # D:\지도\TomTom\HDMap_AVRO 'D:\\Work\\GIS & HD Maps\\TomTom\\unpacked\\HDMap_AVRO'
        file_loc = 'D:\\지도\\TomTom\\HDMap_AVRO'
        file_type = '\\LaneGroup'
        # file_type = '\\LaneCenterLine'
        file_count = 0
        data_count = 0

        # use avro package to parse map data file
        reader = DataFileReader(open(file_loc+file_type+'\\part-r-00000.avro', 'rb'), DatumReader())

        tic = time.perf_counter()
        print('Initializing at ' + str(tic))
        start_str = 'Initializing at {}'.format(tic)
        print(start_str)


        self.set_boundary(
            -122.45,
            37.70,
            -122.30,
            37.80
            )


        self.package_final = []

        # parse then package avro data back into json
        for i, data_point in enumerate(reader):
            
            # entities
            entity_ddct = data_point['entity']['ddctType']
            entity_uuid_msb = self.convert_to_hex(data_point['entity']['UUID']['mostSigBits'])
            entity_uuid_lsb = self.convert_to_hex(data_point['entity']['UUID']['leastSigBits'])
            entity_uuid = uuid.UUID(entity_uuid_msb + entity_uuid_lsb)
            entity_hex = entity_uuid.hex


            if  entity_ddct == 346157642:
                # entity is LaneCenterLine
                package, in_region = self.parse_lane_center_line(entity_hex, data_point)

            elif entity_ddct == -1268011471:
                # entity is LaneBorder
                package, in_region = self.parse_lane_border(entity_hex, data_point)

            elif entity_ddct == 852205264:
                # entity is LaneGroup
                package, in_region = self.parse_lane_group(entity_hex, data_point)

            if in_region is True:
                self.package_final.append(package)
                data_count += 1
                print(data_count)

            # divide data file into smaller json files
            if data_count > 999:
                # D:\지도\TomTom\HDMap_AVRO 'D:\\Work\\GIS & HD Maps\\TomTom\\unpacked\\HDMap_AVRO'
                with open('D:\\지도\\TomTom\\HDMap_AVRO\\LaneGroup' + '\\test_' + str(file_count) + '.json', 'w') as json_out:
                    json.dump(self.package_final, json_out, indent=4)
                    self.package_final.clear()
                    data_count = 0
                file_count += 1

        with open('D:\\지도\\TomTom\\HDMap_AVRO\\LaneGroup' + '\\test_' + '.json', 'w') as json_out:
            json.dump(self.package_final, json_out, indent=4)
        
        toc = time.perf_counter()
        result_str = 'Parsing Completed at {}'.format(toc-tic)
        print(result_str)



if __name__ == '__main__':
        tt_avro_data_parse().main()