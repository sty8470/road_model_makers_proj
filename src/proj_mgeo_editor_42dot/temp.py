        # find all the connecting lanes within each junction
        for _notused, junction in junction_set.junctions.items():
            connecting_lanes = list()
            for node in junction.get_jc_nodes():
                survey_from_links = node.get_from_links()
                for survey_links in survey_from_links:
                    last_link = self.get_foremost_lane_in_the_same_road(survey_links)
                    survey_jc = last_link.get_from_node().junctions
                    if len(survey_jc) != 0:
                        for jc_candidate in survey_jc:
                            if jc_candidate == junction:
                                connecting_lanes.append(last_link)

            repeat_list = list()
            iterator = 1

            # determine properties of each connecting road
            for connection in connecting_lanes:
                # find out the road id of the preceding lane
                # account for floating links with no from_links
                if len(connection.get_from_links()) < 1:
                    if connection.lane_ch_link_left is not None:
                        incoming = connection.lane_ch_link_left.get_from_links()[0]
                    elif connection.lane_ch_link_right is not None:
                        incoming = connection.lane_ch_link_right.get_from_links()[0]
                    else:
                        raise BaseException('[ERROR] Connecting road lane does not have preceding element')
                else:
                    incoming = connection.get_from_links()[0]

                # create or call connecting_road
                if connection.road_id not in repeat_list:
                    # create new connecting road objects
                    junction.connecting_road[connection.road_id] = ConnectingRoad()
                    repeat_list.append(connection.road_id)
                    
                    # assign properties to the connecting road object
                    connector = junction.connecting_road[connection.road_id]
                    if iterator < 10:
                        iter_str = '0{}'.format(iterator)
                    else:
                        iter_str = '{}'.format(iterator)
                    connector.idx = '{}'.format(junction.idx[2:]) + iter_str
                    connector.connecting = connection.road_id
                    connector.incoming = incoming.road_id
                    iterator += 1
                elif connection.road_id in repeat_list:
                    # call existing connecting road object
                    connector = junction.connecting_road[connection.road_id]

                # assign to/from lanes to connecting_road
                connection_road = odr_data.roads[connection.road_id]
                incoming_road = odr_data.roads[incoming.road_id]

                # type check
                if isinstance(connection.ego_lane, str):
                    connection.ego_lane = int(connection.ego_lane)
                if isinstance(incoming.ego_lane, str):
                    incoming.ego_lane = int(incoming.ego_lane)

                # check left/right lane assignments for connection roads
                if connection in connection_road.lane_sections[0].lanes_L:
                    index_list = []
                    total_lanes = len(connection_road.lane_sections[0].lanes_L)
                    for i in range(total_lanes):
                        index_list.append(i+1)
                    index_list.reverse()
                    adj_lane_id = index_list[connection.ego_lane-1]
                    connector.to_lanes.append(adj_lane_id)

                elif connection in connection_road.lane_sections[0].lanes_R:
                    diff = len(connection_road.lane_sections[0].lanes_L)
                    adj_lane_id = connection.ego_lane - diff
                    connector.to_lanes.append((-1)*adj_lane_id)

                if incoming in incoming_road.lane_sections[-1].lanes_L:
                    index_list = []
                    total_lanes = len(incoming_road.lane_sections[-1].lanes_L)
                    for i in range(total_lanes):
                        index_list.append(i+1)
                    index_list.reverse()
                    adj_lane_id = index_list[incoming.ego_lane-1]
                    connector.from_lanes.append(adj_lane_id)
                    
                elif incoming in incoming_road.lane_sections[-1].lanes_R:
                    diff = len(incoming_road.lane_sections[-1].lanes_L)
                    adj_lane_id = incoming.ego_lane - diff
                    connector.from_lanes.append((-1)*adj_lane_id)
    
        odr_data.set_junction_set(junction_set)